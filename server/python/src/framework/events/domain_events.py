"""
租户模块领域事件

定义租户模块相关的所有领域事件。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from framework.events.base import DomainEvent, EventStream


# =============================================================================
# 模块分配事件
# =============================================================================


@dataclass
class ModuleAssigned(DomainEvent):
    """
    模块分配事件

    触发时机：租户分配模块成功后
    携带数据：tenant_id, module_id

    消费者：
    - IAM 服务：同步创建模块角色到租户实例层
    """

    tenant_id: str = ""
    module_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_ASSIGNED


@dataclass
class ModuleUnassigned(DomainEvent):
    """
    模块取消分配事件

    触发时机：租户取消模块分配成功后
    携带数据：tenant_id, module_id

    消费者：
    - IAM 服务：同步删除租户实例层的模块角色
    """

    tenant_id: str = ""
    module_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_UNASSIGNED


# =============================================================================
# 模块菜单事件
# =============================================================================


@dataclass
class ModuleMenuCreated(DomainEvent):
    """
    模块菜单创建事件

    触发时机：模块新增菜单成功后
    携带数据：module_menu_id

    消费者：
    - IAM 服务：同步创建菜单到已分配该模块的租户实例层
    """

    module_menu_id: str = ""
    module_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_MENU_CREATED


@dataclass
class ModuleMenuUpdated(DomainEvent):
    """
    模块菜单更新事件

    触发时机：模块菜单更新成功后
    携带数据：module_menu_id

    消费者：
    - IAM 服务：同步更新已分配该模块的租户实例层菜单
    """

    module_menu_id: str = ""
    module_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_MENU_UPDATED


@dataclass
class ModuleMenuDeleted(DomainEvent):
    """
    模块菜单删除事件

    触发时机：模块菜单删除成功后
    携带数据：module_id, menu_code

    消费者：
    - IAM 服务：同步删除已分配该模块的租户实例层菜单
    """

    module_id: str = ""
    menu_code: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_MENU_DELETED


# =============================================================================
# 模块权限事件
# =============================================================================


@dataclass
class ModulePermissionCreated(DomainEvent):
    """
    模块权限创建事件

    触发时机：模块新增权限成功后
    携带数据：module_permission_id

    消费者：
    - IAM 服务：同步创建权限到已分配该模块的租户实例层
    """

    module_permission_id: str = ""
    module_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_PERMISSION_CREATED


@dataclass
class ModulePermissionUpdated(DomainEvent):
    """
    模块权限更新事件

    触发时机：模块权限更新成功后
    携带数据：module_permission_id

    消费者：
    - IAM 服务：同步更新已分配该模块的租户实例层权限
    """

    module_permission_id: str = ""
    module_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_PERMISSION_UPDATED


@dataclass
class ModulePermissionDeleted(DomainEvent):
    """
    模块权限删除事件

    触发时机：模块权限删除成功后
    携带数据：module_id, permission_code

    消费者：
    - IAM 服务：同步删除已分配该模块的租户实例层权限
    """

    module_id: str = ""
    permission_code: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_PERMISSION_DELETED


# =============================================================================
# 模块角色事件
# =============================================================================


@dataclass
class ModuleRoleCreated(DomainEvent):
    """
    模块角色创建事件

    触发时机：模块新增角色成功后
    携带数据：module_role_id

    消费者：
    - IAM 服务：同步创建角色到已分配该模块的租户实例层
    """

    module_role_id: str = ""
    module_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_ROLE_CREATED


@dataclass
class ModuleRoleUpdated(DomainEvent):
    """
    模块角色更新事件

    触发时机：模块角色更新成功后
    携带数据：module_role_id

    消费者：
    - IAM 服务：同步更新已分配该模块的租户实例层角色
    """

    module_role_id: str = ""
    module_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_ROLE_UPDATED


@dataclass
class ModuleRoleDeleted(DomainEvent):
    """
    模块角色删除事件

    触发时机：模块角色删除成功后
    携带数据：module_id, role_code

    消费者：
    - IAM 服务：同步删除已分配该模块的租户实例层角色
    """

    module_id: str = ""
    role_code: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_ROLE_DELETED


@dataclass
class ModuleRolePermissionChanged(DomainEvent):
    """
    模块角色权限变更事件

    触发时机：模块角色的权限列表变更后
    携带数据：module_role_id

    消费者：
    - IAM 服务：同步更新已分配该模块的租户实例层角色权限
    """

    module_role_id: str = ""
    module_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_ROLE_PERMISSION_CHANGED


# =============================================================================
# 模块角色权限关联事件（细化）
# =============================================================================


@dataclass
class ModuleRolePermissionCreated(DomainEvent):
    """
    模块角色权限关联创建事件

    触发时机：模块角色新增权限关联成功后
    携带数据：module_role_permission_id

    消费者：
    - IAM 服务：同步创建角色权限关联到已分配该模块的租户实例层
    """

    module_role_permission_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_ROLE_PERMISSION_CREATED


@dataclass
class ModuleRolePermissionDeleted(DomainEvent):
    """
    模块角色权限关联删除事件

    触发时机：模块角色删除权限关联成功后
    携带数据：module_role_id, module_permission_id

    消费者：
    - IAM 服务：同步删除已分配该模块的租户实例层角色权限关联
    """

    module_role_id: str = ""
    module_permission_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_ROLE_PERMISSION_DELETED


# =============================================================================
# 模块菜单权限关联事件
# =============================================================================


@dataclass
class ModuleMenuPermissionCreated(DomainEvent):
    """
    模块菜单权限关联创建事件

    触发时机：模块新增菜单权限关联成功后
    携带数据：module_menu_permission_id

    消费者：
    - IAM 服务：同步创建菜单权限关联到已分配该模块的租户实例层
    """

    module_menu_permission_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_MENU_PERMISSION_CREATED


@dataclass
class ModuleMenuPermissionDeleted(DomainEvent):
    """
    模块菜单权限关联删除事件

    触发时机：模块删除菜单权限关联成功后
    携带数据：module_menu_id, module_permission_id

    消费者：
    - IAM 服务：同步删除已分配该模块的租户实例层菜单权限关联
    """

    module_menu_id: str = ""
    module_permission_id: str = ""

    @classmethod
    def get_stream_name(cls) -> str:
        return EventStream.MODULE_MENU_PERMISSION_DELETED
