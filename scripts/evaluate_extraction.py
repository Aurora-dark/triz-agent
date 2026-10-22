#!/usr/bin/env python
"""
评测矛盾提取准确率。

直接调用 api.services.llm_client（不走 HTTP，不写历史记录），
与 data/eval/requirements.json 中的人工标注比对。

运行：
    python scripts/evaluate_extraction.py
    python scripts/evaluate_extraction.py --limit 10
    python scripts/evaluate_extraction.py --ids M01,E01,S01
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.config import LLM_CONFIG  # noqa: E402
from api.services.llm_client import llm_client  # noqa: E402
from api.services.matrix_service import matrix_service  # noqa: E402

EVAL_PATH = ROOT / "data" / "eval" / "requirements.json"
OUTPUT_PATH = ROOT / "data" / "eval" / "last_run.json"


def canonical(name: str) -> str:
    pid = matrix_service.get_param_id(name)
    return matrix_service.get_param_name(pid) if pid else (name or "").strip()


def strip_id(value: str) -> str:
    """'19. 运动物体的能耗' -> '运动物体的能耗'"""
    text = (value or "").strip()
    if ". " in text:
        text = text.split(". ", 1)[1]
    return text.strip()


async def run_case(case: dict) -> dict:
    result = await llm_client.extract_contradiction(case["text"])
    predicted_improve = strip_id(result.get("改善参数", ""))
    predicted_worsen = strip_id(result.get("恶化参数", ""))
    expected_improve = canonical(case["improve"])
    expected_worsen = canonical(case["worsen"])
    accept_improve = {expected_improve} | {
        canonical(item) for item in case.get("accept_improve", [])
    }
    accept_worsen = {expected_worsen} | {
        canonical(item) for item in case.get("accept_worsen", [])
    }
    return {
        "id": case["id"],
        "sector": case["sector"],
        "text": case["text"],
        "expected": {"improve": expected_improve, "worsen": expected_worsen},
        "accepted": {
            "improve": sorted(accept_improve),
            "worsen": sorted(accept_worsen),
        },
        "predicted": {"improve": predicted_improve, "worsen": predicted_worsen},
        "raw": {"improve": result.get("改善参数"), "worsen": result.get("恶化参数")},
        "improve_ok": predicted_improve in accept_improve,
        "worsen_ok": predicted_worsen in accept_worsen,
        "need_more_info": bool(result.get("是否需要补充信息")),
    }


async def main_async(cases: list) -> list:
    results = []
    for index, case in enumerate(cases, 1):
        item = await run_case(case)
        results.append(item)
        mark = "OK " if item["improve_ok"] and item["worsen_ok"] else "ERR"
        print(
            f"[{index:02d}/{len(cases)}] {mark} {case['id']} "
            f"{item['predicted']['improve']} / {item['predicted']['worsen']}"
        )
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--ids", type=str, default="")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH))
    parser.add_argument("--file", type=str, default=str(EVAL_PATH))
    args = parser.parse_args()

    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    cases = data["cases"]
    if args.ids:
        wanted = {item.strip() for item in args.ids.split(",") if item.strip()}
        cases = [case for case in cases if case["id"] in wanted]
    if args.limit:
        cases = cases[: args.limit]

    results = asyncio.run(main_async(cases))

    total = len(results)
    improve_acc = sum(item["improve_ok"] for item in results) / total
    worsen_acc = sum(item["worsen_ok"] for item in results) / total
    joint_acc = sum(item["improve_ok"] and item["worsen_ok"] for item in results) / total
    errors = [item for item in results if not (item["improve_ok"] and item["worsen_ok"])]

    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": LLM_CONFIG["model_name"],
        "total": total,
        "improve_accuracy": round(improve_acc, 4),
        "worsen_accuracy": round(worsen_acc, 4),
        "joint_accuracy": round(joint_acc, 4),
        "passed": joint_acc >= 0.8,
        "errors": errors,
        "results": results,
    }
    Path(args.output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print(f"样本 {total} 条  |  改善参数 {improve_acc:.1%}  |  恶化参数 {worsen_acc:.1%}")
    print(f"双参数同时正确（top-1）: {joint_acc:.1%}  ->  {'PASS' if report['passed'] else 'FAIL'} (目标 80%)")
    if errors:
        print("\n错例清单:")
        for item in errors:
            print(f"  {item['id']} {item['sector']} | {item['text']}")
            print(f"      期望: {item['expected']['improve']} / {item['expected']['worsen']}")
            print(f"      预测: {item['predicted']['improve']} / {item['predicted']['worsen']}")
    print(f"\n报告: {args.output}")


if __name__ == "__main__":
    main()
