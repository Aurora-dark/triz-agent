# api/schemas/response.py
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class BaseResponse(BaseModel):
    """基础响应格式"""
    code: int
    message: str
    data: Optional[Any] = None

class RequirementResponseData(BaseModel):
    """需求接收响应数据"""
    task_id: str
    status: str
    created_at: str

class ContradictionResult(BaseModel):
    """矛盾提取结果"""
    原始需求: str
    改善参数: str
    恶化参数: str
    矛盾描述: str
    是否需要补充信息: bool

class ExtractResponseData(BaseModel):
    """模型调用响应数据"""
    task_id: str
    status: str
    result: Optional[ContradictionResult] = None
    processing_time_ms: Optional[int] = None
    model_used: Optional[str] = None

class ResultResponseData(BaseModel):
    """数据返回响应数据"""
    task_id: str
    status: str
    requirement_text: str
    result: Optional[ContradictionResult] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None