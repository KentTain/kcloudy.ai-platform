"""
Tenant 模块枚举定义
"""

from enum import Enum

from framework.common.enums import EnumBase


class TenantStatus(str, Enum):
    """租户状态常量"""

    ACTIVE = "active"
    INACTIVE = "inactive"


class TenantAdminRole(str, EnumBase):
    """租户管理员角色枚举"""

    ORDINARY_ADMIN = "ordinaryAdmin"
    TENANT_ADMIN = "tenantAdmin"

    @property
    def label(self) -> str:
        labels = {
            TenantAdminRole.ORDINARY_ADMIN: "普通管理员",
            TenantAdminRole.TENANT_ADMIN: "租户管理员",
        }
        return labels.get(self, self.name)


class PluginInstallationStatus(str, EnumBase):
    """插件安装状态枚举"""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"

    @property
    def label(self) -> str:
        labels = {
            PluginInstallationStatus.PENDING: "待安装",
            PluginInstallationStatus.ACTIVE: "已激活",
            PluginInstallationStatus.INACTIVE: "已停用",
            PluginInstallationStatus.FAILED: "安装失败",
        }
        return labels.get(self, self.name)


class PluginInstallType(str, EnumBase):
    """插件安装类型枚举"""

    LOCAL = "local"
    REMOTE = "remote"

    @property
    def label(self) -> str:
        labels = {
            PluginInstallType.LOCAL: "本地安装",
            PluginInstallType.REMOTE: "远程安装",
        }
        return labels.get(self, self.name)
