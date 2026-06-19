"""
模块定义数据结构

定义模块元数据声明的数据结构，包括菜单、权限、角色等。
"""

from dataclasses import dataclass, field


@dataclass
class MenuDef:
    """
    菜单定义

    用于声明模块的菜单项，系统启动时会同步到数据库。

    Attributes:
        code: 唯一标识，格式为 <module>.<name>，如 "iam.users"
        name: 显示名称
        path: 前端路由路径
        icon: 图标标识（可选）
        parent_code: 父菜单 code（可选）
        sort_order: 排序顺序，默认为 0
        is_visible: 是否可见，默认为 True
    """

    code: str
    name: str
    path: str
    icon: str | None = None
    parent_code: str | None = None
    sort_order: int = 0
    is_visible: bool = True


@dataclass
class PermissionDef:
    """
    权限定义

    用于声明模块的权限项，系统启动时会同步到数据库。

    Attributes:
        code: 唯一标识，格式为 <module>:<resource>:<action>，如 "iam:user:read"
        name: 显示名称
        resource: 资源名称
        action: 操作类型：read/write/delete
        description: 权限描述（可选）
    """

    code: str
    name: str
    resource: str
    action: str
    description: str | None = None


@dataclass
class RoleDef:
    """
    角色定义

    用于声明模块的默认角色，系统启动时会同步到数据库。

    Attributes:
        code: 角色编码
        name: 角色名称
        description: 角色描述（可选）
        permission_codes: 关联的权限 code 列表
        is_system: 是否系统内置角色，默认为 False
    """

    code: str
    name: str
    description: str | None = None
    permission_codes: list[str] = field(default_factory=list)
    is_system: bool = False


@dataclass
class ModuleDefinition:
    """
    模块定义

    模块元数据的完整声明，包括菜单、权限、角色等。
    模块通过实现 get_module_definition() 方法返回此定义。

    Attributes:
        code: 模块编码
        name: 模块名称
        description: 模块描述（可选）
        icon: 图标标识（可选）
        version: 模块版本，默认为 "1.0.0"
        menus: 菜单定义列表
        permissions: 权限定义列表
        default_roles: 默认角色定义列表
    """

    code: str
    name: str
    description: str | None = None
    icon: str | None = None
    version: str = "1.0.0"
    menus: list[MenuDef] = field(default_factory=list)
    permissions: list[PermissionDef] = field(default_factory=list)
    default_roles: list[RoleDef] = field(default_factory=list)
