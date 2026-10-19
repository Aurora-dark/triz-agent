# api/services/llm_client.py
import json
import re
from openai import AsyncOpenAI

from ..config import LLM_CONFIG, TRIZ_SYSTEM_PROMPT
from .matrix_service import matrix_service


class LLMClient:
    def __init__(self):
        # 创建 OpenAI 兼容客户端，指向本地 Ollama
        self.client = AsyncOpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
            timeout=120.0,  # 本地模型可能较慢，给足时间
            max_retries=2,
        )

    # ==================== 输出解析 ====================

    @staticmethod
    def _parse_json(content: str) -> dict:
        content = (content or "").strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content).strip()
        start, end = content.find("{"), content.rfind("}")
        if start != -1 and end != -1 and end > start:
            content = content[start : end + 1]
        return json.loads(content)

    def _normalize(self, result: dict):
        """把模型输出的参数名归一到 39 个标准参数，返回 (结果, 错误列表)。"""
        errors = []
        result.setdefault("改善参数", "")
        result.setdefault("恶化参数", "")
        result.setdefault("矛盾描述", "")
        need_more = result.get("是否需要补充信息", False)
        if isinstance(need_more, str):
            need_more = need_more.strip().lower() in ("true", "1", "yes", "是")
        result["是否需要补充信息"] = bool(need_more)
        for field in ("改善参数", "恶化参数"):
            raw = str(result.get(field, "") or "").strip()
            pid = matrix_service.get_param_id(raw)
            if pid:
                result[field] = f"{pid}. {matrix_service.get_param_name(pid)}"
            else:
                errors.append(f"{field}「{raw}」不是标准参数")
        return result, errors

    # ==================== 调用模型 ====================

    async def _request(self, messages: list, model_config: dict) -> dict:
        response = await self.client.chat.completions.create(
            model=model_config.get("model_name", LLM_CONFIG["model_name"]),
            temperature=model_config.get("temperature", LLM_CONFIG["temperature"]),
            max_tokens=model_config.get("max_tokens", LLM_CONFIG["max_tokens"]),
            messages=messages,
        )
        return self._parse_json(response.choices[0].message.content)

    async def extract_contradiction(
        self, requirement_text: str, model_config: dict = None
    ) -> dict:
        config = model_config or {}
        messages = [
            {"role": "system", "content": TRIZ_SYSTEM_PROMPT},
            {"role": "user", "content": requirement_text},
        ]

        result = {}
        errors = []
        for attempt in range(2):
            try:
                result = await self._request(messages, config)
            except (json.JSONDecodeError, ValueError):
                result = {}
                errors = ["模型输出不是合法 JSON"]

            if not isinstance(result, dict):
                result = {}
                errors = ["模型输出不是 JSON 对象"]

            result.setdefault("原始需求", requirement_text)
            result, errors = self._normalize(result)

            if not errors or result.get("是否需要补充信息"):
                return result

            if attempt == 0:
                # 只重试一次，并把上一次的错误回传给模型
                messages = messages[:2] + [
                    {
                        "role": "assistant",
                        "content": json.dumps(result, ensure_ascii=False),
                    },
                    {
                        "role": "user",
                        "content": (
                            "你上一次的输出存在问题：" + "；".join(errors) + "。"
                            "请严格从系统给出的 39 个标准参数中选择，重新只输出 JSON。"
                        ),
                    },
                ]
                config = {**config, "temperature": 0.0}

        # 重试后仍不合法：保留原始输出并明确提示需要补充信息
        result["是否需要补充信息"] = True
        result["矛盾描述"] = "模型输出无法匹配标准参数：" + "；".join(errors)
        return result


llm_client = LLMClient()
