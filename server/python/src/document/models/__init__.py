"""document 模块数据库模型"""

# 注意：framework.database.core 是命名空间包（无 __init__.py），
# create_base_model / create_module_base 由 framework.database 重新导出。
# 与 iam/models/__init__.py 保持一致的导入路径。
from framework.database import create_base_model, create_module_base

Base = create_module_base(schema="document")
BaseModel = create_base_model(Base)

from .config import ConfigItem
from .document import Document, DocumentVersion
from .enums import (
    DocumentProcessingStatus,
    DocumentStatus,
    DocumentType,
    FolderLifecycleStatus,
    LibraryMemberRole,
    LibraryMemberStatus,
    LibraryRoleKind,
    LibraryType,
    MetadataFieldType,
    PermissionLevel,
    RecycleItemStatus,
    ResourceAclEffect,
    ResourceAclStatus,
    ResourceType,
)
from .folder import Folder
from .library import Library, LibraryMember
from .metadata import LibraryMetadataField, ResourceMetadata
from .permission import LibraryRole, LibraryRoleMember, ResourceAcl
from .persona import Persona
from .recycle import RecycleItem
from .tag import Tag, TagGroup

__all__ = [
    # Base
    "Base",
    "BaseModel",
    # 文档库与成员
    "Library",
    "LibraryMember",
    # 文件夹
    "Folder",
    # 文档
    "Document",
    "DocumentVersion",
    # 权限
    "LibraryRole",
    "LibraryRoleMember",
    "ResourceAcl",
    # 标签与人设
    "Tag",
    "TagGroup",
    "Persona",
    # 元数据
    "LibraryMetadataField",
    "ResourceMetadata",
    # 回收站
    "RecycleItem",
    # 配置
    "ConfigItem",
]
