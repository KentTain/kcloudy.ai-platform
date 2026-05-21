"""
IAM 模块枚举定义
"""

from enum import Enum

from models.enums import EnumBase


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

    TENANT_ADMIN = "tenant_admin"
    SYSTEM_ADMIN = "system_admin"
    USER = "user"

    @property
    def label(self) -> str:
        labels = {
            RoleCode.TENANT_ADMIN: "租户管理员",
            RoleCode.SYSTEM_ADMIN: "系统管理员",
            RoleCode.USER: "普通用户",
        }
        return labels.get(self, self.name)


class DepartmentStatus(str, EnumBase):
    """部门状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"

    @property
    def label(self) -> str:
        labels = {
            DepartmentStatus.ACTIVE: "启用",
            DepartmentStatus.INACTIVE: "停用",
        }
        return labels.get(self, self.name)


class TenantStatus(str, Enum):
    """租户状态常量"""

    ACTIVE = "active"
    INACTIVE = "inactive"
