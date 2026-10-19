#!/usr/bin/env python
"""
生成 data/principles_detail.json：给 /matrix/recommend 提供原理的解释与案例。

数据源：data/raw/triz_principles.json（40 条，字段 explain_cn / case_cn）
输出键：与 data/triz_matrix.json 的「发明原理」名称一致（如「分割」）。

运行：python scripts/build_principles_detail.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "data" / "triz_matrix.json"
RAW_PRINCIPLES_PATH = ROOT / "data" / "raw" / "triz_principles.json"
OUTPUT_PATH = ROOT / "data" / "principles_detail.json"


def main():
    matrix_data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    principle_names = matrix_data["发明原理"]
    raw = json.loads(RAW_PRINCIPLES_PATH.read_text(encoding="utf-8"))
    raw_by_id = {int(item["id"]): item for item in raw}

    details = {}
    missing = []
    for pid, short_name in principle_names.items():
        item = raw_by_id.get(int(pid))
        if not item:
            missing.append(pid)
            details[short_name] = {
                "id": int(pid),
                "name": short_name,
                "name_en": "",
                "explain": "",
                "case": "",
                "tags": "",
            }
            continue
        details[short_name] = {
            "id": int(pid),
            "name": item.get("name_cn", short_name),
            "name_en": item.get("name_en", ""),
            "explain": item.get("explain_cn", ""),
            "case": item.get("case_cn", ""),
            "tags": item.get("tag_cn", ""),
        }

    OUTPUT_PATH.write_text(
        json.dumps(details, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已生成 {OUTPUT_PATH}，共 {len(details)} 条原理详情")
    if missing:
        print(f"缺少原始数据的原理 ID: {missing}")


if __name__ == "__main__":
    main()
