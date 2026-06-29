"""运行 tenant 模块的迁移"""

import asyncio
import sys
from pathlib import Path

# 添加 src 目录到路径
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from alembic.config import Config
from alembic import command


def run_migration():
    """运行 tenant 模块的迁移"""
    # 创建 Alembic 配置
    alembic_cfg = Config()
    alembic_cfg.set_section_option("alembic", "script_location", "src/tenant/migrations")
    alembic_cfg.set_section_option("alembic", "sqlalchemy.url", "postgresql+asyncpg://admin:XdA9caoq@localhost:5432/alon_demo")

    # 运行迁移
    command.upgrade(alembic_cfg, "head")
    print("Migration completed successfully!")


if __name__ == "__main__":
    run_migration()

