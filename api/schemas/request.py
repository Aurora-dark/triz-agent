# api/schemas/request.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RequirementRequest(BaseModel):
    """需求接收接口请求体"""
    requirement_text: str = Field(..., min_length=1, max_length=2000, description="用户需求文本")
    user_id: Optional[str] = Field(None, description="用户标识")
    session_id: Optional[str] = Field(None, description="会话标识")
    timestamp: Optional[datetime] = Field(None, description="请求时间")
    metadata: Optional[dict] = Field(default_factory=dict, description="扩展元数据")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "requirement_text": "我想让手机屏幕更大但单手不好拿",
                "user_id": "user_12345",
                "session_id": "session_abc123"
            }
        }
    }

class ExtractRequest(BaseModel):
    """模型调用接口请求体"""
    task_id: str = Field(..., description="任务ID")
    model_config: Optional[dict] = Field(None, description="模型配置覆盖")
    prompt_template: str = Field("default", description="Prompt模板名称")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "task_20260607_143022_a1b2c3",
                "model_config": {
                    "model_name": "gpt-4",
                    "temperature": 0.1
                }
            }
        }
    }