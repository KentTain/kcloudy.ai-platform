#!/usr/bin/env python
"""
数据库迁移验证脚本

检查 Tenant 模块 schema 是否正确创建。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import text
from framework.configs import init_settings, get_settings
from framework.database import get_engine


async def check_tenant_schema():
    """检查 tenant schema 是否存在"""
    settings = get_settings()
    engine = get_engine(settings.sqlalchemy.url)

    async with engine.connect() as conn:
        # 检查 tenant schema
        result = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'tenant'"
            )
        )
        schema_exists = result.fetchone() is not None

        if schema_exists:
            print("✓ tenant schema 已创建")

            # 检查租户表
            result = await conn.execute(
                text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'tenant'
                    ORDER BY table_name
                """)
            )
            tables = [row[0] for row in result.fetchall()]
            print(f"✓ tenant schema 包含表: {', '.join(tables)}")

            # 检查 alembic_version
            result = await conn.execute(
                text("SELECT version_num FROM tenant.alembic_version")
            )
            version = result.fetchone()
            if version:
                print(f"✓ 迁移版本: {version[0]}")
            else:
                print("✗ 未找到迁移版本记录")
                return False
        else:
            print("✗ tenant schema 不存在")
            return False

    return True


async def check_iam_schema():
    """检查 iam schema 是否正确（不应包含租户表）"""
    settings = get_settings()
    engine = get_engine(settings.sqlalchemy.url)

    async with engine.connect() as conn:
        # 检查 iam schema 中不应存在的租户表
        result = await conn.execute(
            text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'iam'
                AND table_name IN ('tenants', 'tenant_configs', 'tenant_admins')
            """)
        )
        tables = [row[0] for row in result.fetchall()]

        if tables:
            print(f"✗ iam schema 仍包含租户表: {', '.join(tables)}")
            return False
        else:
            print("✓ iam schema 已移除租户表")

    return True


async def main():
    """主函数"""
    config_dir = Path(__file__).parent.parent.parent.parent / "config"
    init_settings(config_dir)

    print("=" * 60)
    print("验证 Tenant 模块迁移")
    print("=" * 60)

    results = []
    results.append(await check_tenant_schema())
    results.append(await check_iam_schema())

    print("=" * 60)
    if all(results):
        print("✓ 所有验证通过")
        return 0
    else:
        print("✗ 验证失败，请检查迁移")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
