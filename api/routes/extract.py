# api/routes/extract.py
from fastapi import APIRouter, HTTPException
import time
from ..schemas.request import ExtractRequest
from ..schemas.response import BaseResponse, ExtractResponseData
from ..services.task_manager import task_manager
from ..services.llm_client import llm_client
from ..services.history_service import history_service  # 🆕 导入
from ..config import LLM_CONFIG

router = APIRouter( tags=["extract"])

@router.post("/extract", response_model=BaseResponse)
async def extract_contradiction(req: ExtractRequest):
    if not task_manager.task_exists(req.task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = task_manager.get_task(req.task_id)
    requirement_text = task["requirement_text"]
    
    model_config = req.model_config or {
        "model_name": LLM_CONFIG["model_name"],
        "temperature": LLM_CONFIG["temperature"],
        "max_tokens": LLM_CONFIG["max_tokens"]
    }
    
    start_time = time.time()
    try:
        result = await llm_client.extract_contradiction(requirement_text, model_config)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        task_manager.set_result(
            task_id=req.task_id,
            result=result,
            processing_time_ms=processing_time_ms,
            model_used=model_config.get("model_name")
        )
        
        # 🆕 保存到历史记录
        history_service.save(
            task_id=req.task_id,
            result=result,
            processing_time_ms=processing_time_ms,
            model_used=model_config.get("model_name")
        )
        
        return BaseResponse(
            code=200,
            message="矛盾提取成功",
            data=ExtractResponseData(
                task_id=req.task_id,
                status="completed",
                result=result,
                processing_time_ms=processing_time_ms,
                model_used=model_config.get("model_name")
            ).model_dump()
        )
    except Exception as e:
        task_manager.set_error(req.task_id, str(e))
        raise HTTPException(status_code=500, detail=f"模型调用失败: {str(e)}")