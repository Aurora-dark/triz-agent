# api/services/llm_client.py
import json
from openai import AsyncOpenAI
from ..config import LLM_CONFIG, TRIZ_SYSTEM_PROMPT

class LLMClient:
    def __init__(self):
        # 创建 OpenAI 兼容客户端，指向本地 Ollama
        self.client = AsyncOpenAI(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"],
            timeout=120.0,  # 本地模型可能较慢，给足时间
            max_retries=2
        )
    
    async def extract_contradiction(self, requirement_text: str, model_config: dict = None) -> dict:
        config = model_config or {}
        model_name = config.get("model_name", LLM_CONFIG["model_name"])
        temperature = config.get("temperature", LLM_CONFIG["temperature"])
        max_tokens = config.get("max_tokens", LLM_CONFIG["max_tokens"])
        
        # 调用本地 Ollama 模型
        response = await self.client.chat.completions.create(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": TRIZ_SYSTEM_PROMPT},
                {"role": "user", "content": requirement_text}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # 去除 markdown 代码块标记
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # 解析 JSON
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            # 如果模型输出格式不正确，返回友好提示
            return {
                "原始需求": requirement_text,
                "改善参数": "解析失败",
                "恶化参数": "解析失败",
                "矛盾描述": f"模型返回格式错误，请重试。错误：{str(e)}",
                "是否需要补充信息": True
            }

llm_client = LLMClient()