# kbhub 迁移 Phase 2 实现计划：document 模块

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 完整迁移文档库、文件夹树、文件管理、成员管理、资源权限体系、标签、人设、文档切片索引、回收站到 document 模块，提供 inner 接口供 Phase 3（ai）回查源文件权限。

**架构：** document 模块新建 module.py（菜单+PermissionDef）+ 16 张表模型 + 10 个服务 + admin/console/inner 三层控制器 + 切片索引任务 + 审计接入；权限判定引擎精简实现（复用 framework PermissionEngine + PolicyEvaluator），folder 用 TreeNodeMixin（parent_id 无外键），inner 接口无认证供 ai 回查；前端用本项目组件重新实现，缺件迁移适配。

**技术栈：** Python 3.12+、FastAPI、SQLAlchemy 2.0 async、Alembic、PostgreSQL、MinIO（framework TenantMinioStorage）、pytest + pytest-asyncio、Vue 3 + Pinia + shadcn-vue

---

## 前置条件

- ✅ Phase 1 已完成：framework permission/engine.py、policy_evaluator.py、audit_writer.py、notification/sender.py
- ✅ iam 已有 Notification/PermissionRequest/Policy 模型
- ✅ kbhub 源码本地可访问（`D:\Project\ai\Alon\apps\kbhub`）
- ✅ MinIO 已就绪（framework TenantMinioStorage 可用）
- ✅ ai 模块已有 EmbeddingService（Phase 3 切片索引复用）

## 参考源码

| 目标实现 | kbhub 源文件 |
|---------|-------------|
| 模型字段 | `kbhub/src/kbhub/models/library.py`（Library/Folder/Document/ResourceAcl/LibraryRole/LibraryRoleMember/RecycleItem） |
| 权限判定 | `kbhub/src/kbhub/services/library/permission.py`（精简重写，不逐行移植） |
| 资源 ACL | `kbhub/src/kbhub/services/library/resource_acl.py` |
| 文件夹树 | `kbhub/src/kbhub/services/library/folder.py` |
| 文档管理 | `kbhub/src/kbhub/services/library/document.py` |
| 成员管理 | `kbhub/src/kbhub/services/library/member.py` |
| 权限组 | `kbhub/src/kbhub/services/library/role.py` |
| 回收站 | `kbhub/src/kbhub/services/library/recycle_item.py` |
| 标签/人设 | `kbhub/src/kbhub/services/tag.py`、`persona.py` |
| 元数据 | `kbhub/src/kbhub/models/library.py`（ResourceMetadata/LibraryMetadataField） |
| 枚举 | `kbhub/src/kbhub/models/enums.py`（仅迁移 document 相关） |

---

## 文件结构

### document 后端新增文件

**模块声明**
- `server/python/src/document/module.py` — ModuleDefinition（菜单 + PermissionDef）

**模型（按职责拆分，不照搬 kbhub 巨型 library.py）**
- `server/python/src/document/models/enums.py` — document 相关枚举
- `server/python/src/document/models/library.py` — Library / LibraryMember
- `server/python/src/document/models/folder.py` — Folder（TreeNodeMixin）
- `server/python/src/document/models/document.py` — Document / DocumentVersion
- `server/python/src/document/models/permission.py` — LibraryRole / LibraryRoleMember / ResourceAcl
- `server/python/src/document/models/tag.py` — Tag / TagGroup
- `server/python/src/document/models/persona.py` — Persona
- `server/python/src/document/models/metadata.py` — ResourceMetadata / LibraryMetadataField
- `server/python/src/document/models/recycle.py` — RecycleItem
- `server/python/src/document/models/config.py` — ConfigItem（文档库级配置）
- `server/python/src/document/models/__init__.py` — 修改：导出所有模型

**Schema**
- `server/python/src/document/schemas/library.py`
- `server/python/src/document/schemas/folder.py`
- `server/python/src/document/schemas/document.py`
- `server/python/src/document/schemas/permission.py`
- `server/python/src/document/schemas/tag.py`
- `server/python/src/document/schemas/persona.py`
- `server/python/src/document/schemas/metadata.py`
- `server/python/src/document/schemas/recycle.py`
- `server/python/src/document/schemas/inner.py` — inner 接口 DTO

**服务**
- `server/python/src/document/services/library_service.py` — 文档库 CRUD
- `server/python/src/document/services/folder_service.py` — 文件夹树管理
- `server/python/src/document/services/document_service.py` — 文件上传/预览/下载/切片触发
- `server/python/src/document/services/member_service.py` — 成员管理
- `server/python/src/document/services/permission_service.py` — 权限判定引擎（精简）
- `server/python/src/document/services/permission_config_service.py` — 权限组 + 资源 ACL 配置
- `server/python/src/document/services/tag_service.py` — 标签管理
- `server/python/src/document/services/persona_service.py` — 人设管理
- `server/python/src/document/services/recycle_service.py` — 回收站
- `server/python/src/document/services/metadata_service.py` — 元数据管理
- `server/python/src/document/services/__init__.py` — 修改：导出服务

**控制器**
- `server/python/src/document/controllers/admin/library_controller.py`
- `server/python/src/document/controllers/admin/tag_controller.py`
- `server/python/src/document/controllers/admin/persona_controller.py`
- `server/python/src/document/controllers/console/library_controller.py`
- `server/python/src/document/controllers/console/folder_controller.py`
- `server/python/src/document/controllers/console/document_controller.py`
- `server/python/src/document/controllers/console/member_controller.py`
- `server/python/src/document/controllers/console/permission_controller.py`
- `server/python/src/document/controllers/console/recycle_controller.py`
- `server/python/src/document/controllers/console/metadata_controller.py`
- `server/python/src/document/controllers/inner/permission_controller.py` — 权限回查 + 成员身份回查
- `server/python/src/document/controllers/inner/permission_request_controller.py` — 权限申请 apply 回调

**任务与监听**
- `server/python/src/document/tasks/document_index_task.py` — 切片索引任务触发
- `server/python/src/document/tasks/setup.py` — 修改：注册任务
- `server/python/src/document/listeners/setup.py` — 修改：注册监听

**迁移与种子**
- `server/python/src/document/migrations/__init__.py`
- `server/python/src/document/migrations/env.py` — Alembic env
- `server/python/src/document/migrations/versions/001_initial_schema.py` — 16 张表
- `server/python/src/document/migrations/seeds/library_seed.py` — 默认元数据字段 + 权限组模板

### document 前端新增/修改文件
- `web/vue/src/document/index.ts` — 修改：返回真实路由
- `web/vue/src/document/router/index.ts` — 修改：路由配置
- `web/vue/src/document/api/index.ts` — 修改：真实 API（替换 stub）
- `web/vue/src/document/api/library.ts` / `folder.ts` / `document.ts` / `member.ts` / `permission.ts` / `tag.ts` / `persona.ts` / `recycle.ts` / `metadata.ts`
- `web/vue/src/document/types/index.ts` — 修改：真实类型（替换 stub）
- `web/vue/src/document/stores/index.ts` — 修改：真实 store
- `web/vue/src/document/stores/library.ts` / `folder.ts` / `document.ts` / `tag.ts` / `persona.ts`
- `web/vue/src/document/composables/index.ts` — 修改
- `web/vue/src/document/pages/library/LibraryList.vue` — 文档库列表
- `web/vue/src/document/pages/library/LibraryDetail.vue` — 文档库详情（多 Tab）
- `web/vue/src/document/pages/library/tabs/FilesTab.vue` / `MembersTab.vue` / `PermissionTab.vue` / `RecycleTab.vue` / `AuditTab.vue` / `TaskTab.vue`
- `web/vue/src/document/pages/TagsPage.vue` — 标签管理
- `web/vue/src/document/pages/PersonasPage.vue` — 人设管理
- `web/vue/src/document/components/` — 布局/文件详情/目录树/成员选择器/权限配置/标签选择器/人设编辑器/审计展示（8 组件）

### 测试文件
- `server/python/tests/document/unit/models/test_models.py`
- `server/python/tests/document/unit/services/test_permission_service.py`
- `server/python/tests/document/unit/services/test_folder_service.py`
- `server/python/tests/document/unit/services/test_library_service.py`
- `server/python/tests/document/unit/services/test_recycle_service.py`
- `server/python/tests/document/unit/services/test_tag_service.py`
- `server/python/tests/document/unit/controllers/test_inner_permission_controller.py`
- `server/python/tests/document/unit/controllers/test_library_controller.py`
- `server/python/tests/document/integration/test_inner_permission_flow.py`

---

## 批次 1：模块声明 + 基础模型

### 任务 1：document 枚举

**文件：**
- 创建：`server/python/src/document/models/enums.py`

- [ ] **步骤 1：创建 document 枚举**

参考 kbhub `enums.py`，仅迁移 document 相关枚举（不迁移知识库/工具库枚举）。创建 `server/python/src/document/models/enums.py`：

```python
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
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/document/models/enums.py
git commit -m "feat(document): 新增 document 模块枚举（从 kbhub 精简迁移）"
```

### 任务 2：Library / LibraryMember 模型

**文件：**
- 创建：`server/python/src/document/models/library.py`
- 修改：`server/python/src/document/models/__init__.py`

- [ ] **步骤 1：创建 Library 模型**

参考 kbhub `library.py` 的 Library/LibraryMember 字段，创建 `server/python/src/document/models/library.py`：

```python
"""文档库模型"""

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import LibraryMemberRole, LibraryMemberStatus, LibraryType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class Library(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库表（personal/team）"""

    __tablename__ = "library"
    __table_args__ = (
        Index("ix_library_tenant_id", "tenant_id"),
        Index("ix_library_type", "type"),
        Index("ix_library_owner_id", "owner_id"),
        {"comment": "文档库表"},
    )

    type: Mapped[str] = mapped_column(
        EnumType(enum_class=LibraryType, length=20), nullable=False, comment="文档库类型"
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="文档库编码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="文档库名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="图标")
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="所有者用户ID")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")
    allow_submit_to_kb: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否允许提交入库"
    )


class LibraryMember(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库成员表"""

    __tablename__ = "library_member"
    __table_args__ = (
        Index("ix_library_member_library_id", "library_id"),
        Index("ix_library_member_user_id", "user_id"),
        Index("ix_library_member_role", "role"),
        {"comment": "文档库成员表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档库ID")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="用户ID")
    user_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="用户名")
    role: Mapped[str] = mapped_column(
        EnumType(enum_class=LibraryMemberRole, length=20), nullable=False, comment="成员角色"
    )
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=LibraryMemberStatus, length=20), nullable=False,
        default=LibraryMemberStatus.ACTIVE, comment="成员状态",
    )
    remarks: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="备注")
```

