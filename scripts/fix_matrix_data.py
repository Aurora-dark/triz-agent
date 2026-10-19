#!/usr/bin/env python
"""
修正 data/triz_matrix.json：
1. 把 24 条使用非标准参数名（应力、适应性）的键改成标准名并合并。
2. 对从未作为「改善参数」出现的参数，用权威 39x39 矩阵补齐组合。

参考数据：data/raw/contradiction_matrix_reference.json
（Altshuller 39x39 矩阵，来自 MIT 许可的 kamil-szczepanik/TRIZ-Agents 转录）

运行：python scripts/fix_matrix_data.py [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = ROOT / "data" / "triz_matrix.json"
REFERENCE_PATH = ROOT / "data" / "raw" / "contradiction_matrix_reference.json"

# 非标准名 -> 标准名
KEY_ALIASES = {
    "应力": "应力/压力",
    "适应性": "适应性/通用性",
    "能量消耗": "运动物体的能耗",
}


def normalize_matrix(matrix: dict):
    normalized = {}
    renames = []
    for key, values in matrix.items():
        parts = key.split("_")
        if len(parts) != 2:
            renames.append((key, None))
            continue
        improve, worsen = parts
        new_improve = KEY_ALIASES.get(improve, improve)
        new_worsen = KEY_ALIASES.get(worsen, worsen)
        new_key = f"{new_improve}_{new_worsen}"
        if new_key != key:
            renames.append((key, new_key))
        merged = sorted({int(v) for v in values})
        if new_key in normalized:
            normalized[new_key] = sorted(set(normalized[new_key]) | set(merged))
        else:
            normalized[new_key] = merged
    return normalized, renames


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    parameters = data["参数列表"]
    matrix = data["矩阵"]

    normalized, renames = normalize_matrix(matrix)
    print(f"键规范化: {len(matrix)} -> {len(normalized)}，改名 {len(renames)} 条")
    for old, new in renames:
        print(f"  {old} -> {new}")

    reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    cells = reference["cells"]
    id_to_name = {int(pid): name for pid, name in parameters.items()}

    improve_counts = {name: 0 for name in parameters.values()}
    for key in normalized:
        improve_counts[key.split("_")[0]] += 1
    never_improve = [name for name, count in improve_counts.items() if count == 0]
    print(f"从未作为改善参数: {len(never_improve)} 个 -> {never_improve}")

    # 先校对：已有键与参考矩阵的重合度（仅统计双方都有且值不同的）
    agree = disagree = 0
    for key, values in normalized.items():
        improve, worsen = key.split("_")
        ids = [pid for pid, name in id_to_name.items() if name in (improve, worsen)]
        if len(ids) != 2:
            continue
        improve_id = next((pid for pid, name in id_to_name.items() if name == improve), None)
        worsen_id = next((pid for pid, name in id_to_name.items() if name == worsen), None)
        ref = cells.get(f"{improve_id},{worsen_id}")
        if not ref:
            continue
        if sorted(ref) == sorted(values):
            agree += 1
        else:
            disagree += 1
            print(f"  差异 {key}: 现有={values} 参考={ref}")
    print(f"与参考矩阵比对: 一致 {agree} 条，差异 {disagree} 条")

    added = 0
    for name in never_improve:
        improve_id = next(pid for pid, n in id_to_name.items() if n == name)
        for worsen_id, worsen_name in id_to_name.items():
            if worsen_id == improve_id:
                continue
            ref = cells.get(f"{improve_id},{worsen_id}")
            if not ref:
                continue
            key = f"{name}_{worsen_name}"
            if key in normalized:
                continue
            normalized[key] = sorted({int(v) for v in ref})
            added += 1
    print(f"补齐组合: +{added} 条，最终 {len(normalized)} 条")

    if args.dry_run:
        print("dry-run，不写文件")
        return

    data["矩阵"] = dict(sorted(normalized.items(), key=lambda item: item[0]))
    MATRIX_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已写入 {MATRIX_PATH}")


if __name__ == "__main__":
    sys.exit(main())
