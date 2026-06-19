"""
领域事件模块

提供领域事件的定义和发布能力。
"""

from framework.events.base import DomainEvent
from framework.events.domain_events import (
    ModuleAssigned,
    ModuleUnassigned,
    ModuleMenuCreated,
    ModuleMenuUpdated,
    ModuleMenuDeleted,
    ModulePermissionCreated,
    ModulePermissionUpdated,
    ModulePermissionDeleted,
    ModuleRoleCreated,
    ModuleRoleUpdated,
    ModuleRoleDeleted,
    ModuleRolePermissionChanged,
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
    # 发布器
    "EventPublisher",
    "event_publisher",
]