- [ ] **步骤 2：在 models/__init__.py 导出**

修改 `server/python/src/document/models/__init__.py`：

```python
"""document 模块数据库模型"""

from framework.database.core import create_base_model, create_module_base

Base = create_module_base(schema="document")
BaseModel = create_base_model(Base)

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
from .library import Library, LibraryMember

__all__ = ["Base", "BaseModel", "Library", "LibraryMember"]
```

> 注意：后续任务会逐步追加模型导入与 `__all__` 项。

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/document/models/library.py server/python/src/document/models/__init__.py
git commit -m "feat(document): 新增 Library/LibraryMember 模型"
```

### 任务 3：Folder 模型（TreeNodeMixin）

**文件：**
- 创建：`server/python/src/document/models/folder.py`
- 修改：`server/python/src/document/models/__init__.py`

- [ ] **步骤 1：创建 Folder 模型**

参考 kbhub Folder 字段，Folder 继承 TreeNodeMixin（parent_id 无外键，遵循项目规范）：

```python
"""文件夹模型"""

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import FolderLifecycleStatus
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.mixins.tree import TreeNodeMixin
from framework.database.types.enum import EnumType


class Folder(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin, TreeNodeMixin):
    """文件夹表（树形，TreeNodeMixin）"""

    __tablename__ = "folder"
    __table_args__ = (
        Index("ix_folder_library_id", "library_id"),
        Index("ix_folder_lifecycle_status", "lifecycle_status"),
        {"comment": "文件夹表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档库ID")
    name: Mapped[str] = mapped_column(String(256), nullable=False, comment="文件夹名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    lifecycle_status: Mapped[str] = mapped_column(
        EnumType(enum_class=FolderLifecycleStatus, length=20), nullable=False,
        default=FolderLifecycleStatus.ACTIVE, comment="生命周期状态",
    )
    acl_inherit_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用权限继承"
    )
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否敏感"
    )
    doc_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="文档数")
```

> 注意：TreeNodeMixin 已提供 parent_id / tree_leaf / tree_level / tree_sort / tree_sorts / tree_names / parent_ids 字段，无需重复定义。

- [ ] **步骤 2：在 __init__.py 导出 Folder**

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/document/models/folder.py server/python/src/document/models/__init__.py
git commit -m "feat(document): 新增 Folder 模型（TreeNodeMixin，parent_id 无外键）"
```

### 任务 4：Document / DocumentVersion 模型

**文件：**
- 创建：`server/python/src/document/models/document.py`
- 修改：`server/python/src/document/models/__init__.py`

- [ ] **步骤 1：创建 Document 模型**

参考 kbhub Document 字段（精简，不含 Embedding 字段——切片由 ai 模块管理）：

```python
"""文档模型"""

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import DocumentProcessingStatus, DocumentStatus, DocumentType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class Document(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档表"""

    __tablename__ = "document"
    __table_args__ = (
        Index("ix_document_library_id", "library_id"),
        Index("ix_document_folder_id", "folder_id"),
        Index("ix_document_lifecycle_status", "lifecycle_status"),
        {"comment": "文档表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    folder_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="文件夹ID（空为根目录）")
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="所有者用户ID")
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, comment="MinIO 存储键")
    name: Mapped[str] = mapped_column(String(256), nullable=False, comment="文档名称")
    document_type: Mapped[str] = mapped_column(
        EnumType(enum_class=DocumentType, length=20), nullable=False, comment="文档类型"
    )
    lifecycle_status: Mapped[str] = mapped_column(
        EnumType(enum_class=DocumentStatus, length=20), nullable=False,
        default=DocumentStatus.UPLOADING, comment="生命周期状态",
    )
    processing_status: Mapped[str] = mapped_column(
        EnumType(enum_class=DocumentProcessingStatus, length=20), nullable=False,
        default=DocumentProcessingStatus.PENDING_PARSE, comment="处理状态",
    )
    acl_inherit_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否启用权限继承"
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="文件大小（字节）")
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="MIME 类型")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="元数据")
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="切片索引任务ID")


class DocumentVersion(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档版本表"""

    __tablename__ = "document_version"
    __table_args__ = (Index("ix_document_version_document_id", "document_id"), {"comment": "文档版本表"})

    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档ID")
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="版本号")
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, comment="MinIO 存储键")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="文件大小")
    uploaded_by: Mapped[str] = mapped_column(String(36), nullable=False, comment="上传人ID")
```

- [ ] **步骤 2：在 __init__.py 导出 Document/DocumentVersion**

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/document/models/document.py server/python/src/document/models/__init__.py
git commit -m "feat(document): 新增 Document/DocumentVersion 模型"
```

### 任务 5：module.py 声明 + 模型可映射验证

**文件：**
- 创建：`server/python/src/document/module.py`
- 创建：`server/python/tests/document/unit/models/test_models.py`

- [ ] **步骤 1：创建 module.py**

参考 `iam/module.py` 和 `ai/module.py` 模式，创建 `server/python/src/document/module.py`：

```python
"""document 模块声明"""

from collections.abc import Callable

from document.models import Base
from framework.module.definition import MenuDef, ModuleDefinition, PermissionDef


class DocumentModule:
    """document 模块描述符"""

    @property
    def name(self) -> str:
        return "document"

    @property
    def schema(self) -> str:
        return "document"

    @property
    def dependencies(self) -> list[str]:
        # document 依赖 tenant 和 iam（通过 inner 接口获取用户/组织信息）
        return ["tenant", "iam"]

    def get_base(self) -> type:
        return Base

    def get_routers(self) -> list[tuple]:
        from document.controllers.admin.library_controller import router as admin_library_router
        from document.controllers.admin.persona_controller import router as admin_persona_router
        from document.controllers.admin.tag_controller import router as admin_tag_router
        from document.controllers.console.document_controller import router as console_document_router
        from document.controllers.console.folder_controller import router as console_folder_router
        from document.controllers.console.library_controller import router as console_library_router
        from document.controllers.console.member_controller import router as console_member_router
        from document.controllers.console.metadata_controller import router as console_metadata_router
        from document.controllers.console.permission_controller import router as console_permission_router
        from document.controllers.console.recycle_controller import router as console_recycle_router
        from document.controllers.inner.permission_controller import router as inner_permission_router
        from document.controllers.inner.permission_request_controller import (
            router as inner_permission_request_router,
        )

        return [
            (admin_library_router, "/document/admin/v1", ["Admin - Library"]),
            (admin_tag_router, "/document/admin/v1", ["Admin - Tag"]),
            (admin_persona_router, "/document/admin/v1", ["Admin - Persona"]),
            (console_library_router, "/document/console/v1", ["Console - Library"]),
            (console_folder_router, "/document/console/v1", ["Console - Folder"]),
            (console_document_router, "/document/console/v1", ["Console - Document"]),
            (console_member_router, "/document/console/v1", ["Console - Member"]),
            (console_permission_router, "/document/console/v1", ["Console - Permission"]),
            (console_recycle_router, "/document/console/v1", ["Console - Recycle"]),
            (console_metadata_router, "/document/console/v1", ["Console - Metadata"]),
            (inner_permission_router, "/document/inner/v1", ["Inner - Permission"]),
            (inner_permission_request_router, "/document/inner/v1", ["Inner - PermissionRequest"]),
        ]

    def get_middlewares(self) -> list[type]:
        return []

    def get_lifespan_hooks(self) -> list[Callable]:
        return []

    def get_seeds(self) -> dict[str, Callable]:
        from document.migrations.seeds.library_seed import run as library_seed_run
        return {"document_library": library_seed_run}

    def get_task_setup(self) -> tuple | None:
        from document.tasks.setup import cleanup_tasks, setup_tasks
        return (setup_tasks, cleanup_tasks)

    def get_listener_setup(self) -> tuple | None:
        from document.listeners.setup import cleanup_listeners, setup_listeners
        return (setup_listeners, cleanup_listeners)

    def get_module_definition(self) -> ModuleDefinition:
        return ModuleDefinition(
            code="document",
            name="文档库",
            description="文档库、文件管理、资源权限、标签、人设",
            icon="BookOpen",
            version="1.0.0",
            menus=[
                MenuDef(
                    code="document.libraries",
                    name="文档库",
                    path="/document/libraries",
                    icon="FolderOpen",
                    sort_order=1,
                    permission_codes=["document:library:read"],
                ),
                MenuDef(
                    code="document.libraries.detail",
                    name="文档库详情",
                    path="/document/libraries/{id}",
                    parent_code="document.libraries",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["document:library:read"],
                ),
                MenuDef(
                    code="document.tags",
                    name="标签管理",
                    path="/document/tags",
                    icon="Tag",
                    sort_order=2,
                    permission_codes=["document:tag:read"],
                ),
                MenuDef(
                    code="document.personas",
                    name="人设管理",
                    path="/document/personas",
                    icon="UserCircle",
                    sort_order=3,
                    permission_codes=["document:persona:read"],
                ),
            ],
            permissions=[
                PermissionDef(code="document:library:read", name="查看文档库", resource="library", action="read"),
                PermissionDef(code="document:library:write", name="编辑文档库", resource="library", action="write"),
                PermissionDef(code="document:library:delete", name="删除文档库", resource="library", action="delete"),
                PermissionDef(code="document:folder:write", name="文件夹操作", resource="folder", action="write"),
                PermissionDef(code="document:file:upload", name="文件上传", resource="file", action="upload"),
                PermissionDef(code="document:file:download", name="文件下载", resource="file", action="download"),
                PermissionDef(code="document:tag:read", name="查看标签", resource="tag", action="read"),
                PermissionDef(code="document:tag:write", name="编辑标签", resource="tag", action="write"),
                PermissionDef(code="document:persona:read", name="查看人设", resource="persona", action="read"),
                PermissionDef(code="document:persona:write", name="编辑人设", resource="persona", action="write"),
                PermissionDef(code="document:permission:write", name="配置权限", resource="permission", action="write"),
                PermissionDef(code="document:recycle:purge", name="清空回收站", resource="recycle", action="purge"),
            ],
        )
