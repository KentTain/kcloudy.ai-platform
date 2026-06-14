"""
菜单数据初始化

初始化默认菜单配置。

---
已废弃 (DEPRECATED)
---

此 seed 脚本已废弃，功能已迁移至模块元数据声明系统。

新的实现方式：
在 `src/{module}/module.py` 中实现 `get_module_definition()` 方法，
声明菜单、权限、角色等元数据。系统启动时会自动同步到数据库。

示例：
```python
def get_module_definition(self) -> ModuleDefinition:
    return ModuleDefinition(
        code="iam",
        menus=[
            MenuDef(code="iam.users", name="用户管理", path="/iam/users"),
            MenuDef(code="iam.roles", name="角色管理", path="/iam/roles"),
        ],
        permissions=[...],
        default_roles=[...],
    )
```

参考：
- framework/module/definition.py - 数据结构定义
- framework/module/sync_service.py - 同步服务
- iam/module.py - IAM 模块实现示例

保留此文件仅供参考，未来版本将删除。
---

from __future__ import annotations

import uuid

from sqlalchemy import select

from framework.utils.log_util import write_info, write_success, write_warning
from iam.models import Menu, MenuPermission, Permission

# 默认菜单配置
# 每个菜单项包含：module, code, name, path, icon, parent_code, permissions
DEFAULT_MENUS = [
    # Demo 模块
    {
        "module": "demo",
        "code": "demo:home",
        "name": "首页",
        "path": "/home",
        "icon": "home",
        "parent_code": None,
        "permissions": [],  # 无权限限制，所有用户可见
    },
    {
        "module": "demo",
        "code": "demo:knowledge",
        "name": "知识库",
        "path": "/knowledge",
        "icon": "book-open",
        "parent_code": None,
        "permissions": [],  # 无权限限制
    },
    # IAM 模块
    {
        "module": "iam",
        "code": "iam:management",
        "name": "系统管理",
        "path": "/system",
        "icon": "settings",
        "parent_code": None,
        "permissions": [],  # 目录菜单，无权限限制
    },
    {
        "module": "iam",
        "code": "iam:users",
        "name": "用户管理",
        "path": "/system/users",
        "icon": "users",
        "parent_code": "iam:management",
        "permissions": ["user:read"],
    },
    {
        "module": "iam",
        "code": "iam:roles",
        "name": "角色管理",
        "path": "/system/roles",
        "icon": "shield",
        "parent_code": "iam:management",
        "permissions": ["role:read"],
    },
    {
        "module": "iam",
        "code": "iam:departments",
        "name": "部门管理",
        "path": "/system/departments",
        "icon": "building",
        "parent_code": "iam:management",
        "permissions": ["department:read"],
    },
    # Tenant 模块
    {
        "module": "tenant",
        "code": "tenant:management",
        "name": "租户管理",
        "path": "/tenant",
        "icon": "building-2",
        "parent_code": None,
        "permissions": ["tenant:read"],
    },
]


async def run(*, dry_run: bool = False) -> int:
    """初始化菜单数据

    创建默认菜单及其权限关联。

    场景：执行种子数据初始化
    WHEN 执行 `manage.py seed --module iam`
    THEN 系统创建默认菜单及其权限关联

    场景：种子数据幂等性
    WHEN 多次执行种子数据初始化
    THEN 已存在的菜单不重复创建

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from framework.database.core.engine import get_session

    async with get_session() as session:
        created_count = 0

        # 1. 检查已存在的菜单
        existing_menus = {}
        result = await session.execute(select(Menu.code, Menu.id))
        for row in result.fetchall():
            existing_menus[row[0]] = row[1]

        # 2. 获取所有权限
        all_permissions = {}
        result = await session.execute(select(Permission))
        for perm in result.scalars():
            all_permissions[perm.code] = perm

        # 3. 创建菜单
        menu_map = {}  # code -> Menu 对象

        # 获取已存在的菜单对象
        for menu_data in DEFAULT_MENUS:
            code = menu_data["code"]
            if code in existing_menus:
                result = await session.execute(select(Menu).where(Menu.code == code))
                menu_map[code] = result.scalar_one()

        # 按层级顺序创建菜单（先创建父菜单）
        menus_to_create = []
        pending = list(DEFAULT_MENUS)

        while pending:
            for menu_data in pending[:]:
                code = menu_data["code"]
                parent_code = menu_data.get("parent_code")

                # 如果菜单已存在，跳过
                if code in menu_map:
                    pending.remove(menu_data)
                    continue

                # 如果父菜单不存在且需要父菜单，等待
                if parent_code and parent_code not in menu_map:
                    continue

                # 准备创建菜单
                menus_to_create.append(menu_data)
                pending.remove(menu_data)

        # 4. 使用 TreeNodeMixin.create_node 创建菜单
        if dry_run:
            for menu_data in menus_to_create:
                write_info(
                    f"    [DRY-RUN] 将创建菜单: {menu_data['code']} - {menu_data['name']}"
                )
                # 显示权限关联
                for perm_code in menu_data.get("permissions", []):
                    write_info(f"    [DRY-RUN] 将关联权限: {perm_code}")
        else:
            for menu_data in menus_to_create:
                code = menu_data["code"]
                parent_code = menu_data.get("parent_code")

                # 构建菜单属性
                source = {
                    "module": menu_data["module"],
                    "code": code,
                    "name": menu_data["name"],
                    "path": menu_data["path"],
                    "icon": menu_data.get("icon"),
                    "is_visible": True,
                    "deployment_base_url": None,
                }

                # 设置父菜单 ID
                if parent_code and parent_code in menu_map:
                    source["parent_id"] = menu_map[parent_code].id

                # 使用 TreeNodeMixin.create_node 创建菜单
                menu = await Menu.create_node(session, source)
                await session.flush()
                menu_map[code] = menu
                created_count += 1
                write_success(f"    已创建菜单: {menu.code} - {menu.name}")

            # 5. 创建菜单-权限关联
            for menu_data in DEFAULT_MENUS:
                code = menu_data["code"]
                menu = menu_map.get(code)
                if not menu:
                    continue

                for perm_code in menu_data.get("permissions", []):
                    if perm_code not in all_permissions:
                        write_warning(f"    [WARN] 权限 {perm_code} 不存在，跳过关联")
                        continue

                    # 检查是否已存在
                    result = await session.execute(
                        select(MenuPermission).where(
                            MenuPermission.menu_id == menu.id,
                            MenuPermission.permission_id
                            == all_permissions[perm_code].id,
                        )
                    )
                    if result.scalar_one_or_none():
                        continue

                    mp = MenuPermission(
                        id=str(uuid.uuid4()),
                        menu_id=menu.id,
                        permission_id=all_permissions[perm_code].id,
                    )
                    session.add(mp)
                    created_count += 1

            await session.commit()

        return created_count
