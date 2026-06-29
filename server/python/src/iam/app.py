"""
IAM 模块独立应用工厂

提供 IAM 模块的独立 FastAPI 应用，支持单独部署。
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
from framework.tenant.tenant_protocols import register_tenant_provider
from tenant.services.tenant_provider_impl import tenant_provider_impl

_logger = logger.bind(name=__name__)

APP_NAME = "IAM API"
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    _logger.info(
        f"\nIAM 应用开始启动... ({datetime.now(tz=ChinaTimeZone).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    # 初始化数据库引擎
    from framework.configs import get_settings

    settings = get_settings()
    sqlalchemy_config = settings.sqlalchemy
    setup_engine(
        database_url=sqlalchemy_config.url,
        echo=sqlalchemy_config.echo,
        pool_size=sqlalchemy_config.pool.size,
        max_overflow=sqlalchemy_config.pool.max_overflow,
    )

    # 注册 TenantProvider
    register_tenant_provider(tenant_provider_impl)

    # 自动执行 seed 初始化（异常不阻止应用启动）
    await _run_seed_initialization()

    yield

    _logger.info("IAM 应用关闭")


async def _run_seed_initialization():
    """执行数据初始化种子脚本"""
    from iam.migrations.seeds.organization_seed import (
        run as organization_seed_run,
    )
    from iam.migrations.seeds.user_seed import run as user_seed_run

    seed_modules = [
        ("默认组织", organization_seed_run),
        ("默认用户", user_seed_run),
    ]

    for name, seed_func in seed_modules:
        try:
            count = await seed_func(dry_run=False)
            _logger.info(f"Seed 初始化完成 [{name}]: {count} 条记录")
        except Exception:
            _logger.exception(f"Seed 初始化失败 [{name}]，跳过该模块")


def create_app() -> FastAPI:
    """创建 IAM 模块独立 FastAPI 应用实例"""
    app = FastAPI(
        title=APP_NAME,
        description="身份认证与访问管理 API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # 注册租户中间件
    from framework.configs import get_settings
    settings = get_settings()
    extra_skip_paths = settings.tenant.skip_tenant_setting_path
    app.add_middleware(TenantMiddleware, extra_skip_paths=extra_skip_paths if extra_skip_paths else None)

    # 注册管理后台路由
    from iam.controllers.admin.system_setting_controller import (
        router as admin_system_setting_router,
    )

    app.include_router(
        admin_system_setting_router,
        prefix="/iam/admin/v1/system-settings",
        tags=["Admin - SystemSetting"],
    )

    # 注册用户端路由
    from iam.controllers.console.system_setting_controller import (
        router as console_system_setting_router,
    )

    app.include_router(
        console_system_setting_router,
        prefix="/iam/console/v1/system-settings",
        tags=["Console - SystemSetting"],
    )

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
