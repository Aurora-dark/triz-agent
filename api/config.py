# api/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 存储目录
STORAGE_DIR = BASE_DIR / "storage"
TASKS_DIR = STORAGE_DIR / "tasks"
LOGS_DIR = STORAGE_DIR / "logs"
# 本地 Ollama 配置（已切换到 Qwen2.5:3B）
# 确保目录存在
TASKS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LLM_CONFIG = {
    "provider": "local_ollama",                # ← 改成 local_ollama
    "model_name": "qwen2.5:3b",                # ← 你刚下载的模型
    "temperature": 0.1,
    "max_tokens": 500,
    "api_key": "ollama",                       # ← 本地不需要真实Key
    "base_url": "http://localhost:11434/v1",   # ← Ollama API地址
}
# API配置
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", 8000)),
    "debug": os.getenv("API_DEBUG", "False").lower() == "true",
}

# api/config.py 中的 TRIZ_SYSTEM_PROMPT

TRIZ_SYSTEM_PROMPT = """你是一名TRIZ专家。从用户需求中提取技术矛盾。

# 场景映射示例（必须参考）
| 用户需求示例 | 改善参数 | 恶化参数 |
|-------------|---------|---------|
| "手机屏幕更大但单手不好拿" | 5. 运动物体的面积 | 33. 可操作性 |
| "屏幕更大但单手操作不便" | 5. 运动物体的面积 | 33. 可操作性 |
| "更大屏幕但不易单手操作" | 5. 运动物体的面积 | 33. 可操作性 |

# 输出规则
1. 改善参数和恶化参数必须使用TRIZ标准编号格式："编号. 参数名称"
2. 参考上述示例的风格进行映射
3. 只输出JSON，不要其他内容

# 输出格式（必须严格遵守，字段名不能改变）
{
  "原始需求": "用户输入的原文",
  "改善参数": "编号. 标准参数名称",
  "恶化参数": "编号. 标准参数名称",
  "矛盾描述": "如果提升[改善参数]，则会导致[恶化参数]变差",
  "是否需要补充信息": false
}

# 约束条件
- 不提供解决方案
- 如果需求缺少矛盾对，设置"是否需要补充信息"为true
- 只输出JSON，不输出其他内容
"""