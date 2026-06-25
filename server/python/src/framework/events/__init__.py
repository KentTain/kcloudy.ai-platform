"""
领域事件模块

提供领域事件的定义和发布能力。
"""

from framework.events.base import DomainEvent
from framework.events.domain_events import (
    ModuleAssigned,
    ModuleMenuCreated,
    ModuleMenuDeleted,
    ModuleMenuPermissionCreated,
    ModuleMenuPermissionDeleted,
    ModuleMenuUpdated,
    ModulePermissionCreated,
    ModulePermissionDeleted,
    ModulePermissionUpdated,
    ModuleRoleCreated,
    ModuleRoleDeleted,
    ModuleRolePermissionChanged,
    ModuleRolePermissionCreated,
    ModuleRolePermissionDeleted,
    ModuleRoleUpdated,
    ModuleUnassigned,
)
from framework.events.domain_events import (
    ModuleAssigned,
    ModuleMenuCreated,
    ModuleMenuDeleted,
    ModuleMenuPermissionCreated,
    ModuleMenuPermissionDeleted,
    ModuleMenuUpdated,
    ModulePermissionCreated,
    ModulePermissionDeleted,
    ModulePermissionUpdated,
    ModuleRoleCreated,
    ModuleRoleDeleted,
    ModuleRolePermissionChanged,
    ModuleRolePermissionCreated,
    ModuleRolePermissionDeleted,
    ModuleRoleUpdated,
    ModuleUnassigned,
    PluginInstallationFailed,
    PluginUninstallFailed,
)
from framework.events.publisher import EventPublisher, event_publisher

__all__ = [
    # 基类
    "DomainEvent",
    # 模块分配事件
    "ModuleAssigned",
    "ModuleUnassigned",
    # 模块菜单事件
    "ModuleMenuCreated",
    "ModuleMenuUpdated",
    "ModuleMenuDeleted",
    # 模块权限事件
    "ModulePermissionCreated",
    "ModulePermissionUpdated",
    "ModulePermissionDeleted",
    # 模块角色事件
    "ModuleRoleCreated",
    "ModuleRoleUpdated",
    "ModuleRoleDeleted",
    "ModuleRolePermissionChanged",
    "ModuleRolePermissionCreated",
    "ModuleRolePermissionDeleted",
    # 模块菜单权限事件
    "ModuleMenuPermissionCreated",
    "ModuleMenuPermissionDeleted",
    # 插件事件
    "PluginInstallationFailed",
    "PluginUninstallFailed",
    # 发布器
    "EventPublisher",
    "event_publisher",
]
