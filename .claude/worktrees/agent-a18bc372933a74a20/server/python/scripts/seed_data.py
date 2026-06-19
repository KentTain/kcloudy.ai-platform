"""
数据初始化脚本

初始化各业务模块的默认数据，支持幂等执行和 dry-run 预览。

用法：
    uv run python scripts/seed_data.py              # 初始化所有模块
    uv run python scripts/seed_data.py --dry-run    # 预览待初始化的数据
    uv run python scripts/seed_data.py --module tenant  # 初始化指定模块
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Callable, Coroutine

# Windows 控制台编码处理
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 添加 src 目录到路径（必须在其他导入之前）
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def check_database_connection() -> bool:
    """检查数据库连接

    Returns:
        是否连接成功
    """
    try:
        from demo.configs import settings
        from framework.database.core.engine import setup_engine, get_engine

        sqlalchemy_config = settings.sqlalchemy
        setup_engine(
            database_url=sqlalchemy_config.url,
            echo=sqlalchemy_config.echo,
            pool_size=sqlalchemy_config.pool.size,
            max_overflow=sqlalchemy_config.pool.max_overflow,
        )
        engine = get_engine()

        # 隐藏密码
        db_url = settings.sqlalchemy.url
        if "@" in db_url:
            parts = db_url.split("@")
            safe_url = parts[0].rsplit(":", 1)[0] + ":***@" + parts[1]
        else:
            safe_url = db_url

        print(f"[INFO] 数据库: {safe_url}")
        return True

    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False


def get_seed_modules() -> dict[str, Callable[[bool], Coroutine[None, None, int]]]:
    """获取所有种子模块

    Returns:
        模块名到种子函数的映射
    """
    try:
        from demo.seeds import SEED_MODULES

        return SEED_MODULES
    except ImportError as e:
        print(f"[WARN] 未找到种子模块定义: {e}")
        return {}


async def run_seed(module_name: str, seed_func: Callable, dry_run: bool) -> int:
    """运行单个模块的种子脚本

    Args:
        module_name: 模块名
        seed_func: 种子函数
        dry_run: 是否仅预览

    Returns:
        初始化的记录数
    """
    print(f"  [{module_name}] 初始化中...")
    try:
        count = await seed_func(dry_run=dry_run)
        if count > 0:
            status = "[DRY-RUN] " if dry_run else ""
            print(f"  [{module_name}] {status}初始化 {count} 条记录")
        return count
    except Exception as e:
        print(f"  [{module_name}] [ERROR] {e}")
        return 0


async def run_all_seeds(
    modules: dict[str, Callable],
    dry_run: bool,
    selected_module: str | None = None,
) -> int:
    """运行所有种子脚本

    Args:
        modules: 模块映射
        dry_run: 是否仅预览
        selected_module: 指定模块名，None 表示所有模块

    Returns:
        总初始化记录数
    """
    total = 0

    if selected_module:
        if selected_module not in modules:
            print(f"[ERROR] 未找到模块: {selected_module}")
            print(f"可用模块: {', '.join(modules.keys())}")
            return 0
        modules = {selected_module: modules[selected_module]}

    for name, func in modules.items():
        count = await run_seed(name, func, dry_run)
        total += count

    return total


async def main_async(args: argparse.Namespace) -> None:
    """异步主函数"""
    print("=" * 60)
    print("数据初始化")
    print("=" * 60)
    print()

    # 检查数据库连接
    if not check_database_connection():
        sys.exit(1)

    print()

    # 获取种子模块
    modules = get_seed_modules()
    if not modules:
        print("[WARN] 没有可初始化的模块")
        return

    available = ", ".join(modules.keys())
    print(f"[INFO] 可用模块: {available}")
    print()

    if args.dry_run:
        print("[DRY-RUN] 预览模式，不会实际写入数据库")
        print()

    # 运行种子脚本
    selected = args.module
    if selected and selected not in modules:
        print(f"[ERROR] 未找到模块: {selected}")
        print(f"可用模块: {available}")
        sys.exit(1)

    total = await run_all_seeds(modules, args.dry_run, selected)

    print()
    if args.dry_run:
        print(f"[DRY-RUN] 完成: 预览 {total} 条记录")
    else:
        print(f"[SUCCESS] 完成: 初始化 {total} 条记录")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="数据初始化脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  uv run python scripts/seed_data.py              # 初始化所有模块
  uv run python scripts/seed_data.py --dry-run    # 预览待初始化的数据
  uv run python scripts/seed_data.py --module tenant  # 初始化指定模块
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览待初始化的数据，不写入数据库",
    )
    parser.add_argument(
        "--module",
        type=str,
        default=None,
        help="指定要初始化的模块名",
    )

    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