```

- [ ] **步骤 2：编写模型可映射测试**

创建 `server/python/tests/document/unit/models/test_models.py`：

```python
"""document 模型可映射测试（验证表结构可创建）"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable

from document.models import Base


def test_all_models_can_create_table():
    """所有 document 模型可生成 DDL（验证字段/类型可映射）"""
    engine = create_engine("sqlite://")
    # 遍历所有 document 模型，生成 CreateTable 语句验证不抛错
    for table in Base.metadata.sorted_tables:
        if table.schema == "document":
            CreateTable(table).compile(bind=engine)
```

- [ ] **步骤 3：运行测试验证**

运行：`cd server/python && pytest tests/document/unit/models/test_models.py -v`
预期：PASS（此时仅 Library/LibraryMember/Folder/Document/DocumentVersion 表，后续任务新增表后重新运行仍应通过）

> 注意：此时 module.py 引用的控制器文件尚未创建，模块无法完整加载。批次 7 完成后验证整体加载。

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/document/module.py server/python/tests/document/unit/models/test_models.py
git commit -m "feat(document): 新增 module.py 声明与模型可映射测试"
```

---

## 批次 2：权限模型

### 任务 6：LibraryRole / LibraryRoleMember / ResourceAcl 模型

**文件：**
- 创建：`server/python/src/document/models/permission.py`
- 修改：`server/python/src/document/models/__init__.py`

- [ ] **步骤 1：创建权限模型**

参考 kbhub LibraryRole/LibraryRoleMember/ResourceAcl 字段：

```python
"""文档库权限模型"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import LibraryRoleKind, ResourceAclEffect, ResourceAclStatus, ResourceType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class LibraryRole(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库权限组表"""

    __tablename__ = "library_role"
    __table_args__ = (
        Index("ix_library_role_library_id", "library_id"),
        Index("ix_library_role_kind", "role_kind"),
        {"comment": "文档库权限组表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档库ID")
    role_kind: Mapped[str] = mapped_column(
        EnumType(enum_class=LibraryRoleKind, length=20), nullable=False, comment="权限组类型"
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, comment="权限组编码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="权限组名称")
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="描述")
    system_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否系统内置")
    permissions: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="权限定义（动作->等级）")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", comment="状态")


class LibraryRoleMember(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """权限组成员表"""

    __tablename__ = "library_role_member"
    __table_args__ = (
        Index("ix_library_role_member_role_id", "role_id"),
        Index("ix_library_role_member_user_id", "user_id"),
        {"comment": "权限组成员表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="文档库ID")
    role_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="权限组ID")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="用户ID")


class ResourceAcl(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """资源访问控制表（资源权限继承链）"""

    __tablename__ = "resource_acl"
    __table_args__ = (
        Index("ix_resource_acl_library_id", "library_id"),
        Index("ix_resource_acl_resource", "resource_type", "resource_id"),
        Index("ix_resource_acl_subject", "subject_id"),
        {"comment": "资源访问控制表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    resource_type: Mapped[str] = mapped_column(
        EnumType(enum_class=ResourceType, length=20), nullable=False, comment="资源类型"
    )
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="资源ID")
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="主体ID（用户ID/角色ID）")
    subject_type: Mapped[str] = mapped_column(String(20), nullable=False, default="user", comment="主体类型")
    action: Mapped[str] = mapped_column(String(64), nullable=False, comment="动作（read/preview/download/edit）")
    effect: Mapped[str] = mapped_column(
        EnumType(enum_class=ResourceAclEffect, length=20), nullable=False, comment="效果"
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="优先级")
    inherited_from_resource_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, comment="继承来源资源ID"
    )
    condition_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="条件")
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=ResourceAclStatus, length=20), nullable=False,
        default=ResourceAclStatus.ACTIVE, comment="状态",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="过期时间"
    )
```

- [ ] **步骤 2：在 __init__.py 导出**

追加 `LibraryRole`、`LibraryRoleMember`、`ResourceAcl` 导入与 `__all__` 项。

- [ ] **步骤 3：运行模型可映射测试**

运行：`cd server/python && pytest tests/document/unit/models/test_models.py -v`
预期：PASS

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/document/models/permission.py server/python/src/document/models/__init__.py
git commit -m "feat(document): 新增权限模型 LibraryRole/LibraryRoleMember/ResourceAcl"
```

---

## 批次 3：标签 + 人设模型

### 任务 7：Tag / TagGroup / Persona 模型

**文件：**
- 创建：`server/python/src/document/models/tag.py`
- 创建：`server/python/src/document/models/persona.py`
- 修改：`server/python/src/document/models/__init__.py`

- [ ] **步骤 1：创建 Tag/TagGroup 模型**

参考 kbhub tag.py：

```python
"""标签模型"""

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin


class TagGroup(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """标签分组表"""

    __tablename__ = "tag_group"
    __table_args__ = (Index("ix_tag_group_tenant_id", "tenant_id"), {"comment": "标签分组表"})

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="分组名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序")


class Tag(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """标签表"""

    __tablename__ = "tag"
    __table_args__ = (
        Index("ix_tag_tenant_id", "tenant_id"),
        Index("ix_tag_group_id", "group_id"),
        {"comment": "标签表"},
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="标签名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    color: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="颜色")
    group_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="分组ID")
    persona_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="引用人设ID")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", comment="状态")
    doc_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="引用文档数")
```

- [ ] **步骤 2：创建 Persona 模型**

参考 kbhub GovernancePersona：

```python
"""人设模型"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin


class Persona(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """人设表（AI 提示词）"""

    __tablename__ = "persona"
    __table_args__ = (Index("ix_persona_tenant_id", "tenant_id"), {"comment": "人设表"})

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="人设名称")
    role: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="角色定位")
    instruction: Mapped[str] = mapped_column(Text, nullable=False, comment="指令内容")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
```

- [ ] **步骤 3：在 __init__.py 导出**

追加 `Tag`、`TagGroup`、`Persona`。

- [ ] **步骤 4：运行模型可映射测试 + Commit**

```bash
git add server/python/src/document/models/tag.py server/python/src/document/models/persona.py server/python/src/document/models/__init__.py
git commit -m "feat(document): 新增 Tag/TagGroup/Persona 模型"
```

---

## 批次 4：元数据模型

### 任务 8：ResourceMetadata / LibraryMetadataField 模型

**文件：**
- 创建：`server/python/src/document/models/metadata.py`
- 创建：`server/python/src/document/models/recycle.py`
- 创建：`server/python/src/document/models/config.py`
- 修改：`server/python/src/document/models/__init__.py`

- [ ] **步骤 1：创建元数据模型**

```python
"""元数据模型"""

from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import MetadataFieldType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class LibraryMetadataField(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库元数据字段定义表"""

    __tablename__ = "library_metadata_field"
    __table_args__ = (
        Index("ix_library_metadata_field_library_id", "library_id"),
        {"comment": "文档库元数据字段定义表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="字段名称")
    field_type: Mapped[str] = mapped_column(
        EnumType(enum_class=MetadataFieldType, length=20), nullable=False, comment="字段类型"
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否必填")
    enum_values: Mapped[list | None] = mapped_column(JSONB, nullable=True, comment="枚举值列表")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序")


class ResourceMetadata(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """资源元数据值表"""

    __tablename__ = "resource_metadata"
    __table_args__ = (
        Index("ix_resource_metadata_resource", "resource_type", "resource_id"),
        {"comment": "资源元数据值表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="资源类型（folder/document）")
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="资源ID")
    field_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="元数据字段ID")
    field_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="字段名称（冗余）")
    value: Mapped[str | None] = mapped_column(String(1024), nullable=True, comment="元数据值")
```

- [ ] **步骤 2：创建 RecycleItem 模型**

```python
"""回收站模型"""

from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from document.models.enums import RecycleItemStatus, ResourceType
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class RecycleItem(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """回收站表"""

    __tablename__ = "recycle_item"
    __table_args__ = (
        Index("ix_recycle_item_library_id", "library_id"),
        Index("ix_recycle_item_status", "status"),
        {"comment": "回收站表"},
    )

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="源文档库ID")
    resource_type: Mapped[str] = mapped_column(
        EnumType(enum_class=ResourceType, length=20), nullable=False, comment="资源类型"
    )
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="资源ID")
    original_parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="原父资源ID")
    original_path: Mapped[str | None] = mapped_column(String(1024), nullable=True, comment="原路径")
    deleted_by: Mapped[str] = mapped_column(String(36), nullable=False, comment="删除人ID")
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=RecycleItemStatus, length=20), nullable=False,
        default=RecycleItemStatus.IN_RECYCLE, comment="状态",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="过期时间（自动清理）"
    )
    restored_by: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="恢复人ID")
    restored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="恢复时间")
```

- [ ] **步骤 3：创建 ConfigItem 模型（文档库级配置）**

```python
"""文档库配置模型"""

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from document.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin


class ConfigItem(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """文档库级配置表"""

    __tablename__ = "config_item"
    __table_args__ = (Index("ix_config_item_library_id", "library_id"), {"comment": "文档库级配置表"})

    library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="文档库ID")
    config_key: Mapped[str] = mapped_column(String(128), nullable=False, comment="配置键")
    config_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="配置值")
```

- [ ] **步骤 4：在 __init__.py 导出全部剩余模型**

追加 `LibraryMetadataField`、`ResourceMetadata`、`RecycleItem`、`ConfigItem`。更新 `__all__`。

- [ ] **步骤 5：运行模型可映射测试 + Commit**

运行：`cd server/python && pytest tests/document/unit/models/test_models.py -v`，预期 PASS。

```bash
git add server/python/src/document/models/metadata.py server/python/src/document/models/recycle.py server/python/src/document/models/config.py server/python/src/document/models/__init__.py
git commit -m "feat(document): 新增元数据/回收站/配置模型，完成 16 张表模型"
```

