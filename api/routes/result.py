# api/routes/result.py
from fastapi import APIRouter, HTTPException, Query, Response
from ..schemas.response import BaseResponse, ResultResponseData
from ..services.task_manager import task_manager

router = APIRouter(tags=["requirement"])  # ✅ 添加 tags

@router.get("/result/{task_id}")
async def get_result(
    task_id: str,
    format: str = Query("json", pattern="^(json|text)$")
):
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = task_manager.get_task(task_id)
    
    if format == "text" and task.get("result"):
        r = task["result"]
        text_output = f"""TRIZ技术矛盾提取结果
================================
原始需求：{r.get('原始需求', '')}
改善参数：{r.get('改善参数', '')}
恶化参数：{r.get('恶化参数', '')}
矛盾描述：{r.get('矛盾描述', '')}
是否需要补充信息：{r.get('是否需要补充信息', False)}
================================
状态：{task.get('status')}
耗时：{task.get('processing_time_ms', 'N/A')}ms
"""
        return Response(content=text_output, media_type="text/plain; charset=utf-8")
    
    return BaseResponse(
        code=200,
        message="success",
        data=ResultResponseData(
            task_id=task["task_id"],
            status=task["status"],
            requirement_text=task["requirement_text"],
            result=task.get("result"),
            created_at=task.get("created_at"),
            completed_at=task.get("completed_at"),
            processing_time_ms=task.get("processing_time_ms"),
            error=task.get("error")
        ).model_dump()
    ).model_dump()