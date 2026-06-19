"""
IAM 模块事件处理器
"""

from iam.listeners.handlers.event_handler import (
    ModuleAssignedHandler,
    ModuleUnassignedHandler,
    ModuleMenuCreatedHandler,
    ModuleMenuUpdatedHandler,
    ModuleMenuDeletedHandler,
    ModulePermissionCreatedHandler,
    ModulePermissionUpdatedHandler,
    ModulePermissionDeletedHandler,
    ModuleRoleCreatedHandler,
    ModuleRoleUpdatedHandler,
    ModuleRoleDeletedHandler,
    ModuleRolePermissionChangedHandler,
)

__all__ = [
    "ModuleAssignedHandler",
    "ModuleUnassignedHandler",
    "ModuleMenuCreatedHandler",
    "ModuleMenuUpdatedHandler",
    "ModuleMenuDeletedHandler",
    "ModulePermissionCreatedHandler",
    "ModulePermissionUpdatedHandler",
    "ModulePermissionDeletedHandler",
    "ModuleRoleCreatedHandler",
    "ModuleRoleUpdatedHandler",
    "ModuleRoleDeletedHandler",
    "ModuleRolePermissionChangedHandler",
]
