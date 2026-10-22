#!/usr/bin/env python
"""
用权威 39x39 矩阵全量替换 data/triz_matrix.json。

- 数据源：data/raw/contradiction_matrix_reference.json（1190 个非空格）
- 旧数据备份：data/legacy/triz_matrix_365.json（用于 A/B 对比）
- 覆盖率：1190 / 1482（非对角格）= 80.3%

运行：
    python scripts/rebuild_matrix.py            # 备份并重建
    python scripts/rebuild_matrix.py --check    # 只校验当前矩阵
"""

import argparse
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "data" / "triz_matrix.json"
REFERENCE_PATH = ROOT / "data" / "raw" / "contradiction_matrix_reference.json"
LEGACY_PATH = ROOT / "data" / "legacy" / "triz_matrix_365.json"
AB_REPORT_PATH = ROOT / "data" / "legacy" / "matrix_ab_summary.json"

OFF_DIAGONAL = 39 * 38


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_matrix(parameters: dict, reference: dict) -> dict:
    id_to_name = {int(pid): name for pid, name in parameters.items()}
    matrix = {}
    for key, values in reference["cells"].items():
        improve_id, worsen_id = (int(part) for part in key.split(","))
        if improve_id == worsen_id:
            continue
        improve_name = id_to_name.get(improve_id)
        worsen_name = id_to_name.get(worsen_id)
        if not improve_name or not worsen_name:
            raise SystemExit(f"参数映射缺失: {key}")
        matrix[f"{improve_name}_{worsen_name}"] = sorted({int(v) for v in values})
    return dict(sorted(matrix.items(), key=lambda item: item[0]))


def validate(matrix: dict, parameters: dict, reference: dict) -> None:
    names = set(parameters.values())
    assert len(matrix) == len(reference["cells"]), (len(matrix), len(reference["cells"]))
    for key, values in matrix.items():
        assert len(key.split("_")) == 2, key
        assert set(key.split("_")) <= names, key
        assert values and min(values) >= 1 and max(values) <= 40, (key, values)

    # 随机抽 20 格与参考矩阵逐格比对
    id_to_name = {int(pid): name for pid, name in parameters.items()}
    sample = random.sample(sorted(reference["cells"]), 20)
    for cell in sample:
        improve_id, worsen_id = (int(part) for part in cell.split(","))
        key = f"{id_to_name[improve_id]}_{id_to_name[worsen_id]}"
        expected = sorted({int(v) for v in reference["cells"][cell]})
        assert matrix[key] == expected, (cell, key, matrix[key], expected)
    first_improve, first_worsen = (int(part) for part in sample[0].split(","))
    first_key = f"{id_to_name[first_improve]}_{id_to_name[first_worsen]}"
    print(f"随机校验 20 格通过，例如: {sample[0]} -> {first_key} = {matrix[first_key]}")


def ab_compare(legacy: dict, new: dict) -> dict:
    legacy_matrix = legacy["矩阵"]
    same = different = only_legacy = 0
    examples = []
    for key, old_values in legacy_matrix.items():
        if key not in new:
            only_legacy += 1
            continue
        if sorted(old_values) == sorted(new[key]):
            same += 1
        else:
            different += 1
            if len(examples) < 5:
                examples.append({"key": key, "legacy": old_values, "new": new[key]})
    summary = {
        "legacy_cells": len(legacy_matrix),
        "new_cells": len(new),
        "same": same,
        "different": different,
        "only_in_legacy": only_legacy,
        "different_examples": examples,
    }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    data = load_json(MATRIX_PATH)
    reference = load_json(REFERENCE_PATH)
    parameters, principles = data["参数列表"], data["发明原理"]

    if args.check:
        validate(data["矩阵"], parameters, reference)
        print(f"当前矩阵 {len(data['矩阵'])} 格，覆盖率 {len(data['矩阵'])/OFF_DIAGONAL:.1%}")
        return

    new_matrix = build_matrix(parameters, reference)
    validate(new_matrix, parameters, reference)

    LEGACY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LEGACY_PATH.exists():
        LEGACY_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"旧矩阵已备份: {LEGACY_PATH}")

    summary = ab_compare(load_json(LEGACY_PATH), new_matrix)
    AB_REPORT_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    data["矩阵"] = new_matrix
    MATRIX_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    counts = Counter(name for key in new_matrix for name in key.split("_"))
    print(f"新矩阵: {len(new_matrix)} 格，覆盖率 {len(new_matrix)/OFF_DIAGONAL:.1%}")
    print(f"参数作为改善/恶化出现次数: 最少 {min(counts.values())}，最多 {max(counts.values())}")
    print(
        "A/B: 与旧矩阵相同 {same}，不同 {different}，仅旧矩阵有 {only_in_legacy}".format(
            **summary
        )
    )
    print(f"报告: {AB_REPORT_PATH}")


if __name__ == "__main__":
    main()
