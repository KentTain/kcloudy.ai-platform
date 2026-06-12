"""
Demo 模块独立应用工厂

提供 Demo 模块的独立 FastAPI 应用，支持单独部署。
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from loguru import logger

from framework.common.time import ChinaTimeZone
from framework.database.core.engine import setup_engine
from framework.tenant.middleware import TenantMiddleware
from framework.tenant.protocols import register_tenant_provider

# 尝试导入 demo 配置
try:
    from demo.configs import settings
except ImportError:
    from framework.configs import get_settings

    settings = get_settings()

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
    sqlalchemy_config = settings.sqlalchemy
    setup_engine(
        database_url=sqlalchemy_config.url,
        echo=sqlalchemy_config.echo,
        pool_size=sqlalchemy_config.pool.size,
        max_overflow=sqlalchemy_config.pool.max_overflow,
    )

    # 注册 TenantProvider
    try:
        from iam.services.tenant_provider_impl import iam_tenant_provider

        register_tenant_provider(iam_tenant_provider)
    except ImportError:
        _logger.warning("IAM TenantProvider 不可用，跳过注册")

    # 启动任务调度器
    try:
        from demo.tasks.setup import setup_scheduler

        await setup_scheduler()
    except Exception:
        _logger.exception("任务调度器启动失败")

    # 启动消息监听器
    try:
        from demo.listeners.setup import setup_listeners

        await setup_listeners(settings)
    except Exception:
        _logger.exception("消息监听器启动失败")

    yield

    # 清理消息监听器
    try:
        from demo.listeners.setup import cleanup_listeners

        await cleanup_listeners()
    except Exception:
        _logger.exception("消息监听器清理失败")

    # 清理任务调度器
    try:
        from demo.tasks.setup import cleanup_scheduler

        await cleanup_scheduler()
    except Exception:
        _logger.exception("任务调度器清理失败")

    _logger.info("Demo 应用关闭")


def create_app() -> FastAPI:
    """创建 Demo 模块独立 FastAPI 应用实例"""
    app = FastAPI(
        title=APP_NAME,
        description="AI 助手平台演示 API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # 注册租户中间件
    app.add_middleware(TenantMiddleware)

    # 注册 Demo 路由
    from demo.controllers.dataset import router as dataset_router

    app.include_router(dataset_router, prefix="/api/v1/datasets", tags=["Dataset"])

    # 健康检查端点
    @app.get("/health", tags=["Health"])
    async def health():
        return {
            "status": "ok",
            "app": APP_NAME,
            "uptime": time.time() - start_time,
        }

    return app


# 模块级应用实例（用于 uvicorn 直接启动）
app = create_app()
