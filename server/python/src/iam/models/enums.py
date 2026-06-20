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
