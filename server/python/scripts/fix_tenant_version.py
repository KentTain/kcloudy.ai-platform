"""修复 tenant 模块的迁移版本号"""

import asyncio
import asyncpg


async def fix_version():
    conn = await asyncpg.connect("postgresql://admin:XdA9caoq@localhost:5432/alon_demo")
    await conn.execute("UPDATE tenant.alembic_version SET version_num = '002_tenant_enum_and_comment'")
    print("Updated version to 002_tenant_enum_and_comment")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(fix_version())

