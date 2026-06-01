"""
FastAPI Web 应用工厂

通过动态模块扫描与装配创建应用，替代硬编码 import。
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from loguru import logger

from framework.common.time import ChinaTimeZone
from framework.database.core.engine import setup_engine
from framework.module import load_modules, get_registry, ModuleDescriptor
from framework.tenant.middleware import TenantMiddleware
from framework.tenant.protocols import register_tenant_provider
from framework.utils.startup_timer import StartupTimer
from demo.configs import settings

_logger = logger.bind(name=__name__)

APP_NAME = "Demo API"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    timer: StartupTimer = app.state.startup_timer
    _logger.info(
        f"\nDemo 应用开始启动... ({datetime.now(tz=ChinaTimeZone).strftime('%Y-%m-%d %H:%M:%S')})"
    )

    with timer.phase("基础组件初始化", order=2) as phase:
        # 初始化数据库引擎
        sqlalchemy_config = settings.sqlalchemy
        setup_engine(
            database_url=sqlalchemy_config.url,
            echo=sqlalchemy_config.echo,
            pool_size=sqlalchemy_config.pool.size,
            max_overflow=sqlalchemy_config.pool.max_overflow,
        )
        phase.details["数据库引擎"] = "已初始化"

        # 注册 TenantProvider
        provider = _get_tenant_provider()
        if provider:
            register_tenant_provider(provider)
            phase.details["TenantProvider"] = "已注册"
        else:
            phase.details["TenantProvider"] = "不可用"

    with timer.phase("数据初始化", order=4):
        # 自动执行各模块 seed 初始化（异常不阻止应用启动）
        await _run_seed_initialization()

    registry = get_registry()
    modules = [module.name for module in registry.get_all_modules()]
    server_config = settings.server
    timer.print_summary(
        modules=modules,
        address=f"http://{server_config.host}:{server_config.port}",
        docs_path="/docs",
    )

    yield

    _logger.info("Demo 应用关闭")


def _get_tenant_provider():
    """获取 TenantProvider 实现"""
    try:
        from tenant.services.tenant_provider_impl import tenant_provider_impl
        return tenant_provider_impl
    except ImportError:
        _logger.warning("TenantProvider 不可用")
        return None


async def _run_seed_initialization():
    """执行各模块数据初始化种子脚本"""
    registry = get_registry()

    for module in registry.get_all_modules():
        seeds = module.get_seeds()
        for seed_name, seed_func in seeds.items():
            try:
                count = await seed_func(dry_run=False)
                _logger.info(f"Seed 初始化完成 [{module.name}/{seed_name}]: {count} 条记录")
            except Exception:
                _logger.exception(f"Seed 初始化失败 [{module.name}/{seed_name}]，跳过该模块")


def create_app(module_names: list[str] | None = None) -> FastAPI:
    """
    创建 FastAPI 应用实例

    Args:
        module_names: 要加载的模块名列表，None 表示加载全部

    Returns:
        FastAPI 应用实例
    """
    timer = StartupTimer(app_name=APP_NAME)

    with timer.phase("配置加载", order=1):
        pass

    # 如果未指定模块，尝试从配置文件读取
    if module_names is None:
        try:
            from config.modules import ENABLED_MODULES
            module_names = ENABLED_MODULES
            _logger.info(f"Loaded modules from config: {ENABLED_MODULES}")
        except ImportError:
            _logger.info("No modules config found, loading all modules")

    with timer.phase("模块加载与路由注册", order=3) as phase:
        # 加载模块
        src_path = Path(__file__).parent
        modules = load_modules(src_path, module_names)
        phase.details["模块数量"] = str(len(modules))

    _logger.info(f"已加载模块: {[m.name for m in modules]}")

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
    app.state.startup_timer = timer

    # 注册异常处理器
    from demo.common.exception_handler import register_exception_handlers
    register_exception_handlers(app)

    # 注册租户中间件（解析 X-Tenant-Id 并注入上下文）
    app.add_middleware(TenantMiddleware)

    # 动态注册各模块路由
    for module in modules:
        for router, prefix, tags in module.get_routers():
            app.include_router(router, prefix=prefix, tags=tags)
            _logger.info(f"注册路由: {prefix} [{module.name}]")

    # 动态注册各模块中间件
    for module in modules:
        for middleware_class in module.get_middlewares():
            app.add_middleware(middleware_class)
            _logger.info(f"注册中间件: {middleware_class.__name__} [{module.name}]")

    # 健康检查端点
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "app": APP_NAME}

    return app


app = create_app()
