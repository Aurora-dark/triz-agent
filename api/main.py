# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# ========== 导入路由 ==========
from api.routes import (
    requirement_router,
    extract_router,
    result_router,
    history_router
)

def create_app() -> FastAPI:
    app = FastAPI(
        title="TRIZ智能体API",
        description="TRIZ技术矛盾提取后端服务",
        version="2.0.0"
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ========== 注册路由（统一添加 /api/triz 前缀）==========
    app.include_router(requirement_router, prefix="/api/triz")
    app.include_router(extract_router, prefix="/api/triz")
    app.include_router(result_router, prefix="/api/triz")
    app.include_router(history_router, prefix="/api/triz")
    
    # ========== 健康检查 ==========
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "triz-agent"}
    
    return app

app = create_app()

# 打印路由
print("\n📋 已注册的路由:")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = ", ".join(route.methods) if hasattr(route, 'methods') else "ANY"
        print(f"   {methods:15} {route.path}")
print("=" * 60)