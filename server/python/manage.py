#!/usr/bin/env python
"""
Demo 管理脚本

支持多模块架构的动态加载和数据库管理。

# 启动Web服务器（加载所有模块）
python manage.py runserver

# 启动Web服务器（按需加载模块）
python manage.py runserver --module iam,demo

# 启动定时任务调度器
python manage.py runtask --module demo

# 启动监听器服务
python manage.py runlistener --module demo

# 生成迁移脚本（按模块）
python manage.py db makemigrations --module iam -m "add oauth"

# 应用迁移（按模块）
python manage.py db migrate --module iam
python manage.py db migrate --all

# 显示当前数据库版本
python manage.py db current

# 显示迁移历史
python manage.py db history --module iam

# 回滚迁移
python manage.py db downgrade --module iam

# 重建数据库 Schema
python manage.py db rebuild --module iam
python manage.py db rebuild --all

# 初始化数据
python manage.py seed
python manage.py seed --module iam
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加 src 目录到路径
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import click

# 设置时区
os.environ["TZ"] = "Asia/Shanghai"


def load_all_modules():
    """加载所有模块"""
    from framework.module import load_modules, ModuleRegistry
    ModuleRegistry.reset()
    return load_modules(src_path)


def resolve_target_modules(module_arg: str | None, all_modules: bool = False):
    """解析目标模块列表"""
    from framework.module import get_registry

    if all_modules:
        registry = get_registry()
        if not registry.get_all_modules():
            load_all_modules()
        registry = get_registry()
        return registry.get_all_modules()

    if module_arg:
        names = module_arg.split(",")
        if not get_registry().get_all_modules():
            load_all_modules()
        registry = get_registry()
        modules = []
        for name in names:
            module = registry.get_module(name)
            if module is None:
                click.echo(f"❌ 未找到模块: {name}")
                sys.exit(1)
            modules.append(module)
        return modules

    # 默认加载所有
    if not get_registry().get_all_modules():
        load_all_modules()
    return get_registry().get_all_modules()


def get_module_alembic_config(module, database_url: str | None = None):
    """获取模块的 Alembic 配置"""
    from alembic.config import Config
    from demo.configs import settings

    module_dir = src_path / module.name / "migrations"
    config_file = module_dir / "alembic.ini"

    # 如果模块有独立的 alembic.ini，使用它
    # 否则使用全局配置并设置模块路径
    if config_file.exists():
        config = Config(str(config_file))
    else:
        # 使用全局 alembic.ini
        global_config_file = Path(__file__).parent / "alembic.ini"
        config = Config(str(global_config_file))

    # 设置模块特定的配置
    config.set_main_option(
        "script_location",
        str(module_dir)
    )
    config.set_main_option(
        "version_locations",
        str(module_dir / "versions")
    )

    if database_url:
        connection_url = database_url
    else:
        connection_url = str(settings.sqlalchemy.url)
    config.set_main_option("sqlalchemy.url", connection_url)

    return config


def get_database_url():
    """获取数据库连接 URL"""
    from demo.configs import settings
    return str(settings.sqlalchemy.url)


@click.group()
def cli():
    """Demo 管理命令行工具"""
    pass


# ────────────────────────────────────────────────────────────────────
# 服务器启动命令
# ────────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--host", help="监听的主机地址")
@click.option("--port", type=int, help="监听的端口")
@click.option("--reload", is_flag=True, help="启用热重载")
@click.option("--module", default=None, help="指定加载的模块（逗号分隔）")
def runserver(host, port, reload, module):
    """启动 Web 服务器"""
    import uvicorn

    from demo.configs import settings

    click.echo("正在启动 Web 服务器...")

    # 如果指定了模块，通过环境变量传递
    if module:
        os.environ["LOAD_MODULES"] = module
        click.echo(f"  加载模块: {module}")

    server_host = host or settings.server.host
    server_port = port or settings.server.port
    display_host = "127.0.0.1" if server_host == "0.0.0.0" else server_host

    click.echo(f"  地址: http://{display_host}:{server_port}")
    click.echo(f"  文档: http://{display_host}:{server_port}/docs")

    uvicorn.run(
        "application_web:app",
        host=server_host,
        port=server_port,
        reload=reload,
    )


@cli.command()
@click.option("--module", default=None, help="指定加载的模块（逗号分隔）")
def runtask(module):
    """启动定时任务调度器"""
    click.echo("正在启动定时任务调度器...")
    if module:
        os.environ["LOAD_MODULES"] = module
    from application_task import main
    main(module)


@cli.command()
@click.option("--module", default=None, help="指定加载的模块（逗号分隔）")
def runlistener(module):
    """启动监听器服务"""
    click.echo("正在启动监听器服务...")
    if module:
        os.environ["LOAD_MODULES"] = module
    from application_listener import main
    main(module)


# ────────────────────────────────────────────────────────────────────
# 数据库迁移命令
# ────────────────────────────────────────────────────────────────────


@cli.group()
@click.option(
    "--database-url",
    "-d",
    default=None,
    help="数据库连接URL，例如: postgresql+asyncpg://user:password@localhost:5432/dbname",
)
@click.pass_context
def db(ctx, database_url):
    """数据库管理命令"""
    ctx.ensure_object(dict)
    ctx.obj["database_url"] = database_url
    if database_url:
        click.echo(f"使用指定的数据库连接: {database_url[:50]}...")


@db.command()
@click.option("--message", "-m", default=None, help="迁移消息描述")
@click.option("--module", default=None, help="指定模块生成迁移")
@click.pass_context
def makemigrations(ctx, message, module):
    """生成数据库迁移脚本"""
    from alembic import command

    click.echo("正在生成数据库迁移脚本...")

    # 加载模块
    modules = resolve_target_modules(module)
    database_url = ctx.obj.get("database_url") if ctx.obj else None

    for m in modules:
        click.echo(f"  [{m.name}] 生成迁移...")
        config = get_module_alembic_config(m, database_url)
        migration_message = message or f"{m.name}_auto_migration"

        try:
            command.revision(config, autogenerate=True, message=migration_message)
            click.echo(f"  [{m.name}] ✅ 成功生成迁移脚本: {migration_message}")
        except Exception as e:
            click.echo(f"  [{m.name}] ❌ 生成迁移脚本失败: {e}")


@db.command()
@click.option("--module", default=None, help="指定模块应用迁移")
@click.option("--all", "all_modules", is_flag=True, help="应用所有模块迁移")
@click.option("--sql", is_flag=True, help="显示SQL语句而不执行迁移")
@click.option("--yes", "-y", is_flag=True, help="跳过确认直接执行迁移")
@click.pass_context
def migrate(ctx, module, all_modules, sql, yes):
    """应用数据库迁移"""
    from alembic import command

    modules = resolve_target_modules(module, all_modules)
    database_url = ctx.obj.get("database_url") if ctx.obj else None

    for m in modules:
        click.echo(f"  [{m.name}] 应用迁移...")
        config = get_module_alembic_config(m, database_url)

        try:
            if sql:
                command.upgrade(config, "head", sql=True)
                continue

            if not yes and not click.confirm(f"  [{m.name}] 确定要执行数据库迁移吗？"):
                click.echo(f"  [{m.name}] 已取消迁移操作")
                continue

            command.upgrade(config, "head")
            click.echo(f"  [{m.name}] ✅ 数据库迁移成功完成")

        except Exception as e:
            click.echo(f"  [{m.name}] ❌ 数据库迁移失败: {e}")


@db.command(name="current")
@click.option("--module", default=None, help="指定模块查看版本")
@click.pass_context
def show_current(ctx, module):
    """显示当前的数据库版本"""
    from alembic import command

    modules = resolve_target_modules(module)
    database_url = ctx.obj.get("database_url") if ctx.obj else None

    click.echo("当前数据库版本:")
    for m in modules:
        config = get_module_alembic_config(m, database_url)
        try:
            click.echo(f"  [{m.name}]")
            command.current(config, verbose=True)
        except Exception as e:
            click.echo(f"  [{m.name}] ❌ 获取当前版本失败: {e}")


@db.command()
@click.option("--module", default=None, help="指定模块查看历史")
@click.pass_context
def history(ctx, module):
    """显示迁移历史"""
    from alembic import command

    modules = resolve_target_modules(module)
    database_url = ctx.obj.get("database_url") if ctx.obj else None

    click.echo("迁移历史:")
    for m in modules:
        config = get_module_alembic_config(m, database_url)
        try:
            click.echo(f"  [{m.name}]")
            command.history(config, verbose=True)
        except Exception as e:
            click.echo(f"  [{m.name}] ❌ 获取迁移历史失败: {e}")


@db.command()
@click.option("--module", default=None, help="指定模块回滚迁移")
@click.option("--revision", default="-1", help="要回滚到的版本，默认回滚一个版本")
@click.option("--yes", "-y", is_flag=True, help="跳过确认直接执行回滚")
@click.pass_context
def downgrade(ctx, module, revision, yes):
    """回滚数据库迁移"""
    from alembic import command

    modules = resolve_target_modules(module)
    database_url = ctx.obj.get("database_url") if ctx.obj else None

    for m in modules:
        if not yes and not click.confirm(f"  [{m.name}] 确定要回滚到版本 '{revision}' 吗？"):
            click.echo(f"  [{m.name}] 已取消回滚操作")
            continue

        config = get_module_alembic_config(m, database_url)
        click.echo(f"  [{m.name}] 正在回滚到版本: {revision}...")
        try:
            command.downgrade(config, revision)
            click.echo(f"  [{m.name}] ✅ 成功回滚")
        except Exception as e:
            click.echo(f"  [{m.name}] ❌ 回滚失败: {e}")


@db.command()
@click.option("--module", default=None, help="指定模块重建 schema")
@click.option("--all", "all_modules", is_flag=True, help="重建所有模块 schema")
@click.option("--yes", "-y", is_flag=True, help="跳过确认直接执行")
@click.option("--dry-run", is_flag=True, help="仅预览操作，不实际执行")
@click.pass_context
def rebuild(ctx, module, all_modules, yes, dry_run):
    """重建数据库 Schema"""
    from sqlalchemy import text

    modules = resolve_target_modules(module, all_modules)

    click.echo("=" * 60)
    if dry_run:
        click.echo("[DRY-RUN] 预览模式，不会实际执行")
    click.echo("重建数据库 Schema")
    click.echo("=" * 60)
    click.echo()

    for m in modules:
        click.echo(f"  [{m.name}] 将执行:")
        click.echo(f"    1. DROP SCHEMA IF EXISTS {m.schema} CASCADE")
        click.echo(f"    2. CREATE SCHEMA {m.schema}")
        click.echo(f"    3. alembic upgrade head")
        click.echo(f"    4. run seeds")
        click.echo()

    if not dry_run:
        if not yes and not click.confirm("⚠️  此操作将删除所有数据！确定要继续吗？"):
            click.echo("已取消重建操作")
            return

    async def do_rebuild():
        from framework.database.core.engine import setup_engine, get_session

        db_url = get_database_url()
        if ctx.obj:
            override_url = ctx.obj.get("database_url")
            if override_url:
                db_url = override_url

        setup_engine(database_url=db_url)

        for m in modules:
            if dry_run:
                click.echo(f"  [{m.name}] [DRY-RUN] DROP + CREATE SCHEMA")
                continue

            async with get_session() as session:
                # DROP SCHEMA
                await session.execute(
                    text(f"DROP SCHEMA IF EXISTS {m.schema} CASCADE")
                )
                await session.commit()
                click.echo(f"  [{m.name}] ✅ 已删除 schema: {m.schema}")

                # CREATE SCHEMA
                await session.execute(
                    text(f"CREATE SCHEMA {m.schema}")
                )
                await session.commit()
                click.echo(f"  [{m.name}] ✅ 已创建 schema: {m.schema}")

        # 运行迁移
        from alembic import command

        for m in modules:
            config = get_module_alembic_config(m)
            if not dry_run:
                command.upgrade(config, "head")
                click.echo(f"  [{m.name}] ✅ 已应用迁移")

        # 运行 seed
        for m in modules:
            seeds = m.get_seeds()
            for seed_name, seed_func in seeds.items():
                if dry_run:
                    click.echo(f"  [{m.name}/{seed_name}] [DRY-RUN] 预览 seed")
                    continue

                try:
                    count = await seed_func(dry_run=False)
                    click.echo(f"  [{m.name}/{seed_name}] ✅ 初始化 {count} 条记录")
                except Exception as e:
                    click.echo(f"  [{m.name}/{seed_name}] ❌ {e}")

    if not dry_run:
        asyncio.run(do_rebuild())
    else:
        asyncio.run(do_rebuild())

    click.echo()
    if dry_run:
        click.echo("[DRY-RUN] 预览完成")
    else:
        click.echo("✅ 重建完成")


# ────────────────────────────────────────────────────────────────────
# 数据初始化命令
# ────────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--dry-run", is_flag=True, help="仅预览，不写入数据库")
@click.option("--module", default=None, help="指定要初始化的模块名")
def seed(dry_run, module):
    """初始化默认数据"""
    from framework.module import get_registry

    # 加载模块
    modules = resolve_target_modules(module)

    click.echo("=" * 60)
    click.echo("数据初始化")
    click.echo("=" * 60)
    click.echo()

    # 检查数据库连接
    try:
        from demo.configs import settings
        from framework.database.core.engine import setup_engine

        sqlalchemy_config = settings.sqlalchemy
        setup_engine(
            database_url=sqlalchemy_config.url,
            echo=sqlalchemy_config.echo,
            pool_size=sqlalchemy_config.pool.size,
            max_overflow=sqlalchemy_config.pool.max_overflow,
        )

        db_url = settings.sqlalchemy.url
        if "@" in db_url:
            parts = db_url.split("@")
            safe_url = parts[0].rsplit(":", 1)[0] + ":***@" + parts[1]
        else:
            safe_url = db_url
        click.echo(f"数据库: {safe_url}")

    except Exception as e:
        click.echo(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

    click.echo()

    if dry_run:
        click.echo("[DRY-RUN] 预览模式，不会实际写入数据库")
        click.echo()

    # 运行种子脚本
    async def run_seeds():
        total = 0
        for m in modules:
            seeds = m.get_seeds()
            if not seeds:
                click.echo(f"  [{m.name}] 无 seed 数据")
                continue

            for seed_name, seed_func in seeds.items():
                click.echo(f"  [{m.name}/{seed_name}] 初始化中...")
                try:
                    count = await seed_func(dry_run=dry_run)
                    if count > 0:
                        status = "[DRY-RUN] " if dry_run else ""
                        click.echo(f"  [{m.name}/{seed_name}] {status}初始化 {count} 条记录")
                    total += count
                except Exception as e:
                    click.echo(f"  [{m.name}/{seed_name}] ❌ {e}")
        return total

    total = asyncio.run(run_seeds())

    click.echo()
    if dry_run:
        click.echo(f"[DRY-RUN] 完成: 预览 {total} 条记录")
    else:
        click.echo(f"✅ 完成: 初始化 {total} 条记录")


if __name__ == "__main__":
    cli()