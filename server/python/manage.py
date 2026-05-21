#!/usr/bin/env python
"""
Demo 管理脚本

# 启动Web服务器
python manage.py runserver

# 启动Web服务器（自定义主机和端口）
python manage.py runserver --host 0.0.0.0 --port 8080

# 启动定时任务调度器
python manage.py runtask

# 启动监听器服务
python manage.py runlistener

# 生成迁移脚本
python manage.py db makemigrations -m "add user tables"

# 应用迁移
python manage.py db migrate

# 显示当前数据库版本
python manage.py db current

# 显示迁移历史
python manage.py db history

# 回滚到上一个版本
python manage.py db downgrade

# 初始化数据
python manage.py seed

# 预览数据初始化
python manage.py seed --dry-run

# 初始化指定模块数据
python manage.py seed --module tenant
"""

import importlib
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


def import_all_models():
    """导入所有模型模块"""
    models_dir = src_path / "demo" / "models"
    for model_file in models_dir.glob("*.py"):
        if model_file.name != "__init__.py" and not model_file.name.startswith("_"):
            module_name = f"demo.models.{model_file.stem}"
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                print(f"[WARN] 无法导入模型模块 {module_name}: {e}")


def get_alembic_config(database_url: str | None = None):
    """获取 Alembic 配置"""
    from alembic import command
    from alembic.config import Config

    from demo.configs import settings

    config = Config()
    config.config_file_name = str(Path(__file__).parent / "alembic.ini")

    if database_url:
        connection_url = database_url
    else:
        connection_url = str(settings.sqlalchemy.url)
    config.set_main_option("sqlalchemy.url", connection_url)

    return config


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
def runserver(host, port, reload):
    """启动 Web 服务器"""
    import uvicorn

    from demo.configs import settings

    click.echo("正在启动 Web 服务器...")

    server_host = host or settings.server.host
    server_port = port or settings.server.port

    click.echo(f"  地址: http://{server_host}:{server_port}")
    click.echo(f"  文档: http://{server_host}:{server_port}/docs")

    uvicorn.run(
        "application_web:app",
        host=server_host,
        port=server_port,
        reload=reload,
    )


@cli.command()
def runtask():
    """启动定时任务调度器"""
    click.echo("正在启动定时任务调度器...")
    from application_task import main

    main()


@cli.command()
def runlistener():
    """启动监听器服务"""
    click.echo("正在启动监听器服务...")
    from application_listener import main

    main()


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
@click.pass_context
def makemigrations(ctx, message):
    """生成数据库迁移脚本"""
    from alembic import command

    click.echo("正在生成数据库迁移脚本...")

    # 确保所有模型被导入
    import_all_models()

    database_url = ctx.obj.get("database_url") if ctx.obj else None
    config = get_alembic_config(database_url)
    migration_message = message or "auto_migration"

    try:
        command.revision(config, autogenerate=True, message=migration_message)
        click.echo(f"✅ 成功生成迁移脚本: {migration_message}")
    except Exception as e:
        click.echo(f"❌ 生成迁移脚本失败: {e}")
        sys.exit(1)


@db.command()
@click.option("--revision", default="head", help="要迁移到的版本，默认为最新版本")
@click.option("--sql", is_flag=True, help="显示SQL语句而不执行迁移")
@click.option("--yes", "-y", is_flag=True, help="跳过确认直接执行迁移")
@click.pass_context
def migrate(ctx, revision, sql, yes):
    """应用数据库迁移"""
    from alembic import command

    database_url = ctx.obj.get("database_url") if ctx.obj else None
    config = get_alembic_config(database_url)

    try:
        current = command.current(config, verbose=False)
        click.echo(f"当前数据库版本: {current if current else '未初始化'}")

        if sql:
            command.upgrade(config, revision, sql=True)
            return

        click.echo(f"目标数据库版本: {revision}")

        if not yes and not click.confirm("确定要执行数据库迁移吗？"):
            click.echo("已取消迁移操作")
            return

        click.echo("正在应用数据库迁移...")
        command.upgrade(config, revision)

        new_version = command.current(config, verbose=False)
        click.echo("✅ 数据库迁移成功完成")
        click.echo(f"新的数据库版本: {new_version}")

    except Exception as e:
        click.echo(f"❌ 数据库迁移失败: {e}")
        sys.exit(1)