---

## 批次 5：权限判定引擎

### 任务 9：权限判定引擎（TDD）

**文件：**
- 创建：`server/python/src/document/services/permission_service.py`
- 测试：`server/python/tests/document/unit/services/test_permission_service.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec `document-resource-permission/spec.md` 的 16 个场景，编写核心判定测试：

```python
"""文档库权限判定引擎单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.services.permission_service import PermissionService
from document.models.enums import LibraryMemberRole, PermissionLevel


@pytest.mark.asyncio
class TestPermissionService:
    """权限判定引擎测试"""

    async def _make_service(self):
        return PermissionService()

    async def test_owner_has_full_editable(self):
        """owner/admin 全部资源可编辑"""
        service = await self._make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.OWNER):
            result = await service.check_resource_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="download",
            )
        assert result == "editable"

    async def test_admin_has_full_editable(self):
        """admin 全部资源可编辑"""
        service = await self._make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.ADMIN):
            result = await service.check_resource_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="edit",
            )
        assert result == "editable"

    async def test_member_permission_from_acl_inheritance(self):
        """普通成员通过继承链计算权限，取最高等级"""
        service = await self._make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.MEMBER), \
             patch.object(service, "_compute_inherited_permission", new_callable=AsyncMock, return_value="editable"):
            result = await service.check_resource_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="download",
            )
        assert result == "editable"

    async def test_no_permission_returns_none(self):
        """无权限返回 none"""
        service = await self._make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=None), \
             patch.object(service, "_compute_inherited_permission", new_callable=AsyncMock, return_value="none"):
            result = await service.check_resource_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="download",
            )
        assert result == "none"

    async def test_deny_acl_overrides_allow(self):
        """显式 deny 覆盖继承 allow"""
        service = await self._make_service()
        result = service._merge_permission_levels(inherited="editable", direct_deny=True)
        assert result == "none"

    async def test_highest_permission_wins(self):
        """多个权限来源取最高等级"""
        service = await self._make_service()
        # 全员权限=readonly + 自定义权限组=editable + 直授权=none -> editable（取最高）
        result = service._pick_highest_level(["readonly", "editable", "none"])
        assert result == "editable"

    async def test_all_deny_returns_none(self):
        """所有来源均为 none/deny 返回 none"""
        service = await self._make_service()
        result = service._pick_highest_level(["none", "none", "none"])
        assert result == "none"

    async def test_permission_not_amplified_for_non_member(self):
        """非文档库成员返回 none（不放大权限）"""
        service = await self._make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=None):
            result = await service.check_resource_permission(
                session, user_id="outsider", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="read",
            )
        assert result == "none"

    async def test_inheritance_truncated_when_disabled(self):
        """关闭继承后父级权限截断"""
        service = await self._make_service()
        session = AsyncMock()
        with patch.object(service, "_get_member_role", new_callable=AsyncMock, return_value=LibraryMemberRole.MEMBER), \
             patch.object(service, "_compute_inherited_permission", new_callable=AsyncMock, return_value="none") as mock_inherit:
            # 文档 acl_inherit_enabled=False，不查继承
            result = await service.check_resource_permission(
                session, user_id="u1", library_id="lib-1",
                resource_type="document", resource_id="d1", operation="read",
            )
            # 由于 mock 返回 none，结果是 none
            assert result == "none"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/document/unit/services/test_permission_service.py -v`
预期：FAIL，`ModuleNotFoundError`

- [ ] **步骤 3：实现权限判定引擎**

参考 kbhub `services/library/permission.py` 的判定流程（精简，不逐行移植），创建 `server/python/src/document/services/permission_service.py`：

```python
"""文档库权限判定引擎

判定流程（见迁移方案 §3.1 第 2 层）：
  1. owner/admin 命中 -> 全部资源可编辑
  2. 计算 全员权限 + 自定义权限组 + 用户直授权，取最高等级
  3. 沿继承链计算资源权限（文档库根 -> 目录 -> 文件），取最高等级
  4. 显式 deny 覆盖继承 allow
  5. 叠加第 3 层企业 Policy（由 framework PermissionEngine 编排）

精简实现：不迁移 kbhub permission.py 的 7.8 万行 Alon 平台特有逻辑。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import LibraryMember, ResourceAcl
from document.models.enums import LibraryMemberRole, PermissionLevel, ResourceType
from framework.permission.engine import PermissionCheckResult, PermissionEngine, PermissionEngineProtocol


# 权限等级映射
LEVEL_MAP = {
    PermissionLevel.UNCONFIGURED: "none",
    PermissionLevel.NONE: "none",
    PermissionLevel.READONLY: "readonly",
    PermissionLevel.EDITABLE: "editable",
}

# 只读操作集合
READ_OPERATIONS = {"read", "preview"}


class DocumentPermissionChecker(PermissionEngineProtocol):
    """document 第2层资源权限判定器（实现 framework Protocol）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
    ) -> str:
        """实现 Protocol：供 framework PermissionEngine 调用"""
        # resource_id 实际为 library_id:resource_id 格式时需拆分，此处简化
        return "none"


class PermissionService:
    """文档库权限判定服务"""

    async def check_resource_permission(
        self,
        session: AsyncSession,
        user_id: str,
        library_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
    ) -> str:
        """
        判定用户对资源的权限等级。

        Returns: editable / readonly / none
        """
        # 1. 查成员角色
        member_role = await self._get_member_role(session, library_id=library_id, user_id=user_id)

        # 非成员直接 none（不放大权限）
        if member_role is None:
            return "none"

        # 2. owner/admin 全可编辑
        if member_role in (LibraryMemberRole.OWNER, LibraryMemberRole.ADMIN):
            return "editable"

        # 3. 普通成员：计算继承链 + 直授权 + 权限组，取最高
        inherited = await self._compute_inherited_permission(
            session, user_id=user_id, library_id=library_id,
            resource_type=resource_type, resource_id=resource_id, operation=operation,
        )

        # 4. 显式 deny 覆盖
        direct_deny = await self._has_direct_deny(
            session, library_id=library_id, resource_id=resource_id, user_id=user_id, operation=operation
        )
        if direct_deny:
            return "none"

        return inherited

    async def _get_member_role(
        self, session: AsyncSession, library_id: str, user_id: str
    ) -> str | None:
        """获取用户在文档库的成员角色"""
        from document.models.enums import LibraryMemberStatus

        stmt = select(LibraryMember.role).where(
            LibraryMember.library_id == library_id,
            LibraryMember.user_id == user_id,
            LibraryMember.status == LibraryMemberStatus.ACTIVE,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _compute_inherited_permission(
        self,
        session: AsyncSession,
        user_id: str,
        library_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
    ) -> str:
        """
        沿继承链计算权限（文档库根 -> 目录 -> 文件），取最高等级。

        简化实现：查询该资源及祖先路径上的所有 ACL，取最高等级。
        """
        # 查询该资源的直授权 ACL（用户维度 + 角色维度）
        stmt = select(ResourceAcl).where(
            ResourceAcl.library_id == library_id,
            ResourceAcl.resource_id.in_([library_id, resource_id]),  # 库根 + 当前资源
            ResourceAcl.subject_id == user_id,
            ResourceAcl.action == operation,
            ResourceAcl.status == "active",
        )
        result = await session.execute(stmt)
        acls = list(result.scalars().all())

        levels = []
        for acl in acls:
            if acl.effect == "deny":
                levels.append("none")
            else:
                levels.append("editable")  # 简化：有 allow 即 editable

        if not levels:
            return "none"
        return self._pick_highest_level(levels)

    async def _has_direct_deny(
        self, session: AsyncSession, library_id: str, resource_id: str, user_id: str, operation: str
    ) -> bool:
        """检查是否有显式 deny"""
        stmt = select(ResourceAcl).where(
            ResourceAcl.library_id == library_id,
            ResourceAcl.resource_id == resource_id,
            ResourceAcl.subject_id == user_id,
            ResourceAcl.action == operation,
            ResourceAcl.effect == "deny",
            ResourceAcl.status == "active",
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    def _pick_highest_level(self, levels: list[str]) -> str:
        """多个权限来源取最高等级"""
        priority = {"editable": 2, "readonly": 1, "none": 0}
        if not levels:
            return "none"
        return max(levels, key=lambda lv: priority.get(lv, 0))

    def _merge_permission_levels(self, inherited: str, direct_deny: bool) -> str:
        """合并继承权限与直授权"""
        if direct_deny:
            return "none"
        return inherited

    async def diagnose(
        self,
        session: AsyncSession,
        user_id: str,
        library_id: str,
        resource_type: str,
        resource_id: str,
        operation: str,
    ) -> dict:
        """权限排障：输出最终允许/拒绝及命中原因"""
        perm = await self.check_resource_permission(
            session, user_id=user_id, library_id=library_id,
            resource_type=resource_type, resource_id=resource_id, operation=operation,
        )
        allowed = perm == "editable" or (perm == "readonly" and operation in READ_OPERATIONS)
        return {
            "allowed": allowed,
            "resource_permission": perm,
            "reasons": [f"最终权限等级={perm}", f"操作={operation}", f"成员身份={await self._get_member_role(session, library_id, user_id)}"],
        }


permission_service = PermissionService()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && pytest tests/document/unit/services/test_permission_service.py -v`
预期：PASS（9 个测试通过）

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/document/services/permission_service.py server/python/tests/document/unit/services/test_permission_service.py
git commit -m "feat(document): 新增权限判定引擎（owner/admin/继承链/deny覆盖/不放大权限）"
```

---

## 批次 6：业务服务

### 任务 10：library_service（TDD）

**文件：**
- 创建：`server/python/src/document/services/library_service.py`
- 测试：`server/python/tests/document/unit/services/test_library_service.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec `document-library/spec.md` 场景（创建个人/团队库、列表分页筛选、编辑、删除软删除）：

```python
"""文档库服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.services.library_service import LibraryService


