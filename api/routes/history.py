# api/routes/history.py
from fastapi import APIRouter, HTTPException, Query
from ..services.history_service import history_service
from ..services.matrix_service import matrix_service
from ..schemas.response import BaseResponse

router = APIRouter( tags=["history"])

@router.get("/history")
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    keyword: str = Query(None, description="搜索关键词")
):
    """获取历史记录列表"""
    if keyword:
        records = history_service.search(keyword)
    else:
        records = history_service.get_all(limit)
    
    return BaseResponse(
        code=200,
        message="success",
        data={
            "total": len(records),
            "records": records
        }
    ).model_dump()

@router.get("/history/{task_id}")
async def get_history_detail(task_id: str):
    """获取单条历史记录详情"""
    record = history_service.get_by_task_id(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return BaseResponse(
        code=200,
        message="success",
        data=record
    ).model_dump()

@router.delete("/history/{task_id}")
async def delete_history(task_id: str):
    """删除历史记录"""
    record = history_service.get_by_task_id(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    history_service.delete(task_id)
    return BaseResponse(
        code=200,
        message="删除成功",
        data=None
    ).model_dump()

@router.get("/matrix/recommend")
async def get_matrix_recommendation(
    improve: str = Query(..., description="改善参数"),
    worsen: str = Query(..., description="恶化参数")
):
    """获取矛盾矩阵推荐"""
    try:
        result = matrix_service.get_recommendation(improve, worsen)
        return BaseResponse(
            code=200,
            message="success",
            data=result
        ).model_dump()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matrix/parameters")
async def get_triz_parameters():
    """获取所有TRIZ参数列表"""
    params = matrix_service.get_all_parameters()
    return BaseResponse(
        code=200,
        message="success",
        data=params
    ).model_dump()