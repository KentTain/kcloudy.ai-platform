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
from framework.common.time import ChinaTimeZone
from framework.database.core.engine import setup_engine
from framework.tenant.middleware import TenantMiddleware
from framework.tenant.protocols import register_tenant_provider
from iam.services.tenant_provider_impl import iam_tenant_provider
from demo.configs import settings

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
    register_tenant_provider(iam_tenant_provider)

    # 自动执行 seed 初始化（异常不阻止应用启动）
    await _run_seed_initialization()

    # 启动时的初始化逻辑
    yield
    # 关闭时的清理逻辑
    _logger.info("Demo 应用关闭")


async def _run_seed_initialization():
    """执行数据初始化种子脚本"""
    from iam.migrations.seeds.tenant_seed import run as tenant_seed_run
    from iam.migrations.seeds.iam_seed import run as iam_seed_run
    from iam.migrations.seeds.admin_seed import run as admin_seed_run

    seed_modules = [
        ("租户", tenant_seed_run),
        ("角色权限", iam_seed_run),
        ("管理员", admin_seed_run),
    ]

    for name, seed_func in seed_modules:
        try:
            count = await seed_func(dry_run=False)
            _logger.info(f"Seed 初始化完成 [{name}]: {count} 条记录")
        except Exception:
            _logger.exception(f"Seed 初始化失败 [{name}]，跳过该模块")


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

    # 注册路由 - Dataset
    from demo.controllers import dataset
    app.include_router(dataset.router, prefix="/api/v1/datasets", tags=["Dataset"])

    # 注册租户中间件（解析 X-Tenant-Id 并注入上下文）
    app.add_middleware(TenantMiddleware)

    # 注册路由 - IAM
    from iam.controllers import router as iam_router
    app.include_router(iam_router, prefix="/api/v1", tags=["IAM"])

    # 注册路由 - 管理后台
    from iam.controllers.admin.tenant_controller import router as admin_tenant_router
    app.include_router(admin_tenant_router, prefix="/admin/v1", tags=["Admin - Tenant"])
    from iam.controllers.admin.system_setting_controller import router as admin_system_setting_router
    app.include_router(admin_system_setting_router, prefix="/admin/v1/system-settings", tags=["Admin - SystemSetting"])

    # 注册路由 - 用户端租户
    from iam.controllers.console.tenant_controller import router as console_tenant_router
    app.include_router(console_tenant_router, prefix="/console/v1/tenants", tags=["Console - Tenant"])
    from iam.controllers.console.system_setting_controller import router as console_system_setting_router
    app.include_router(console_system_setting_router, prefix="/console/v1/system-settings", tags=["Console - SystemSetting"])

    # 健康检查端点
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "app": APP_NAME}

    return app


app = create_app()
