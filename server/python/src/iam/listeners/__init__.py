"""
IAM 模块监听器
"""

from iam.listeners.handlers.event_handler import (
    ModuleAssignedHandler,
    ModuleMenuCreatedHandler,
    ModuleMenuDeletedHandler,
    ModuleMenuUpdatedHandler,
    ModulePermissionCreatedHandler,
    ModulePermissionDeletedHandler,
    ModulePermissionUpdatedHandler,
    ModuleRoleCreatedHandler,
    ModuleRoleDeletedHandler,
    ModuleRolePermissionChangedHandler,
    ModuleRoleUpdatedHandler,
    ModuleUnassignedHandler,
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
