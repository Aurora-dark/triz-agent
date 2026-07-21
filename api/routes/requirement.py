# api/routes/requirement.py
from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..schemas.request import RequirementRequest
from ..schemas.response import BaseResponse, RequirementResponseData
from ..services.task_manager import task_manager

router = APIRouter(tags=["requirement"])  # ✅ 添加 tags

@router.post("/requirement", response_model=BaseResponse)
async def receive_requirement(req: RequirementRequest):
    try:
        # 使用统一的 task_manager
        task_id = task_manager.create_task(
            requirement_text=req.requirement_text,
            user_id=req.user_id,
            session_id=req.session_id,
            metadata=req.metadata
        )
        
        return BaseResponse(
            code=200,
            message="需求接收成功",
            data=RequirementResponseData(
                task_id=task_id,
                status="pending",
                created_at=datetime.now().isoformat()
            ).model_dump()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"需求接收失败: {str(e)}")