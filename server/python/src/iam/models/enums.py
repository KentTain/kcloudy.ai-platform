"""
IAM 模块枚举定义
"""

from enum import Enum

from framework.common.enums import EnumBase


class UserStatus(str, EnumBase):
    """用户状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"

    @property
    def label(self) -> str:
        labels = {
            UserStatus.ACTIVE: "激活",
            UserStatus.INACTIVE: "停用",
            UserStatus.LOCKED: "锁定",
        }
        return labels.get(self, self.name)


class OAuthProvider(str, EnumBase):
    """OAuth 提供商枚举"""

    WECHAT = "wechat"
    WEWORK = "wework"

    @property
    def label(self) -> str:
        labels = {
            OAuthProvider.WECHAT: "微信",
            OAuthProvider.WEWORK: "企业微信",
        }
        return labels.get(self, self.name)


class RoleCode(str, EnumBase):
    """角色编码枚举"""

    ADMIN = "admin"
    VIEWER = "viewer"

    @property
    def label(self) -> str:
        labels = {
            RoleCode.ADMIN: "管理员",
            RoleCode.VIEWER: "查看者",
        }
        return labels.get(self, self.name)


class OrganizationStatus(str, EnumBase):
    """组织状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"

    @property
    def label(self) -> str:
        labels = {
            OrganizationStatus.ACTIVE: "启用",
            OrganizationStatus.INACTIVE: "停用",
        }
        return labels.get(self, self.name)


class TenantStatus(str, Enum):
    """租户状态常量"""

    ACTIVE = "active"
    INACTIVE = "inactive"


class UserTenantRole(str, EnumBase):
    """用户租户角色枚举"""

    ADMIN = "admin"
    MEMBER = "member"

    @property
    def label(self) -> str:
        labels = {
            UserTenantRole.ADMIN: "管理员",
            UserTenantRole.MEMBER: "成员",
        }
        return labels.get(self, self.name)


class NotificationType(str, EnumBase):
    """站内信类型枚举"""

    IMPORT_REVIEW_PENDING = "import_review_pending"
    IMPORT_REVIEW_APPROVED = "import_review_approved"
    IMPORT_REVIEW_REJECTED = "import_review_rejected"
    PERMISSION_REQUEST_PENDING = "permission_request_pending"
    PERMISSION_REQUEST_APPROVED = "permission_request_approved"
    PERMISSION_REQUEST_REJECTED = "permission_request_rejected"
    SYSTEM = "system"

    @property
    def label(self) -> str:
        labels = {
            NotificationType.IMPORT_REVIEW_PENDING: "导入审核待处理",
            NotificationType.IMPORT_REVIEW_APPROVED: "导入审核已通过",
            NotificationType.IMPORT_REVIEW_REJECTED: "导入审核已拒绝",
            NotificationType.PERMISSION_REQUEST_PENDING: "权限申请待审批",
            NotificationType.PERMISSION_REQUEST_APPROVED: "权限申请已通过",
            NotificationType.PERMISSION_REQUEST_REJECTED: "权限申请已拒绝",
            NotificationType.SYSTEM: "系统通知",
        }
        return labels.get(self, self.name)


class PermissionRequestType(str, EnumBase):
    """权限申请类型枚举"""

    LIBRARY_JOIN = "library_join"
    LIBRARY_RESOURCE = "library_resource"
    LIBRARY_ROLE = "library_role"
    KNOWLEDGE_BASE_JOIN = "knowledge_base_join"
    KNOWLEDGE_BASE_ROLE = "knowledge_base_role"

    @property
    def label(self) -> str:
        labels = {
            PermissionRequestType.LIBRARY_JOIN: "加入文库",
            PermissionRequestType.LIBRARY_RESOURCE: "文库资源权限",
            PermissionRequestType.LIBRARY_ROLE: "文库角色",
            PermissionRequestType.KNOWLEDGE_BASE_JOIN: "加入知识库",
            PermissionRequestType.KNOWLEDGE_BASE_ROLE: "知识库角色",
        }
        return labels.get(self, self.name)


class PermissionRequestStatus(str, EnumBase):
    """权限申请状态枚举"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLYING = "applying"
    APPLIED = "applied"
    APPLY_FAILED = "apply_failed"

    @property
    def label(self) -> str:
        labels = {
            PermissionRequestStatus.PENDING: "待审批",
            PermissionRequestStatus.APPROVED: "已通过",
            PermissionRequestStatus.REJECTED: "已拒绝",
            PermissionRequestStatus.APPLYING: "生效中",
            PermissionRequestStatus.APPLIED: "已生效",
            PermissionRequestStatus.APPLY_FAILED: "生效失败",
        }
        return labels.get(self, self.name)

