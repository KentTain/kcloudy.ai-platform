"""document 模块枚举（从 kbhub enums.py 精简迁移）"""

from enum import Enum


class LibraryType(str, Enum):
    """文档库类型"""
    PERSONAL = "personal"
    TEAM = "team"


class LibraryMemberRole(str, Enum):
    """文档库成员角色"""
    OWNER = "owner"
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    MEMBER = "member"
    VIEWER = "viewer"


class LibraryMemberStatus(str, Enum):
    """成员状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class LibraryRoleKind(str, Enum):
    """权限组类型"""
    ALL_MEMBERS = "all_members"
    CUSTOM = "custom"


class ResourceAclEffect(str, Enum):
    """资源 ACL 效果"""
    ALLOW = "allow"
    DENY = "deny"


class ResourceAclStatus(str, Enum):
    """资源 ACL 状态"""
    ACTIVE = "active"
    DISABLED = "disabled"


class ResourceType(str, Enum):
    """资源类型"""
    LIBRARY_ROOT = "library_root"
    FOLDER = "folder"
    DOCUMENT = "document"


class PermissionLevel(int, Enum):
    """权限等级：-1 未配置 / 0 无 / 1 只读 / 2 可编辑"""
    UNCONFIGURED = -1
    NONE = 0
    READONLY = 1
    EDITABLE = 2


class FolderLifecycleStatus(str, Enum):
    """文件夹生命周期"""
    ACTIVE = "active"
    TRASHED = "trashed"


class DocumentType(str, Enum):
    """文档类型"""
    DOCUMENT = "document"
    IMAGE = "image"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """文档生命周期"""
    UPLOADING = "uploading"
    ACTIVE = "active"
    TRASHED = "trashed"


class DocumentProcessingStatus(str, Enum):
    """文档处理状态"""
    PENDING_PARSE = "pending_parse"
    PARSING = "parsing"
    PARSED = "parsed"
    INDEXED = "indexed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


class RecycleItemStatus(str, Enum):
    """回收站状态"""
    IN_RECYCLE = "in_recycle"
    RESTORED = "restored"
    PURGED = "purged"


class MetadataFieldType(str, Enum):
    """元数据字段类型"""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    ENUM = "enum"