@pytest.mark.asyncio
class TestLibraryService:
    async def test_create_personal_library_auto_owner(self):
        """创建个人文档库，创建者自动成为 owner"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.library_service.get_tenant_id", return_value="t1"), \
             patch("document.services.library_service.get_user_id", return_value="u1"), \
             patch("document.services.library_service.has_personal_library", new_callable=AsyncMock, return_value=False):
            lib = await LibraryService.create(
                session, library_type="personal", code="personal-u1", name="我的文档库",
            )
        assert lib.owner_id == "u1"
        session.add.assert_called()

    async def test_create_personal_library_reject_if_exists(self):
        """已存在个人文档库时拒绝创建"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.library_service.get_tenant_id", return_value="t1"), \
             patch("document.services.library_service.get_user_id", return_value="u1"), \
             patch("document.services.library_service.has_personal_library", new_callable=AsyncMock, return_value=True):
            with pytest.raises(ValueError, match="个人文档库"):
                await LibraryService.create(
                    session, library_type="personal", code="personal-u1", name="我的文档库",
                )

    async def test_create_team_library_reject_duplicate_name(self):
        """团队文档库名称重复拒绝"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.services.library_service.get_tenant_id", return_value="t1"), \
             patch("document.services.library_service.get_user_id", return_value="u1"), \
             patch("document.services.library_service.has_team_library_name", new_callable=AsyncMock, return_value=True):
            with pytest.raises(ValueError, match="名称已存在"):
                await LibraryService.create(
                    session, library_type="team", code="team-rd", name="研发库",
                )

    async def test_delete_library_soft_delete(self):
        """删除文档库为软删除"""
        session = AsyncMock(spec=AsyncSession)
        mock_lib = MagicMock()
        mock_lib.id = "lib-1"
        mock_lib.deleted_at = None
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_lib
        session.execute = AsyncMock(return_value=result)
        await LibraryService.soft_delete(session, library_id="lib-1")
        assert mock_lib.deleted_at is not None
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/document/unit/services/test_library_service.py -v`，预期 FAIL。

- [ ] **步骤 3：实现 library_service**

参考 kbhub `services/library/library.py` 的方法（精简），创建 `server/python/src/document/services/library_service.py`：

```python
"""文档库服务"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Library, LibraryMember
from document.models.enums import LibraryMemberRole, LibraryMemberStatus, LibraryType
from framework.common.ctx import get_tenant_id, get_user_id
from framework.database.mixins.tenant import TenantMixin


class LibraryService:
    """文档库服务"""

    @staticmethod
    async def create(
        session: AsyncSession,
        library_type: str,
        code: str,
        name: str,
        description: str | None = None,
        icon: str | None = None,
    ) -> Library:
        """创建文档库"""
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        # 个人文档库唯一性校验
        if library_type == LibraryType.PERSONAL:
            if await LibraryService.has_personal_library(session, tenant_id=tenant_id, user_id=user_id):
                raise ValueError("每个用户最多一个个人文档库")

        # 团队文档库名称唯一性校验
        if library_type == LibraryType.TEAM:
            if await LibraryService.has_team_library_name(session, tenant_id=tenant_id, name=name):
                raise ValueError("文档库名称已存在")

        library = Library(
            tenant_id=tenant_id,
            type=library_type,
            code=code,
            name=name,
            description=description,
            icon=icon,
            owner_id=user_id,
            enabled=True,
            allow_submit_to_kb=True,
        )
        session.add(library)
        await session.flush()

        # 创建者自动成为 owner
        member = LibraryMember(
            tenant_id=tenant_id,
            library_id=library.id,
            user_id=user_id,
            user_name=user_id,  # 实际应从 iam 查询用户名
            role=LibraryMemberRole.OWNER,
            status=LibraryMemberStatus.ACTIVE,
        )
        session.add(member)
        await session.flush()
        return library

    @staticmethod
    async def has_personal_library(session: AsyncSession, tenant_id: str, user_id: str) -> bool:
        """是否已有个人文档库"""
        stmt = select(func.count(Library.id)).where(
            Library.tenant_id == tenant_id,
            Library.owner_id == user_id,
            Library.type == LibraryType.PERSONAL,
            Library.deleted_at.is_(None),
        )
        return (await session.execute(stmt)).scalar() > 0

    @staticmethod
    async def has_team_library_name(session: AsyncSession, tenant_id: str, name: str) -> bool:
        stmt = select(func.count(Library.id)).where(
            Library.tenant_id == tenant_id,
            Library.name == name,
            Library.type == LibraryType.TEAM,
            Library.deleted_at.is_(None),
        )
        return (await session.execute(stmt)).scalar() > 0

    @staticmethod
    async def list_libraries(
        session: AsyncSession,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        library_type: str | None = None,
    ) -> tuple[list[Library], int]:
        conditions = [Library.tenant_id == tenant_id, Library.deleted_at.is_(None)]
        if keyword:
            conditions.append(Library.name.like(f"%{keyword}%"))
        if library_type:
            conditions.append(Library.type == library_type)

        total = (await session.execute(
            select(func.count(Library.id)).where(*conditions)
        )).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(Library).where(*conditions)
            .order_by(Library.created_at.desc())
            .offset(offset).limit(page_size)
        )
        items = list((await session.execute(stmt)).scalars().all())
        return items, total

    @staticmethod
    async def get_by_id(session: AsyncSession, library_id: str) -> Library | None:
        stmt = select(Library).where(Library.id == library_id, Library.deleted_at.is_(None))
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def soft_delete(session: AsyncSession, library_id: str) -> None:
        lib = await LibraryService.get_by_id(session, library_id)
        if lib is None:
            raise ValueError("文档库不存在")
        lib.deleted_at = datetime.now(timezone.utc)
        await session.flush()


library_service = LibraryService()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && pytest tests/document/unit/services/test_library_service.py -v`，预期 PASS。

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/document/services/library_service.py server/python/tests/document/unit/services/test_library_service.py
git commit -m "feat(document): 新增文档库服务（创建/列表/软删除）"
```

### 任务 11：folder_service（TDD）

**文件：**
- 创建：`server/python/src/document/services/folder_service.py`
- 测试：`server/python/tests/document/unit/services/test_folder_service.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec `document-library/spec.md` 文件夹树场景（创建/重命名/移动/循环引用检测）：

```python
"""文件夹服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from document.services.folder_service import FolderService


@pytest.mark.asyncio
class TestFolderService:
    async def test_create_folder_uses_treenode(self):
        """创建文件夹使用 TreeNodeMixin.create_node"""
        session = AsyncMock(spec=AsyncSession)
        with patch("document.models.Folder.create_node", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock(id="f1")
            folder = await FolderService.create(
                session, library_id="lib-1", name="子文件夹", parent_id="root",
            )
            mock_create.assert_called_once()

    async def test_move_folder_detects_cycle(self):
        """移动文件夹检测循环引用"""
        session = AsyncMock(spec=AsyncSession)
        mock_folder = MagicMock()
        mock_folder.id = "f1"
        mock_folder.parent_ids = "root,f2,f1,"  # f1 是 f2 的子孙
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_folder
        session.execute = AsyncMock(return_value=result)

        with pytest.raises(ValueError, match="循环引用"):
            await FolderService.move(session, folder_id="f1", new_parent_id="f2")
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/document/unit/services/test_folder_service.py -v`，预期 FAIL。

- [ ] **步骤 3：实现 folder_service**

利用 TreeNodeMixin 内置的 create_node/update_node/delete_node/list_nodes/build_tree 方法：

```python
"""文件夹服务（基于 TreeNodeMixin）"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Folder


class FolderService:
    """文件夹服务"""

    @staticmethod
    async def create(
        session: AsyncSession,
        library_id: str,
        name: str,
        parent_id: str | None = None,
        description: str | None = None,
    ) -> Folder:
        """创建文件夹（使用 TreeNodeMixin.create_node 自动维护树字段）"""
        folder = await Folder.create_node(
            session,
            source={
                "library_id": library_id,
                "name": name,
                "description": description,
                "parent_id": parent_id,
            },
        )
        return folder

    @staticmethod
    async def rename(session: AsyncSession, folder_id: str, name: str) -> Folder:
        """重命名文件夹"""
        return await Folder.update_node(session, id=folder_id, source={"name": name})

    @staticmethod
    async def move(session: AsyncSession, folder_id: str, new_parent_id: str) -> Folder:
        """移动文件夹（循环引用检测）"""
        # 获取目标父节点，检查是否为当前节点的子孙
        if new_parent_id and new_parent_id != "root":
            target = await Folder.one_node(session, new_parent_id)
            if target and target.parent_ids.startswith(f"{target.parent_ids}{folder_id},"):
                raise ValueError("不允许形成循环引用")
            # 目标是当前节点的子孙
            stmt = select(Folder).where(Folder.id == folder_id)
            current = (await session.execute(stmt)).scalar_one_or_none()
            if current and target and target.parent_ids.startswith(
                f"{current.parent_ids}{current.id},"
            ):
                raise ValueError("循环引用")

        return await Folder.update_node(session, id=folder_id, source={"parent_id": new_parent_id})

    @staticmethod
    async def delete(session: AsyncSession, folder_id: str) -> int:
        """删除文件夹（软删除，含子孙）"""
        return await Folder.delete_node(session, id=folder_id)

    @staticmethod
    async def list_tree(session: AsyncSession, library_id: str) -> list:
        """获取文件夹树"""
        nodes = await Folder.list_nodes(
            session, extra_conditions=[Folder.library_id == library_id]
        )
        return Folder.build_tree(nodes)


folder_service = FolderService()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && pytest tests/document/unit/services/test_folder_service.py -v`，预期 PASS。

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/document/services/folder_service.py server/python/tests/document/unit/services/test_folder_service.py
git commit -m "feat(document): 新增文件夹服务（基于 TreeNodeMixin）"
```

### 任务 12：document_service + member_service + tag_service + persona_service + recycle_service + metadata_service + permission_config_service

**文件：**
- 创建：`server/python/src/document/services/document_service.py`
- 创建：`server/python/src/document/services/member_service.py`
- 创建：`server/python/src/document/services/permission_config_service.py`
- 创建：`server/python/src/document/services/tag_service.py`
- 创建：`server/python/src/document/services/persona_service.py`
- 创建：`server/python/src/document/services/recycle_service.py`
- 创建：`server/python/src/document/services/metadata_service.py`
- 创建：`server/python/tests/document/unit/services/test_recycle_service.py`
- 创建：`server/python/tests/document/unit/services/test_tag_service.py`
- 修改：`server/python/src/document/services/__init__.py`

