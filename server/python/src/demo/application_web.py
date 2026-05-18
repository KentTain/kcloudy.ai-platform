"""
FastAPI Web 应用工厂
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from loguru import logger

from demo.common.exception_handler import register_exception_handlers
from demo.core.common.time import ChinaTimeZone
from demo.models.core.engine import setup_orm

_logger = logger.bind(name=__name__)

APP_NAME = "Demo API"
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    _logger.info(
        f"\nDemo 应用开始启动... ({datetime.now(tz=ChinaTimeZone).strftime('%Y-%m-%d %H:%M:%S')})"
    )
    # 初始化数据库引擎
    setup_orm()
    # 启动时的初始化逻辑
    yield
    # 关闭时的清理逻辑
    _logger.info("Demo 应用关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title=APP_NAME,
        description="最小化 AI 助手平台",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # 注册异常处理器
    register_exception_handlers(app)

    # 注册路由
    from demo.controllers import dataset

    app.include_router(dataset.router, prefix="/api/v1/datasets", tags=["Dataset"])

    # 健康检查端点
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "app": APP_NAME}

    return app


app = create_app()
