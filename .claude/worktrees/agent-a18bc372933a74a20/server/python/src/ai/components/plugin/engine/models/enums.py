"""
插件相关枚举定义
"""

from enum import Enum


class EnumBase(Enum):
    """枚举基类"""

    @classmethod
    def _missing_(cls, value):
        """支持通过值查找枚举成员"""
        for member in cls:
            if member.value == value:
                return member
        return None

    def __str__(self) -> str:
        return self.value


class RuntimeType(EnumBase):
    """运行时类型枚举"""

    LOCAL = "local"
    REMOTE = "remote"
    CONTAINER = "container"


class PluginType(EnumBase):
    """插件类型枚举"""

    MODEL = "model"  # AI模型插件（LLM、Embedding等）
    TOOL = "tool"  # 工具插件
    AGENT = "agent"  # AI代理插件
    OAUTH = "oauth"  # OAuth认证插件
    ENDPOINT = "endpoint"  # 端点插件


class InstallType(EnumBase):
    """安装类型枚举"""

    LOCAL = "local"
    REMOTE = "remote"


class SourceType(EnumBase):
    """来源类型枚举"""

    PACKAGE = "package"
    MARKETPLACE = "marketplace"


class TaskStatus(EnumBase):
    """任务状态枚举"""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class PluginStatus(EnumBase):
    """插件运行状态枚举"""

    ACTIVE = "active"  # 活跃状态
    INACTIVE = "inactive"  # 非活跃状态