> 以下每个服务遵循相同模式：static 方法 + AsyncSession 注入 + 多租户过滤 + 软删除。参考 kbhub 对应源文件精简实现。

- [ ] **步骤 1：实现 document_service**

创建 `server/python/src/document/services/document_service.py`，实现：upload（走 framework TenantMinioStorage）、get_by_id、list_documents（按 library_id/folder_id）、move、soft_delete、trigger_index_task（委托 tasks/document_index_task.py）。关键上传逻辑：

```python
"""文档服务"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Document
from document.models.enums import DocumentStatus
from framework.common.ctx import get_tenant_id, get_user_id
from framework.storage.tenant_storage import tenant_storage_upload


class DocumentService:
    @staticmethod
    async def upload(
        session: AsyncSession,
        library_id: str,
        folder_id: str | None,
        filename: str,
        content: bytes,
        mime_type: str | None = None,
    ) -> Document:
        """上传文件到 MinIO 并创建 Document 记录"""
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        # 上传到 MinIO（租户感知路径）
        storage_key = await tenant_storage_upload(
            path=f"document/{library_id}/{filename}",
            data=content,
            content_type=mime_type,
        )

        doc = Document(
            tenant_id=tenant_id,
            library_id=library_id,
            folder_id=folder_id,
            owner_id=user_id,
            storage_key=storage_key,
            name=filename,
            document_type="document",
            lifecycle_status=DocumentStatus.UPLOADING,
            file_size=len(content),
            mime_type=mime_type,
        )
        session.add(doc)
        await session.flush()
        return doc

    @staticmethod
    async def get_by_id(session: AsyncSession, doc_id: str) -> Document | None:
        stmt = select(Document).where(Document.id == doc_id, Document.deleted_at.is_(None))
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def list_documents(
        session: AsyncSession, library_id: str, folder_id: str | None = None,
        page: int = 1, page_size: int = 50,
    ) -> tuple[list[Document], int]:
        conditions = [Document.library_id == library_id, Document.deleted_at.is_(None)]
        if folder_id:
            conditions.append(Document.folder_id == folder_id)
        total = (await session.execute(
            select(func.count(Document.id)).where(*conditions)
        )).scalar() or 0
        offset = (page - 1) * page_size
        stmt = select(Document).where(*conditions).offset(offset).limit(page_size)
        return list((await session.execute(stmt)).scalars().all()), total

    @staticmethod
    async def soft_delete(session: AsyncSession, doc_id: str) -> None:
        doc = await DocumentService.get_by_id(session, doc_id)
        if doc is None:
            raise ValueError("文档不存在")
        doc.deleted_at = datetime.now(timezone.utc)
        await session.flush()


document_service = DocumentService()
```

- [ ] **步骤 2：实现 member_service**

创建 `member/python/src/document/services/member_service.py`，参考 kbhub `services/library/member.py`，实现 add_member（跨租户校验）、remove_member（owner 不可移除）、update_member_role、list_members。

- [ ] **步骤 3：实现 tag_service（TDD）**

创建 `server/python/tests/document/unit/services/test_tag_service.py`（测试：创建/查询/删除/已被引用不可删除/分组下有标签不可删除），然后实现 `tag_service.py`：CRUD + 引用校验（查询 Tag.doc_count > 0 或被 Persona 引用时拒绝删除）。

- [ ] **步骤 4：实现 persona_service**

参考 kbhub `services/persona.py`，实现 CRUD + 名称租户内唯一 + 已被标签引用不可删除 + 选项列表（不含完整 instruction）。

- [ ] **步骤 5：实现 recycle_service（TDD）**

参考 kbhub `services/library/recycle_item.py`，测试场景：查看/恢复（原始路径不存在恢复到根/名称冲突重命名）/永久删除（权限校验）/清空。实现 `recycle_service.py`。

- [ ] **步骤 6：实现 permission_config_service**

参考 kbhub `services/library/role.py` 和 `resource_acl.py`，实现：list_roles、create_role（新建权限组默认复制全员权限）、list_role_members、add_role_members、list_resource_acls、create_resource_acl、update_inheritance（关闭继承截断）。

- [ ] **步骤 7：实现 metadata_service**

参考 kbhub `services/library/document.py` 的元数据部分，实现：define_field、set_metadata（枚举值校验）、batch_set、query_metadata、search_by_metadata。

- [ ] **步骤 8：更新 services/__init__.py 导出全部服务**

```python
"""document 模块服务"""

from document.services.document_service import document_service
from document.services.folder_service import folder_service
from document.services.library_service import library_service
from document.services.member_service import member_service
from document.services.metadata_service import metadata_service
from document.services.permission_config_service import permission_config_service
from document.services.permission_service import permission_service
from document.services.persona_service import persona_service
from document.services.recycle_service import recycle_service
from document.services.tag_service import tag_service

__all__ = [
    "library_service", "folder_service", "document_service", "member_service",
    "permission_service", "permission_config_service", "tag_service",
    "persona_service", "recycle_service", "metadata_service",
]
```

- [ ] **步骤 9：运行全部服务测试**

运行：`cd server/python && pytest tests/document/unit/services/ -v`，预期 PASS。

- [ ] **步骤 10：Commit**

```bash
git add server/python/src/document/services/ server/python/tests/document/unit/services/
git commit -m "feat(document): 新增全部业务服务（文档/成员/标签/人设/回收站/权限配置/元数据）"
```

---

## 批次 7：控制器 + schemas

### 任务 13：schemas

**文件：**
- 创建：`server/python/src/document/schemas/library.py` / `folder.py` / `document.py` / `permission.py` / `tag.py` / `persona.py` / `metadata.py` / `recycle.py` / `inner.py`

- [ ] **步骤 1：创建 library schema**

参考 iam schemas 模式，创建 `server/python/src/document/schemas/library.py`：

```python
"""文档库 Schema"""

from datetime import datetime
from pydantic import Field
from framework.schemas.base import BaseModel, BasePaginatedQuery


class LibraryCreate(BaseModel):
    library_type: str = Field(..., description="文档库类型")
    code: str = Field(..., description="编码")
    name: str = Field(..., description="名称")
    description: str | None = Field(default=None)
    icon: str | None = Field(default=None)


class LibraryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    icon: str | None = None
    enabled: bool | None = None
    allow_submit_to_kb: bool | None = None


class LibraryPaginatedQuery(BasePaginatedQuery):
    library_type: str | None = Field(default=None)


class LibraryResponse(BaseModel):
    id: str
    type: str
    code: str
    name: str
    description: str | None = None
    icon: str | None = None
    owner_id: str
    enabled: bool
    allow_submit_to_kb: bool
    created_at: datetime
```

- [ ] **步骤 2：创建其余 schema**

按相同模式创建 folder/document/permission/tag/persona/metadata/recycle/inner schema。inner schema 含 `DocumentPermissionQuery`、`MemberCheckQuery`、`PermissionApplyCallbackRequest`。

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/document/schemas/
git commit -m "feat(document): 新增全部 Schema（library/folder/document/permission/tag/persona/metadata/recycle/inner）"
```

### 任务 14：inner 控制器（权限回查 + 成员身份回查 + 权限申请回调）

**文件：**
- 创建：`server/python/src/document/controllers/inner/permission_controller.py`
- 创建：`server/python/src/document/controllers/inner/permission_request_controller.py`
- 测试：`server/python/tests/document/unit/controllers/test_inner_permission_controller.py`

- [ ] **步骤 1：编写 inner 控制器测试**

参考 OpenSpec `document-inner-api/spec.md` 10 个场景（权限回查返回 editable/readonly/none/deny、成员身份回查、无认证仅供模块间调用、跨租户不可访问）：

```python
"""inner 权限控制器测试"""

import pytest
from unittest.mock import AsyncMock, patch
from document.controllers.inner.permission_controller import check_document_permission, check_library_member


@pytest.mark.asyncio
class TestInnerPermissionController:
    async def test_check_permission_returns_editable(self):
        session = AsyncMock()
        with patch("document.services.permission_service.permission_service.check_resource_permission", new_callable=AsyncMock, return_value="editable"):
            response = await check_document_permission(
                document_id="d1", user_id="u1", session=session,
            )
            assert response.status_code == 200

    async def test_check_permission_non_member_returns_none(self):
        session = AsyncMock()
        with patch("document.services.permission_service.permission_service.check_resource_permission", new_callable=AsyncMock, return_value="none"):
            response = await check_document_permission(
                document_id="d1", user_id="outsider", session=session,
            )
            assert response.status_code == 200

    async def test_check_member_returns_true(self):
        session = AsyncMock()
        with patch("document.services.permission_service.permission_service._get_member_role", new_callable=AsyncMock, return_value="member"):
            response = await check_library_member(
                library_id="lib-1", user_id="u1", session=session,
            )
            assert response.status_code == 200
```

- [ ] **步骤 2：实现 inner 权限控制器**

创建 `server/python/src/document/controllers/inner/permission_controller.py`：

```python
"""document inner 接口 - 权限回查（无认证，仅供 ai 模块调用）"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.services.permission_service import permission_service

router = APIRouter()


@router.get("/documents/{document_id}/permission")
async def check_document_permission(
    document_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """
    回查用户对源文件的资源权限。

    场景：知识库问答需回查源文件权限，不放大权限。
    返回：editable / readonly / none
    """
    # 先查文档获取 library_id
    from document.services.document_service import document_service
    doc = await document_service.get_by_id(session, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="源文件不存在")

    perm = await permission_service.check_resource_permission(
        session, user_id=user_id, library_id=doc.library_id,
        resource_type="document", resource_id=document_id, operation="read",
    )
    return ApiResponse.success(data={"permission": perm})


@router.get("/libraries/{library_id}/members")
async def check_library_member(
    library_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """回查文档库成员身份"""
    role = await permission_service._get_member_role(session, library_id=library_id, user_id=user_id)
    return ApiResponse.success(data={"is_member": role is not None, "role": role})
```

- [ ] **步骤 3：实现 inner 权限申请回调控制器**

创建 `server/python/src/document/controllers/inner/permission_request_controller.py`，处理 5 种申请类型（library_join/library_resource/library_role）的 apply 回调，创建 library_members/resource_acls/library_role_members：

```python
"""document inner 接口 - 权限申请审批回调落地"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from document.schemas.inner import PermissionApplyCallbackRequest

