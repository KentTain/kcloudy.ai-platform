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
from framework.database.core.engine_pool import init_default_engine
from framework.database.dependencies import get_task_session
from framework.database.migration_validator import StartupMigrationValidator
from framework.middlewares.test_user_middleware import TestUserMiddleware
from framework.module import get_registry, load_modules
from framework.module.sync_service import ModuleDefinitionSyncService
from framework.tenant.middleware import TenantMiddleware
from framework.tenant.sync_protocols import register_module_auto_assigner
from framework.tenant.tenant_protocols import (
    register_tenant_provider,
    register_tenant_role_creator,
)
from framework.utils.log_util import (
    write_error,
    write_info,
    write_success,
    write_warning,
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
        # 初始化 DatabaseEnginePool（用于多租户引擎池管理）
        init_default_engine(
            database_url=sqlalchemy_config.url,
            echo=sqlalchemy_config.echo,
            pool_size=sqlalchemy_config.pool.size,
            max_overflow=sqlalchemy_config.pool.max_overflow,
        )
        phase.details["数据库引擎"] = "已初始化"

        # 初始化 Redis 客户端
        try:
            from framework.cache.redis_util import RedisUtil

            await RedisUtil.init(settings.redis)
            phase.details["Redis"] = "已初始化"
        except Exception as e:
            _logger.exception(f"Redis 客户端初始化失败: {e}")
            phase.details["Redis"] = "初始化失败"

        # 注册 TenantProvider
        provider = _get_tenant_provider()
        if provider:
            register_tenant_provider(provider)
            phase.details["TenantProvider"] = "已注册"
        else:
            phase.details["TenantProvider"] = "不可用"

        # 注册 ModuleAutoAssigner（由 IAM 模块实现）
        try:
            from iam.services.module_auto_assigner import IamModuleAutoAssigner

            register_module_auto_assigner(IamModuleAutoAssigner())
            phase.details["ModuleAutoAssigner"] = "已注册"
        except ImportError as e:
            _logger.exception(f"ModuleAutoAssigner 注册失败: {e}")
            phase.details["ModuleAutoAssigner"] = "不可用"

        # 注册 TenantRoleCreator（由 IAM 模块实现）
        try:
            from iam.services.tenant_role_creator import IAMTenantRoleCreator

            register_tenant_role_creator(IAMTenantRoleCreator())
            phase.details["TenantRoleCreator"] = "已注册"
        except ImportError as e:
            _logger.exception(f"TenantRoleCreator 注册失败: {e}")
            phase.details["TenantRoleCreator"] = "不可用"

        # 注册 PluginInstallationProvider（由 Tenant 模块实现）
        try:
            from framework.tenant.plugin_protocols import (
                register_plugin_installation_provider,
            )
            from tenant.services.plugin_provider import (
                plugin_installation_provider_impl,
            )

            register_plugin_installation_provider(plugin_installation_provider_impl)
            phase.details["PluginInstallationProvider"] = "已注册"
        except ImportError as e:
            _logger.exception(f"PluginInstallationProvider 注册失败: {e}")
            phase.details["PluginInstallationProvider"] = "不可用"

        # 注册 ModuleDefinitionSyncProvider（由 Tenant 模块实现）
        try:
            from framework.tenant.sync_protocols import (
                register_module_definition_sync_provider,
            )
            from tenant.services.module_sync_provider import (
                module_definition_sync_provider_impl,
            )

            register_module_definition_sync_provider(
                module_definition_sync_provider_impl
            )
            phase.details["ModuleDefinitionSyncProvider"] = "已注册"
        except ImportError as e:
            _logger.exception(f"ModuleDefinitionSyncProvider 注册失败: {e}")
            phase.details["ModuleDefinitionSyncProvider"] = "不可用"

    with timer.phase("数据库迁移验证", order=2.5) as phase:
        # 验证并自动运行数据库迁移
        src_path = Path(__file__).parent
        auto_migrate = settings.sqlalchemy.auto_migrate
        migration_validator = StartupMigrationValidator(src_path, auto_migrate=auto_migrate)

        if auto_migrate:
            write_info("自动迁移模式已启用 (auto_migrate=true)")

        async with get_task_session() as session:
            migration_result = await migration_validator.validate_and_migrate(session)

        if migration_result["all_migrated"]:
            if migration_result.get("auto_migrated"):
                phase.details["迁移状态"] = f"✓ 自动迁移完成: {migration_result['auto_migrated']}"
            else:
                phase.details["迁移状态"] = "✓ 全部完成"
            write_success("数据库迁移验证通过")
        else:
            failed = migration_result.get("need_migration", [])
            phase.details["迁移状态"] = f"⚠ 需要迁移: {failed}"
            write_error(
                f"数据库迁移缺失: {failed}。"
                f"请先运行: uv run python manage.py db migrate --all --yes"
            )
            # 迁移缺失时跳过后续初始化步骤
            app.state.migration_needed = True

    # 仅在迁移完成时执行后续初始化
    migration_needed = getattr(app.state, "migration_needed", False)

    if not migration_needed:
        with timer.phase("模块定义同步", order=3) as phase:
            # 同步模块定义（菜单、权限、角色）到数据库
            await _run_module_definition_sync(phase)

        with timer.phase("数据初始化", order=4):
            # 自动执行各模块 seed 初始化（异常不阻止应用启动）
            await _run_seed_initialization()

        with timer.phase("插件目录扫描", order=4.5) as phase:
            # 启动时扫描插件目录并注册到数据库
            await _run_plugin_scan_at_startup(phase)

        with timer.phase("监听器初始化", order=4.6) as phase:
            # 启动各模块的事件监听器
            await _setup_listeners(phase)

        with timer.phase("数据完整性验证", order=5) as phase:
            # 验证关键数据是否存在
            src_path = Path(__file__).parent
            migration_validator = StartupMigrationValidator(src_path)
            async with get_task_session() as session:
                verification = await migration_validator.verify_data_integrity(session)

            if verification["all_passed"]:
                phase.details["验证状态"] = "✓ 全部通过"
                write_success("数据完整性验证通过")
            else:
                failed = [k for k, v in verification.items()
                         if k != "all_passed" and not v.get("passed")]
                phase.details["验证状态"] = f"⚠ 部分缺失: {failed}"
                write_warning(f"数据完整性验证未通过，部分功能可能异常: {failed}")
    else:
        write_warning("检测到迁移缺失，跳过模块定义同步和数据初始化")
        write_info("请运行迁移后重启应用: uv run python manage.py db migrate --all --yes")

    registry = get_registry()
    modules = [module.name for module in registry.get_all_modules()]
    server_config = settings.server
    timer.print_summary(
        modules=modules,
        address=f"http://{server_config.host}:{server_config.port}",
        docs_path="/docs",
    )

    yield

    # 清理监听器
    await _cleanup_listeners()

    # 关闭 Redis 连接
    try:
        from framework.cache.redis_util import RedisUtil

        await RedisUtil.close()
    except Exception as e:
        _logger.exception(f"Redis 连接关闭失败: {e}")

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
        async with get_task_session() as session:
            await sync_service.sync_all_modules(session)
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


async def _run_plugin_scan_at_startup(phase) -> None:
    """
    启动时扫描插件目录并注册到数据库

    根据配置决定是否扫描以及扫描的目录路径。
    扫描失败不阻止应用启动，仅记录错误。

    Args:
        phase: 启动计时器阶段对象，用于记录扫描详情
    """
    plugin_config = settings.plugin

    # 检查是否启用启动时扫描
    if not plugin_config.scan_on_startup:
        phase.details["扫描状态"] = "已禁用"
        return

    # 检查是否配置了扫描目录
    scan_directory = plugin_config.scan_directory
    if not scan_directory:
        phase.details["扫描状态"] = "未配置目录"
        write_warning("插件启动扫描已启用但未配置目录 (plugin.scan_directory)")
        return

    try:
        from tenant.services.plugin_startup_scan_service import scan_plugins_at_startup

        async with get_task_session() as session:
            result = await scan_plugins_at_startup(session, scan_directory)
            await session.commit()

        # 记录扫描结果
        if result.total_count == 0:
            phase.details["扫描状态"] = "目录为空"
            write_info(f"插件目录为空，未找到 .zip 文件: {scan_directory}")
        else:
            phase.details["扫描状态"] = (
                f"共 {result.total_count} 个, "
                f"成功 {result.success_count} 个, "
                f"跳过 {result.skipped_count} 个, "
                f"失败 {result.failed_count} 个"
            )
            if result.success_count > 0 or result.skipped_count > 0:
                write_success(
                    f"插件目录扫描完成: 共 {result.total_count} 个, "
                    f"成功 {result.success_count} 个, "
                    f"跳过 {result.skipped_count} 个, "
                    f"失败 {result.failed_count} 个"
                )
            if result.failed_count > 0:
                write_warning(f"部分插件扫描失败: {result.errors}")

    except Exception as e:
        _logger.exception(f"插件目录扫描失败: {e}")
        phase.details["扫描状态"] = f"失败: {e}"
        write_error(f"插件目录扫描失败，部分插件可能不可用: {e}")


async def _setup_listeners(phase) -> None:
    """
    启动各模块的事件监听器

    遍历所有模块，调用其 get_listener_setup() 方法获取监听器设置函数并执行。

    Args:
        phase: 启动计时器阶段对象，用于记录初始化详情
    """
    registry = get_registry()
    listener_count = 0

    for module in registry.get_all_modules():
        listener_setup = module.get_listener_setup()
        if listener_setup:
            try:
                setup_func, _ = listener_setup
                await setup_func(settings)
                listener_count += 1
                _logger.info(f"模块 {module.name} 监听器已启动")
            except Exception as e:
                _logger.exception(f"模块 {module.name} 监听器启动失败: {e}")
                write_error(f"模块 {module.name} 监听器启动失败")

    if listener_count > 0:
        phase.details["监听器数量"] = listener_count
        write_success(f"事件监听器启动完成: {listener_count} 个")
    else:
        phase.details["监听器数量"] = 0


async def _cleanup_listeners() -> None:
    """清理所有模块的事件监听器"""
    registry = get_registry()

    for module in registry.get_all_modules():
        listener_setup = module.get_listener_setup()
        if listener_setup:
            try:
                _, cleanup_func = listener_setup
                await cleanup_func()
                _logger.info(f"模块 {module.name} 监听器已清理")
            except Exception as e:
                _logger.exception(f"模块 {module.name} 监听器清理失败: {e}")


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
    # 执行顺序：AdminAuthMiddleware → TestUserMiddleware → IAMAuthMiddleware → TenantMiddleware
    # - AdminAuthMiddleware: 处理 /tenant/admin/* 路径的管理员认证
    # - IAMAuthMiddleware: 处理 /iam/*、/ai/*、/tenant/console/* 路径的用户认证
    # - TenantMiddleware: 解析租户信息并注入上下文

    # 1. 注册租户中间件（解析租户并注入上下文）
    # 从配置读取扩展的跳过路径，追加到内置 SKIP_PATHS 之后
    extra_skip_paths = settings.tenant.skip_tenant_setting_path
    app.add_middleware(TenantMiddleware, extra_skip_paths=extra_skip_paths if extra_skip_paths else None)

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
