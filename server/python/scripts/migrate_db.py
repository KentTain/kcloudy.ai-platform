#!/usr/bin/env python3
"""
数据库迁移脚本

运行 Alembic 数据库迁移，创建缺失的表。

用法：
    uv run python scripts/migrate_db.py              # 执行迁移
    uv run python scripts/migrate_db.py --dry-run    # 仅预览待执行的迁移
    uv run python scripts/migrate_db.py --status     # 查看当前迁移状态
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Windows 控制台编码处理
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]


def run_alembic(args: list[str], description: str = "") -> tuple[bool, str]:
    """运行 alembic 命令

    Args:
        args: alembic 命令参数
        description: 操作描述

    Returns:
        (成功标志, 输出内容)
    """
    cmd = ["alembic"] + args
    cmd_str = " ".join(cmd)

    if description:
        print(f"[INFO] {description}...")
    print(f"  执行: {cmd_str}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=Path(__file__).parent.parent,  # 切换到 server/python 目录
        )

        if result.stdout:
            print(result.stdout)

        if result.returncode != 0:
            if result.stderr:
                print(f"[ERROR] {result.stderr}")
            return False, result.stderr or ""

        return True, result.stdout

    except FileNotFoundError:
        print("[ERROR] alembic 命令未找到，请确保已安装依赖: uv sync")
        return False, ""
    except Exception as e:
        print(f"[ERROR] 执行失败: {e}")
        return False, str(e)


def check_database_connection() -> bool:
    """检查数据库连接

    Returns:
        是否连接成功
    """
    print("[INFO] 检查数据库连接...")

    try:
        # 尝试导入配置
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from demo.configs import settings

        db_url = settings.sqlalchemy.url
        # 隐藏密码
        if "@" in db_url:
            parts = db_url.split("@")
            safe_url = parts[0].rsplit(":", 1)[0] + ":***@" + parts[1]
        else:
            safe_url = db_url

        print(f"  数据库: {safe_url}")
        return True

    except Exception as e:
        print(f"[ERROR] 加载配置失败: {e}")
        print("  请确保配置文件存在: server/config/application-local.yml")
        return False


def show_status() -> None:
    """显示当前迁移状态"""
    print("=" * 60)
    print("数据库迁移状态")
    print("=" * 60)

    # 检查数据库连接
    if not check_database_connection():
        return

    print()

    # 显示当前版本
    success, _ = run_alembic(["current"], "当前数据库版本")

    if success:
        print()
        # 显示迁移历史
        run_alembic(["history"], "迁移历史")


def run_upgrade(dry_run: bool = False) -> None:
    """执行数据库迁移

    Args:
        dry_run: 是否仅预览
    """
    print("=" * 60)
    print("数据库迁移")
    print("=" * 60)

    # 检查数据库连接
    if not check_database_connection():
        sys.exit(1)

    print()

    if dry_run:
        print("[DRY-RUN] 预览待执行的迁移...")
        run_alembic(["upgrade", "head", "--sql"], "待执行的 SQL")
    else:
        success, _ = run_alembic(["upgrade", "head"], "执行数据库迁移")

        if success:
            print()
            print("[SUCCESS] 数据库迁移完成")
            print()
            run_alembic(["current"], "当前版本")
        else:
            print()
            print("[FAILED] 数据库迁移失败")
            sys.exit(1)


def run_downgrade(revision: str = "-1") -> None:
    """回滚数据库迁移

    Args:
        revision: 目标版本号，默认回滚一个版本
    """
    print("=" * 60)
    print("数据库迁移回滚")
    print("=" * 60)

    # 检查数据库连接
    if not check_database_connection():
        sys.exit(1)

    print()

    success, _ = run_alembic(["downgrade", revision], f"回滚到版本: {revision}")

    if success:
        print()
        print("[SUCCESS] 回滚完成")
        run_alembic(["current"], "当前版本")
    else:
        print()
        print("[FAILED] 回滚失败")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="数据库迁移脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  uv run python scripts/migrate_db.py              # 执行迁移
  uv run python scripts/migrate_db.py --dry-run    # 预览迁移 SQL
  uv run python scripts/migrate_db.py --status     # 查看状态
  uv run python scripts/migrate_db.py --downgrade  # 回滚一个版本
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览待执行的迁移 SQL，不实际执行",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="显示当前迁移状态",
    )
    parser.add_argument(
        "--downgrade",
        action="store_true",
        help="回滚数据库迁移",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default="-1",
        help="目标版本号（用于 downgrade），默认 -1（回滚一个版本）",
    )

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.downgrade:
        run_downgrade(args.revision)
    else:
        run_upgrade(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
