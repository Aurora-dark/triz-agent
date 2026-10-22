import json
import random
from pathlib import Path

from api.services.matrix_service import matrix_service

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = json.loads(
    (ROOT / "data" / "raw" / "contradiction_matrix_reference.json").read_text(
        encoding="utf-8"
    )
)
OFF_DIAGONAL = 39 * 38


def test_coverage_at_least_80_percent():
    coverage = len(matrix_service.matrix) / OFF_DIAGONAL
    assert len(matrix_service.matrix) == 1190
    assert coverage >= 0.8


def test_random_cells_match_reference():
    id_to_name = {int(pid): name for pid, name in matrix_service.parameters.items()}
    sample = random.sample(sorted(REFERENCE["cells"]), 20)
    for cell in sample:
        improve_id, worsen_id = (int(part) for part in cell.split(","))
        key = f"{id_to_name[improve_id]}_{id_to_name[worsen_id]}"
        assert matrix_service.matrix[key] == sorted(
            {int(v) for v in REFERENCE["cells"][cell]}
        )


def test_exact_recommendation_has_details():
    result = matrix_service.get_recommendation("能量消耗", "重量")
    assert result["匹配类型"] == "精确"
    assert result["是否有匹配"] is True
    assert result["推荐原理ID"]
    assert all(item["explain"] and item["case"] for item in result["推荐原理详情"])


def test_reverse_lookup():
    key = next(iter(matrix_service.matrix))
    improve, worsen = key.split("_")
    result = matrix_service.get_recommendation(worsen, improve)
    assert result["是否有匹配"] is True
    assert result["推荐原理ID"]


def test_fuzzy_fallback_for_missing_pair():
    names = list(matrix_service.parameters.values())
    missing = next(
        (a, b)
        for a in names
        for b in names
        if a != b
        and f"{a}_{b}" not in matrix_service.matrix
        and f"{b}_{a}" not in matrix_service.matrix
    )
    result = matrix_service.get_recommendation(*missing)
    assert result["匹配类型"] == "近似"
    assert result["推荐原理ID"]
    assert result["近似组合"]
    assert result["推荐原理详情"]


def test_unknown_parameter_is_miss():
    result = matrix_service.get_recommendation("外星参数", "重量")
    assert result["匹配类型"] == "未命中"
    assert result["是否有匹配"] is False
    assert result["推荐原理ID"] == []
