from fastapi.testclient import TestClient

from api.main import app
from api.services import history_service as history_module
from api.services import llm_client as llm_module

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_matrix_recommend_exact():
    response = client.get(
        "/api/triz/matrix/recommend", params={"improve": "能量消耗", "worsen": "重量"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["匹配类型"] == "精确"
    assert data["推荐原理详情"]


def test_matrix_parameters_count():
    response = client.get("/api/triz/matrix/parameters")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 39


def test_extract_accepts_model_config_alias(monkeypatch):
    async def fake_extract(text, config=None):
        return {
            "原始需求": text,
            "改善参数": "19. 运动物体的能耗",
            "恶化参数": "1. 运动物体的重量",
            "矛盾描述": "如果提升运动物体的能耗，则会导致运动物体的重量变差",
            "是否需要补充信息": False,
        }

    monkeypatch.setattr(llm_module.llm_client, "extract_contradiction", fake_extract)
    monkeypatch.setattr(history_module.history_service, "save", lambda **kwargs: None)

    created = client.post(
        "/api/triz/requirement", json={"requirement_text": "电池续航短但机身要轻薄"}
    )
    assert created.status_code == 200
    task_id = created.json()["data"]["task_id"]

    response = client.post(
        "/api/triz/extract",
        json={"task_id": task_id, "model_config": {"temperature": 0.1}},
    )
    assert response.status_code == 200
    result = response.json()["data"]["result"]
    assert result["改善参数"] == "19. 运动物体的能耗"

    detail = client.get(f"/api/triz/result/{task_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["status"] == "completed"


def test_result_not_found():
    response = client.get("/api/triz/result/not-exist")
    assert response.status_code == 404


def test_static_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "TRIZ" in response.text