@db.command(name="current")
@click.pass_context
def show_current(ctx):
    """显示当前的数据库版本"""
    from alembic import command

    database_url = ctx.obj.get("database_url") if ctx.obj else None
    config = get_alembic_config(database_url)

    click.echo("当前数据库版本:")
    try:
        command.current(config, verbose=True)
    except Exception as e:
        click.echo(f"❌ 获取当前版本失败: {e}")
        sys.exit(1)


@db.command()
@click.pass_context
def history(ctx):
    """显示迁移历史"""
    from alembic import command

    database_url = ctx.obj.get("database_url") if ctx.obj else None
    config = get_alembic_config(database_url)

    click.echo("迁移历史:")
    try:
        command.history(config, verbose=True)
    except Exception as e:
        click.echo(f"❌ 获取迁移历史失败: {e}")
        sys.exit(1)


@db.command()
@click.option("--revision", default="-1", help="要回滚到的版本，默认回滚一个版本")
@click.option("--yes", "-y", is_flag=True, help="跳过确认直接执行回滚")
@click.pass_context
def downgrade(ctx, revision, yes):
    """回滚数据库迁移"""
    from alembic import command

    database_url = ctx.obj.get("database_url") if ctx.obj else None
    config = get_alembic_config(database_url)

    if not yes and not click.confirm(f"确定要回滚到版本 '{revision}' 吗？"):
        click.echo("已取消回滚操作")
        return

    click.echo(f"正在回滚到版本: {revision}...")
    try:
        command.downgrade(config, revision)
        click.echo("✅ 成功回滚")

        current = command.current(config, verbose=False)
        click.echo(f"当前数据库版本: {current if current else '未初始化'}")
    except Exception as e:
        click.echo(f"❌ 回滚失败: {e}")
        sys.exit(1)


# ────────────────────────────────────────────────────────────────────
# 数据初始化命令
# ────────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--dry-run", is_flag=True, help="仅预览，不写入数据库")
@click.option("--module", default=None, help="指定要初始化的模块名")
def seed(dry_run, module):
    """初始化默认数据"""
    import asyncio

    from demo.migrations.seeds import SEED_MODULES

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

        # 隐藏密码
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

    # 获取种子模块
    if not SEED_MODULES:
        click.echo("[WARN] 没有可初始化的模块")
        return

    available = ", ".join(SEED_MODULES.keys())
    click.echo(f"可用模块: {available}")
    click.echo()

    if dry_run:
        click.echo("[DRY-RUN] 预览模式，不会实际写入数据库")
        click.echo()

    # 确定要执行的模块
    if module:
        if module not in SEED_MODULES:
            click.echo(f"❌ 未找到模块: {module}")
            click.echo(f"可用模块: {available}")
            sys.exit(1)
        modules = {module: SEED_MODULES[module]}
    else:
        modules = SEED_MODULES

    # 运行种子脚本
    async def run_seeds():
        total = 0
        for name, func in modules.items():
            click.echo(f"  [{name}] 初始化中...")
            try:
                count = await func(dry_run=dry_run)
                if count > 0:
                    status = "[DRY-RUN] " if dry_run else ""
                    click.echo(f"  [{name}] {status}初始化 {count} 条记录")
                total += count
            except Exception as e:
                click.echo(f"  [{name}] ❌ {e}")
        return total

    total = asyncio.run(run_seeds())

    click.echo()
    if dry_run:
        click.echo(f"[DRY-RUN] 完成: 预览 {total} 条记录")
    else:
        click.echo(f"✅ 完成: 初始化 {total} 条记录")


if __name__ == "__main__":
    cli()
