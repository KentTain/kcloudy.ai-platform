"""验证 tenant 模块的迁移并直接应用表级 comment"""

import asyncio
import asyncpg

TABLE_COMMENTS = {
    "tenants": "租户表",
    "tenant_admins": "租户管理员表",
    "plugin_installations": "插件安装记录表",
    "plugin_definitions": "插件定义表",
    "modules": "模块定义表",
    "module_permissions": "模块权限表",
    "module_roles": "模块角色表",
    "tenant_modules": "租户模块分配表",
    "module_menus": "模块菜单定义表",
    "module_menu_permissions": "模块菜单-权限关联表",
    "module_role_permissions": "模块角色-权限关联表",
    "cache_configs": "缓存配置表",
    "database_configs": "数据库配置表",
    "pubsub_configs": "发布订阅配置表",
    "queue_configs": "队列配置表",
    "storage_configs": "存储配置表",
    "tenant_configs": "租户配置表",
    "tenant_business_configs": "租户业务配置表",
}


async def apply_comments(conn):
    """应用表级 comment"""
    for table, comment in TABLE_COMMENTS.items():
        await conn.execute(f"COMMENT ON TABLE tenant.{table} IS '{comment}'")
        print(f"Applied comment to {table}")

    # 更新迁移版本
    await conn.execute(
        "UPDATE tenant.alembic_version SET version_num = '002_tenant_enum_and_comment'"
    )
    print("Updated migration version to 002_tenant_enum_and_comment")


async def verify():
    """验证数据库中的表级 comment 和 EnumType"""
    conn = await asyncpg.connect("postgresql://admin:XdA9caoq@localhost:5432/alon_demo")

    try:
        # 检查迁移版本
        version = await conn.fetchval(
            "SELECT version_num FROM tenant.alembic_version"
        )
        print(f"Current tenant migration version: {version}")

        # 应用表级 comment
        print("\nApplying table comments...")
        await apply_comments(conn)
        await conn.execute("COMMIT")

        # 检查表级 comment
        tables = await conn.fetch("""
            SELECT tablename, obj_description((schemaname || '.' || tablename)::regclass) as comment
            FROM pg_tables
            WHERE schemaname = 'tenant'
            ORDER BY tablename
        """)

        print("\n表级 comment:")
        for table in tables:
            print(f"  {table['tablename']}: {table['comment']}")

        # 检查 tenants 表的 status 字段类型
        column_info = await conn.fetch("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'tenant' AND table_name = 'tenants' AND column_name = 'status'
        """)

        print("\ntenants.status 字段类型:")
        for col in column_info:
            print(f"  {col['column_name']}: {col['data_type']} ({col['udt_name']})")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(verify())
