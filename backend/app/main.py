# FastAPI 入口
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .database import Base, engine
from .core.config import settings
# 导入模型以确保它们被注册到 Base
from . import models
from .routers import auth, business

# 初始化数据库表（必须在导入模型之后）
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI 运动教练 API - 基于 MediaPipe 的瑜伽动作分析系统",
    version="1.0.0"
)

# CORS 配置 (允许前端访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态目录，以便前端可以通过 URL 访问上传和处理后的视频
# 例如: http://localhost:8000/static/outputs/xxx.mp4
static_path = settings.BASE_DIR
app.mount(settings.STATIC_URL, StaticFiles(directory=str(static_path)), name="static")

# 注册路由
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(business.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    """根路径"""
    return {
        "message": "欢迎使用 AIMovement API",
        "version": "1.0.0",
        "docs": "/docs"
    }