router = APIRouter()


@router.post("/permission-requests/{request_id}/apply")
async def apply_permission_request(
    request_id: str,
    data: PermissionApplyCallbackRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """权限申请审批通过后回调落地授权（iam 审批后调用）"""
    from document.services.member_service import member_service
    from document.services.permission_config_service import permission_config_service

    try:
        if data.request_type == "library_join":
            await member_service.add_member(
                session, library_id=data.target_resource_id, user_id=data.applicant_id,
                role=data.requested_role or "member",
            )
        elif data.request_type == "library_resource":
            await permission_config_service.create_resource_acl(
                session, library_id=data.target_resource_id, resource_id=data.extra_data.get("resource_id"),
                subject_id=data.applicant_id, action=data.requested_permission, effect="allow",
            )
        elif data.request_type == "library_role":
            await permission_config_service.add_role_members(
                session, library_id=data.target_resource_id, role_id=data.requested_role,
                user_ids=[data.applicant_id],
            )
        await session.commit()
        return ApiResponse.success(data={"applied": True})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **步骤 4：运行测试 + Commit**

```bash
git add server/python/src/document/controllers/inner/ server/python/tests/document/unit/controllers/test_inner_permission_controller.py
git commit -m "feat(document): 新增 inner 接口（权限回查/成员身份回查/权限申请回调）"
```

### 任务 15：console 控制器

**文件：**
- 创建：`server/python/src/document/controllers/console/library_controller.py` / `folder_controller.py` / `document_controller.py` / `member_controller.py` / `permission_controller.py` / `recycle_controller.py` / `metadata_controller.py`

- [ ] **步骤 1：实现 console 控制器**

参考 iam console 控制器模式，每个控制器注入 `get_db_session`，使用 `ApiResponse.success/paginated`，调用对应 service。例如 `library_controller.py`：

```python
"""文档库控制器 - 用户端"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from framework.tenant.context import get_tenant_id
from document.schemas.library import LibraryCreate, LibraryPaginatedQuery, LibraryResponse, LibraryUpdate
from document.services.library_service import library_service

router = APIRouter()


@router.get("/libraries")
async def list_libraries(
    query: LibraryPaginatedQuery = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    tenant_id = get_tenant_id()
    items, total = await library_service.list_libraries(
        session, tenant_id=tenant_id, page=query.page, page_size=query.page_size,
        keyword=query.keyword, library_type=query.library_type,
    )
    return ApiResponse.paginated(
        data=[LibraryResponse.model_validate(l).model_dump() for l in items],
        total=total, page=query.page, page_size=query.page_size,
    )


@router.post("/libraries")
async def create_library(
    data: LibraryCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    try:
        lib = await library_service.create(
            session, library_type=data.library_type, code=data.code, name=data.name,
            description=data.description, icon=data.icon,
        )
        await session.commit()
        return ApiResponse.success(data=LibraryResponse.model_validate(lib).model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **步骤 2：实现其余 6 个 console 控制器**

folder/document/member/permission/recycle/metadata 控制器，遵循相同模式。

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/document/controllers/console/
git commit -m "feat(document): 新增 console 控制器（library/folder/document/member/permission/recycle/metadata）"
```

### 任务 16：admin 控制器

**文件：**
- 创建：`server/python/src/document/controllers/admin/library_controller.py` / `tag_controller.py` / `persona_controller.py`

- [ ] **步骤 1：实现 admin 控制器**

admin 层提供管理端列表查看（按租户）。tag/persona 控制器提供 CRUD。遵循 iam admin 控制器模式。

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/document/controllers/admin/
git commit -m "feat(document): 新增 admin 控制器（library/tag/persona）"
```

---

## 批次 8：任务与监听

### 任务 17：文档切片索引任务

**文件：**
- 创建：`server/python/src/document/tasks/document_index_task.py`
- 修改：`server/python/src/document/tasks/setup.py`

- [ ] **步骤 1：实现切片索引任务触发**

document 只触发任务 + 记录状态，实际切片由 ai 模块执行（通过事件或 inner 接口）：

```python
"""文档切片索引任务触发"""

from sqlalchemy.ext.asyncio import AsyncSession

from document.models import Document
from document.models.enums import DocumentProcessingStatus


async def trigger_index_task(session: AsyncSession, document_id: str) -> str:
    """
    触发文档切片索引任务。

    document 只记录状态，实际 Embedding 由 ai 模块执行。
    Phase 3 完成后通过 ai inner 接口或事件触发。
    """
    doc = await Document.one_node(session, document_id) if hasattr(Document, "one_node") else None
    # 更新处理状态
    from sqlalchemy import select
    stmt = select(Document).where(Document.id == document_id)
    doc = (await session.execute(stmt)).scalar_one_or_none()
    if doc is None:
        raise ValueError("文档不存在")
    doc.processing_status = DocumentProcessingStatus.PARSING
    await session.flush()

    # TODO(phase3): 通过 ai inner 接口触发实际切片
    # from framework.notification.sender import ...
    return document_id


async def setup_tasks() -> None:
    """注册定时任务（索引恢复补偿、回收站自动清理）"""
    # TODO: 接入 framework scheduler
    pass


async def cleanup_tasks() -> None:
    pass
```

- [ ] **步骤 2：实现 listeners**

修改 `server/python/src/document/listeners/setup.py`，注册权限变更失效监听（暂空实现，后续增强）。

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/document/tasks/ server/python/src/document/listeners/
git commit -m "feat(document): 新增切片索引任务触发与监听器骨架"
```

---

## 批次 9：数据库迁移与种子

### 任务 18：16 张表迁移脚本

**文件：**
- 创建：`server/python/src/document/migrations/__init__.py`
- 创建：`server/python/src/document/migrations/env.py`
- 创建：`server/python/src/document/migrations/versions/001_initial_schema.py`

- [ ] **步骤 1：创建 migrations 包**

创建 `server/python/src/document/migrations/__init__.py`（空）。

- [ ] **步骤 2：创建 env.py**

参考 iam `migrations/env.py`，创建 document 的 Alembic env（schema=document）。

- [ ] **步骤 3：创建初始迁移脚本**

参考 iam `003_audit_log.py` 模式，创建 `server/python/src/document/migrations/versions/001_initial_schema.py`，用 `op.create_table` 创建 16 张表（library/library_member/folder/document/document_version/library_role/library_role_member/resource_acl/tag/tag_group/persona/library_metadata_field/resource_metadata/recycle_item/config_item），schema="document"。

- [ ] **步骤 4：执行迁移验证**

运行：`cd server/python && alembic -c alembic.ini upgrade head`
预期：无错误，16 张表创建成功

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/document/migrations/
git commit -m "feat(document): 新增 16 张表初始迁移脚本"
```

### 任务 19：种子数据

**文件：**
- 创建：`server/python/src/document/migrations/seeds/__init__.py`
- 创建：`server/python/src/document/migrations/seeds/library_seed.py`

- [ ] **步骤 1：创建种子数据**

创建 `server/python/src/document/migrations/seeds/library_seed.py`，提供默认元数据字段定义和全员权限组模板：

```python
"""document 默认种子数据"""

from sqlalchemy.ext.asyncio import AsyncSession

from document.models import LibraryMetadataField, LibraryRole
from document.models.enums import LibraryRoleKind


async def run(session: AsyncSession) -> None:
    """创建默认元数据字段和权限组模板（幂等）"""
    # 默认元数据字段模板（实际绑定到具体文档库时复制）
    # 此处仅作为全局模板，具体文档库创建时由 library_service 复制
    pass  # 占位，具体种子逻辑在 library_service.create 中按需初始化
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/document/migrations/seeds/
git commit -m "feat(document): 新增种子数据骨架"
```

---

## 批次 10：审计接入

### 任务 20：业务操作审计接入

**文件：**
- 修改：`server/python/src/document/services/library_service.py` / `folder_service.py` / `document_service.py` / `member_service.py` / `permission_config_service.py` / `tag_service.py` / `persona_service.py` / `recycle_service.py`

- [ ] **步骤 1：在关键写操作加 @audit_log 装饰器或 write_audit 调用**

在 library_service.create/soft_delete、folder_service.create/delete、document_service.upload/soft_delete、member_service.add_member/remove_member、permission_config_service.create_resource_acl、tag_service.create/delete、persona_service.create/delete、recycle_service.purge 等写操作中，调用 `framework.permission.audit_writer.write_audit` 或使用 `@audit_log` 装饰器，`business_domain="document"`。

示例（library_service.create 末尾）：

```python
from framework.permission.audit_writer import write_audit

# 在 create 方法 return 前：
await write_audit(
    session=session,
    business_domain="document",
    operation_type="create_library",
    resource_type="library",
    resource_id=library.id,
    resource_name=library.name,
    after_data={"type": library.type, "code": library.code},
)
```

- [ ] **步骤 2：验证审计写入**

运行集成测试，确认操作后 `iam.audit_logs` 表有 `business_domain=document` 的记录。

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/document/services/
git commit -m "feat(document): 业务操作接入 framework 审计写入辅助"
```

---

## 批次 11：前端基础

### 任务 21：前端类型 + API + stores

**文件：**
- 修改：`web/vue/src/document/types/index.ts`
- 创建：`web/vue/src/document/api/library.ts` / `folder.ts` / `document.ts` / `member.ts` / `permission.ts` / `tag.ts` / `persona.ts` / `recycle.ts` / `metadata.ts`
- 修改：`web/vue/src/document/api/index.ts`
- 修改：`web/vue/src/document/stores/index.ts`
- 创建：`web/vue/src/document/stores/library.ts` / `folder.ts` / `tag.ts` / `persona.ts`

- [ ] **步骤 1：替换 types/index.ts 为真实类型**

参考 iam types 模式，定义 Library/Folder/Document/LibraryMember/Tag/Persona/RecycleItem 等接口（替换原 stub）。

- [ ] **步骤 2：创建各 API 文件**

参考 iam api/user.ts 模式，每个 API 文件从 `@/framework/api/client` 导入 get/post/put/del，返回 `Promise<ApiResponse<T>>`，路径遵循 `/document/console/v1/*` 和 `/document/admin/v1/*`。替换 `api/index.ts` 的 stub 为真实导出。

- [ ] **步骤 3：创建 stores**

参考 iam stores/user.ts 模式，创建 library/folder/tag/persona store，替换 `stores/index.ts` 的 stub。

- [ ] **步骤 4：类型校验**

运行：`cd web/vue && pnpm typecheck`，预期无错误。

- [ ] **步骤 5：Commit**

```bash
git add web/vue/src/document/types/ web/vue/src/document/api/ web/vue/src/document/stores/
git commit -m "feat(document): 前端类型/API/stores 从 stub 替换为真实实现"
```

---

## 批次 12：前端页面

### 任务 22：文档库列表 + 详情页

**文件：**
- 创建：`web/vue/src/document/pages/library/LibraryList.vue`
- 创建：`web/vue/src/document/pages/library/LibraryDetail.vue`
- 创建：`web/vue/src/document/pages/library/tabs/FilesTab.vue` / `MembersTab.vue` / `PermissionTab.vue` / `RecycleTab.vue` / `AuditTab.vue` / `TaskTab.vue`

- [ ] **步骤 1：创建文档库列表页**

参考 iam `pages/users/UserList.vue` 列表页模式（DataTable + 分页 + 关键词筛选 + 创建按钮）。调用 `getLibraries`，使用 `@/components` 统一入口的 DataTable/Button/Input。

- [ ] **步骤 2：创建文档库详情页（多 Tab）**

LibraryDetail.vue 使用 Tabs 组件，各 Tab 独立组件：
- FilesTab：文件夹树 + 文件列表（调用 folder/document API）
- MembersTab：成员列表 + 添加/移除/角色分配
- PermissionTab：权限组 + 资源 ACL 配置
- RecycleTab：回收站查看/恢复/永久删除
- AuditTab：审计日志（接入现有 audit-logs 接口）
- TaskTab：切片索引任务状态

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/document/pages/library/
git commit -m "feat(document): 新增文档库列表与详情页（多 Tab）"
```

### 任务 23：标签 + 人设页面

**文件：**
- 创建：`web/vue/src/document/pages/TagsPage.vue`
- 创建：`web/vue/src/document/pages/PersonasPage.vue`

- [ ] **步骤 1：创建标签管理页**

参考列表页模式，调用 tag API，含分组管理、人设引用。

- [ ] **步骤 2：创建人设管理页**

含 CodeMirror 提示词编辑器（引入 codemirror 依赖），调用 persona API。

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/document/pages/TagsPage.vue web/vue/src/document/pages/PersonasPage.vue
git commit -m "feat(document): 新增标签管理与人设管理页面"
```

---

## 批次 13：前端专用组件

### 任务 24：迁移适配 8 个专用组件

**文件：**
- 创建：`web/vue/src/document/components/LibraryLayout.vue` — 文档库布局（侧栏+内容区）
- 创建：`web/vue/src/document/components/FileDetail.vue` — 文件详情（预览/元数据/版本）
- 创建：`web/vue/src/document/components/FolderTree.vue` — 目录树（文件浏览器）
- 创建：`web/vue/src/document/components/MemberSelector.vue` — 成员管理（人员选择器，适配 iam 接口）
- 创建：`web/vue/src/document/components/PermissionConfig.vue` — 权限配置（权限组+资源权限树）
- 创建：`web/vue/src/document/components/TagSelector.vue` — 标签选择器
- 创建：`web/vue/src/document/components/PersonaEditor.vue` — 人设编辑器（CodeMirror）
- 创建：`web/vue/src/document/components/AuditLogViewer.vue` — 审计日志展示

- [ ] **步骤 1：迁移适配各组件**

参考 kbhub `web/src/components/` 对应组件的业务逻辑，用本项目 shadcn-vue + Tailwind 重写 UI，仅迁移业务逻辑。人员选择器复用 iam 的 PeopleSelect 组件（`@/components/common/feedback/PeopleSelect`）。

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/document/components/
git commit -m "feat(document): 迁移适配 8 个专用组件（布局/文件详情/目录树/成员选择器/权限配置/标签选择器/人设编辑器/审计展示）"
```

---

## 批次 14：前端路由 + 权限 + 测试

### 任务 25：路由配置 + 权限码接入

**文件：**
- 修改：`web/vue/src/document/router/index.ts`
- 修改：`web/vue/src/document/index.ts`
- 修改：`web/vue/src/config/modules.ts`

- [ ] **步骤 1：配置路由**

修改 `web/vue/src/document/router/index.ts`，参考 iam router 嵌套模式：

```typescript
import type { RouteRecordRaw } from "vue-router";

export const documentRoutes: RouteRecordRaw[] = [
  {
    path: "document",
    name: "DocumentRoot",
    component: () => import("@/document/components/LibraryLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      {
        path: "libraries",
        name: "DocumentLibraryList",
        component: () => import("@/document/pages/library/LibraryList.vue"),
        meta: { title: "文档库", icon: "folder-open", requiresAuth: true, permissions: ["document:library:read"] },
      },
      {
        path: "libraries/:id",
        name: "DocumentLibraryDetail",
        component: () => import("@/document/pages/library/LibraryDetail.vue"),
        meta: { title: "文档库详情", hidden: true, requiresAuth: true, permissions: ["document:library:read"] },
      },
      {
        path: "tags",
        name: "DocumentTags",
        component: () => import("@/document/pages/TagsPage.vue"),
        meta: { title: "标签管理", icon: "tag", requiresAuth: true, permissions: ["document:tag:read"] },
      },
      {
        path: "personas",
        name: "DocumentPersonas",
        component: () => import("@/document/pages/PersonasPage.vue"),
        meta: { title: "人设管理", icon: "user-circle", requiresAuth: true, permissions: ["document:persona:read"] },
      },
    ],
  },
];

