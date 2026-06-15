"""
FastAPI Web 应用工厂

通过动态模块扫描与装配创建应用，替代硬编码 import。
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from loguru import logger

from demo.configs import settings
from framework.common.time import ChinaTimeZone
from framework.database.core.engine import setup_engine
from framework.middlewares.test_user_middleware import TestUserMiddleware
from framework.module import get_registry, load_modules
from framework.module.sync_service import ModuleDefinitionSyncService
from framework.tenant.middleware import TenantMiddleware
from framework.tenant.protocols import register_tenant_provider
from framework.utils.log_util import (
    write_error,
    write_info,
    write_success,
)
from framework.utils.startup_timer import StartupTimer
from iam.middlewares.iam_auth_middleware import IAMAuthMiddleware

_logger = logger.bind(name=__name__)

APP_NAME = "AI Platform API"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    timer: StartupTimer = app.state.startup_timer
    from datetime import datetime

    write_info(
        "AI Platform 应用开始启动... "
        f"({datetime.now(tz=ChinaTimeZone).strftime('%Y-%m-%d %H:%M:%S')})"
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

    with timer.phase("模块定义同步", order=3) as phase:
        # 同步模块定义（菜单、权限、角色）到数据库
        await _run_module_definition_sync(phase)

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

    write_info("AI Platform 应用关闭")


def _get_tenant_provider():
    """获取 TenantProvider 实现"""
    try:
        from tenant.services.tenant_provider_impl import tenant_provider_impl

        return tenant_provider_impl
    except ImportError as e:
        _logger.exception(f"模块定义同步失败: {e}")
        write_error("TenantProvider 不可用")
        return None


async def _run_module_definition_sync(phase) -> None:
    """
    执行模块定义同步

    将所有模块的元数据定义（菜单、权限、角色）同步到数据库。

    Args:
        phase: 启动计时器阶段对象，用于记录同步详情
    """
    sync_service = ModuleDefinitionSyncService()

    try:
        await sync_service.sync_all_modules()
        write_success("模块定义同步完成")
        phase.details["同步状态"] = "成功"
    except Exception as e:
        _logger.exception(f"模块定义同步失败: {e}")
        phase.details["同步状态"] = f"失败: {e}"
        # 同步失败不阻止应用启动，但记录错误
        write_error(f"模块定义同步失败，部分功能可能异常: {e}")


async def _run_seed_initialization():
    """执行各模块数据初始化种子脚本"""
    registry = get_registry()

    for module in registry.get_all_modules():
        seeds = module.get_seeds()
        for seed_name, seed_func in seeds.items():
            try:
                count = await seed_func(dry_run=False)
                write_success(
                    f"Seed 初始化完成 [{module.name}/{seed_name}]: {count} 条记录"
                )
            except Exception as e:
                _logger.exception(
                    f"Seed 初始化失败 [{module.name}/{seed_name}]，"
                    f"跳过该模块，错误消息: {e}"
                )
                write_error(f"Seed 初始化失败 [{module.name}/{seed_name}]，跳过该模块")


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
            write_info(f"Loaded modules from config: {ENABLED_MODULES}")
        except ImportError:
            _logger.exception("No modules config found, loading all modules")
            write_error("No modules config found, loading all modules")

    with timer.phase("模块加载与路由注册", order=3) as phase:
        # 加载模块
        src_path = Path(__file__).parent
        modules = load_modules(src_path, module_names)
        phase.details["模块数量"] = str(len(modules))

    write_info(f"已加载模块: {[m.name for m in modules]}")

    app = FastAPI(
        title=APP_NAME,
        description="AI 助手平台",
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

    # 注册中间件（注意：中间件执行顺序为栈结构，后注册的先执行）
    # 执行顺序：TenantMiddleware -> IAMAuthMiddleware -> TestUserMiddleware

    # 1. 注册租户中间件（解析租户并注入上下文）
    app.add_middleware(TenantMiddleware)

    # 2. 注册认证中间件（验证 JWT 并同步用户信息到 Context）
    app.add_middleware(IAMAuthMiddleware)

    # 3. 注册测试用户中间件（仅非生产环境）
    # 必须最后注册（最先执行），以便在认证后覆盖用户信息
    env = getattr(settings, "env", "development")
    if env != "production":
        app.add_middleware(TestUserMiddleware, enabled=True, env=env)
        write_info("已启用测试用户中间件（仅非生产环境）")

    # 动态注册各模块路由并打印日志
    _register_module_routes(app, modules)

    # 动态注册各模块中间件
    for module in modules:
        for middleware_class in module.get_middlewares():
            app.add_middleware(middleware_class)
            write_info(f"注册中间件: {middleware_class.__name__} [{module.name}]")

    # 健康检查端点
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "app": APP_NAME}

    return app


def _register_module_routes(app: FastAPI, modules: list) -> None:
    """
    注册模块路由并打印路由日志

    Args:
        app: FastAPI 应用实例
        modules: 模块列表
    """
    from collections import defaultdict

    # 按模块和类型分组收集路由信息
    # 结构: {module_name: {route_type: {prefix: {first_level: count}}}}
    module_routes = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    )

    # 注册路由并收集统计信息
    for module in modules:
        for router, prefix, tags in module.get_routers():
            app.include_router(router, prefix=prefix, tags=tags)

            # 确定路由类型
            if "/admin/" in prefix:
                route_type = "admin"
            elif "/console/" in prefix:
                route_type = "console"
            elif "/inner/" in prefix:
                route_type = "inner"
            else:
                route_type = "default"

            # 统计第一级路径的端点数量
            for route in router.routes:
                if hasattr(route, "path") and hasattr(route, "methods"):
                    # 提取第一级路径（如 /auth/login → /auth）
                    path = route.path
                    parts = path.strip("/").split("/")
                    first_level = "/" + parts[0] if parts else "/"

                    # 统计端点数量
                    for method in route.methods:
                        if method != "HEAD":
                            key = module.name, route_type, prefix, first_level
                            module_routes[key[0]][key[1]][key[2]][key[3]] += 1

    # 打印路由注册日志
    type_labels = {
        "admin": "管理后台",
        "console": "用户端",
        "inner": "内部接口",
        "default": "默认",
    }

    for module_name, types_dict in module_routes.items():
        for route_type, prefix_dict in types_dict.items():
            type_label = type_labels.get(route_type, route_type)

            for prefix, first_levels in prefix_dict.items():
                # 生成路由汇总
                route_stats = [
                    f"{path}（{count} 个端点）"
                    for path, count in sorted(first_levels.items())
                ]
                # 单行显示：模块、类型、路由
                write_info(
                    f"注册路由: {module_name} {type_label} ({prefix}) "
                    f"路由：{', '.join(route_stats)}"
                )


app = create_app()
