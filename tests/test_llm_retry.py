import asyncio

from api.services.llm_client import llm_client


def test_two_stage_mapping_success(monkeypatch):
    async def fake_aspects(text, config):
        return {"改善方面": "提高速度", "恶化方面": "物料洒落和破损"}

    monkeypatch.setattr(llm_client, "extract_aspects", fake_aspects)
    result = asyncio.run(llm_client.extract_contradiction("提高速度但物料破损"))
    assert result["改善参数"] == "9. 速度"
    assert result["恶化参数"] == "23. 物质损失"
    assert result["是否需要补充信息"] is False


def test_two_stage_falls_back_and_retries(monkeypatch):
    calls = []

    async def fake_aspects(text, config):
        return {"改善方面": "外星参数A", "恶化方面": "外星参数B"}

    async def fake_request(messages, config):
        calls.append(messages)
        if len(calls) == 1:
            return {
                "原始需求": "测试",
                "改善参数": "外星参数A",
                "恶化参数": "外星参数B",
                "是否需要补充信息": False,
            }
        return {
            "原始需求": "测试",
            "改善参数": "能量消耗",
            "恶化参数": "重量",
            "是否需要补充信息": False,
        }

    monkeypatch.setattr(llm_client, "extract_aspects", fake_aspects)
    monkeypatch.setattr(llm_client, "_request", fake_request)

    result = asyncio.run(llm_client.extract_contradiction("测试"))
    assert len(calls) == 2
    assert result["改善参数"] == "19. 运动物体的能耗"
    assert result["恶化参数"] == "1. 运动物体的重量"


def test_two_stage_invalid_twice_marks_need_more_info(monkeypatch):
    calls = []

    async def fake_aspects(text, config):
        return {"改善方面": "还是不对", "恶化方面": "也不对"}

    async def fake_request(messages, config):
        calls.append(messages)
        return {
            "原始需求": "测试",
            "改善参数": "还是不对",
            "恶化参数": "也不对",
            "是否需要补充信息": False,
        }

    monkeypatch.setattr(llm_client, "extract_aspects", fake_aspects)
    monkeypatch.setattr(llm_client, "_request", fake_request)

    result = asyncio.run(llm_client.extract_contradiction("测试"))
    assert len(calls) == 2
    assert result["是否需要补充信息"] is True
    assert "无法匹配标准参数" in result["矛盾描述"]
