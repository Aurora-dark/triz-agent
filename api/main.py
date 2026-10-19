# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    
    # ========== 健康检查（必须放在静态文件服务之前）==========
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "triz-agent"}
    print("✅ /health 已注册")
    
    # ========== 注册路由（统一添加 /api/triz 前缀）==========
    app.include_router(requirement_router, prefix="/api/triz")
    app.include_router(extract_router, prefix="/api/triz")
    app.include_router(result_router, prefix="/api/triz")
    app.include_router(history_router, prefix="/api/triz")
    print("✅ API 路由已注册")
    
    # ========== ✅ 静态文件服务（必须放在最后）==========
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_dir = os.path.join(base_dir, "static")
    
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"✅ 已创建静态文件目录: {static_dir}")
    
    # 检查 index.html 是否存在
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        print(f"✅ 找到前端文件: {index_file}")
    else:
        print(f"⚠️ 未找到前端文件: {index_file}")
        print(f"   请将 index.html 复制到 {static_dir}")
    
    # 挂载静态文件（放在所有路由之后）
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    print(f"✅ 静态文件服务已挂载: {static_dir}")
    
    return app

app = create_app()

# 打印路由
print("\n📋 已注册的路由:")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = ", ".join(route.methods) if hasattr(route, 'methods') else "ANY"
        print(f"   {methods:15} {route.path}")
print("=" * 60)