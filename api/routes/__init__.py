# api/routes/__init__.py
"""
路由模块初始化文件
导出所有路由供 main.py 使用
"""

from .requirement import router as requirement_router
from .extract import router as extract_router
from .result import router as result_router
from .history import router as history_router

# 导出所有路由
__all__ = [
    "requirement_router",
    "extract_router",
    "result_router",
    "history_router"
]