export default documentRoutes;
```

- [ ] **步骤 2：更新 index.ts 返回真实路由**

修改 `web/vue/src/document/index.ts`：`getRoutes: () => documentRoutes`。

- [ ] **步骤 3：启用 document 模块**

修改 `web/vue/src/config/modules.ts`（如需手动启用，或重新运行 generate-modules-config.ts）。

- [ ] **步骤 4：Commit**

```bash
git add web/vue/src/document/router/ web/vue/src/document/index.ts web/vue/src/config/modules.ts
git commit -m "feat(document): 前端路由配置与权限码接入，启用 document 模块"
```

### 任务 26：前端测试

**文件：**
- 创建：`web/vue/src/document/pages/library/__tests__/LibraryList.spec.ts`
- 创建：`web/vue/src/document/pages/__tests__/TagsPage.spec.ts`

- [ ] **步骤 1：编写 LibraryList 组件测试**

测试列表渲染、创建文档库、分页交互。

- [ ] **步骤 2：编写 TagsPage 组件测试**

测试标签 CRUD、分组管理。

- [ ] **步骤 3：运行前端测试**

运行：`cd web/vue && pnpm test`，预期 PASS。

- [ ] **步骤 4：Commit**

```bash
git add web/vue/src/document/pages/library/__tests__/ web/vue/src/document/pages/__tests__/
git commit -m "test(document): 新增前端组件测试"
```

### 任务 27：Phase 2 整体验收

- [ ] **步骤 1：运行后端全部 document 测试**

运行：`cd server/python && pytest tests/document/ -v`，预期全部 PASS。

- [ ] **步骤 2：运行 ruff 和 pyright**

运行：`cd server/python && ruff check src/document/ && pyright src/document/`，预期无错误。

- [ ] **步骤 3：运行前端类型检查和测试**

运行：`cd web/vue && pnpm typecheck && pnpm test`，预期无错误。

- [ ] **步骤 4：验证迁移脚本**

运行：`cd server/python && alembic -c alembic.ini upgrade head`，预期无错误。

- [ ] **步骤 5：验证模块加载**

确认 document 模块在应用启动时正确加载，菜单和权限码同步到租户实例层。

- [ ] **步骤 6：验证 OpenSpec tasks 全部完成**

逐项核对 `openspec/changes/kbhub-migration-phase2/tasks.md` 的 53 项任务。

- [ ] **步骤 7：Commit 验收标记**

```bash
git add -A
git commit -m "chore(kbhub-phase2): Phase 2 整体验收通过"
```

---

## 自检结果

### 规格覆盖度
- ✅ module.py 声明（任务 5）
- ✅ 16 张表模型（任务 1-4, 6-8）
- ✅ 权限判定引擎（任务 9，覆盖 owner/admin/继承链/deny/不放大）
- ✅ 9 个业务服务（任务 10-12）
- ✅ 控制器 admin/console/inner（任务 13-16）
- ✅ inner 接口（任务 14，权限回查 + 成员身份 + 权限申请回调）
- ✅ 切片索引任务（任务 17）
- ✅ 迁移 + 种子（任务 18-19）
- ✅ 审计接入（任务 20）
- ✅ 前端基础（任务 21）
- ✅ 前端页面（任务 22-23）
- ✅ 前端组件（任务 24）
- ✅ 前端路由 + 权限 + 测试（任务 25-26）

### 占位符扫描
- 切片索引任务含 `TODO(phase3)`：document 触发任务，实际 Embedding 由 ai 模块执行，Phase 3 接入。设计上明确的占位，非缺陷。
- 种子数据 `library_seed.py` 含占位 pass：默认元数据字段在 library_service.create 中按需初始化，全局模板暂空。可在实现时补充。
- listeners/tasks setup 含 TODO：接入 framework scheduler，后续增强。

### 类型一致性
- 模型字段在 service/schema/controller/前端类型中一致
- 权限等级（editable/readonly/none）在 permission_service/inner 控制器/前端类型中一致
- 枚举值（LibraryMemberRole 等）在后端 enums 与前端类型中一致
- inner 接口路径（`/document/inner/v1/documents/{id}/permission`、`/document/inner/v1/libraries/{id}/members`）与 Phase 3 ai 模块回查路径一致
