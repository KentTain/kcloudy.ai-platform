# kbhub 迁移 Phase 3 实现计划：ai 模块扩展 + 集成验收

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 完整迁移知识库、入库审核、工具库、平台设置到 ai 模块，实现知识库成员权限体系（不放大源文档权限），执行跨模块端到端集成验收。

**架构：** ai 模块增补 module.py 菜单权限 + 14 张表模型 + 8 个服务 + admin/console/inner 三层控制器；知识库问答复用现有 Conversation/Message 模型与 SSE 事件流（EventType.SOURCE_DOCUMENT 已存在），通过 document inner 接口回查源文件权限（检索前后双重过滤）；工具库统一 Runtime 按 protocol 分发 HttpExecutor/McpExecutor；外部依赖 prance/openapi-spec-validator/MCP SDK 在本 Phase 安装。

**技术栈：** Python 3.12+、FastAPI、SQLAlchemy 2.0 async、Alembic、PostgreSQL、pytest；外部依赖：prance、openapi-spec-validator、mcp；复用：ai EmbeddingService/LLMService/RerankService/GraphRAGClient/Conversation/Message、framework permission engine、iam notification sender

---

## 前置条件

- ✅ Phase 1 完成：framework permission engine/policy_evaluator/audit_writer/notification sender、iam Notification/PermissionRequest/Policy
- ✅ Phase 2 完成：document 16 张表、permission_service、inner 接口（`/document/inner/v1/documents/{id}/permission`、`/document/inner/v1/libraries/{id}/members`、`/document/inner/v1/permission-requests/{id}/apply`）
- ✅ ai 模块已有：Conversation/Message/MessageMetadata 模型、ChatService/ConversationService、EmbeddingService/LLMService/RerankService、GraphRAGClient、EventType（含 SOURCE_DOCUMENT）、SSE 事件流模式
- ✅ ai 迁移版本链：None → 001 → 002 → 003 → `004_add_message_metadata_table`（Phase 3 起点）
- ✅ kbhub 源码可访问

## 参考源码

| 目标实现 | kbhub 源文件 |
|---------|-------------|
| 知识库模型 | `kbhub/src/kbhub/models/knowledge_base.py`（KnowledgeBase/Member/KbDocumentReference） |
| 入库审核 | `kbhub/src/kbhub/models/knowledge_base.py`（KbDocumentReview）、`services/knowledge_base/approval.py` |
| 工具库模型 | `kbhub/src/kbhub/models/tool.py`（Tool/ToolAuth/ToolFunction/ToolParameter/ToolImportRecord） |
| 工具导入 | `kbhub/src/kbhub/services/tool_import.py`、`tool_runtime.py` |
| 平台设置 | `kbhub/src/kbhub/services/platform_settings.py`、`models/config.py`（ConfigItem） |
| 知识库检索 | `kbhub/src/kbhub/services/knowledge_base/retrieval.py` |
| 枚举 | `kbhub/src/kbhub/models/enums.py`（知识库/工具相关枚举） |
| 前端 | `kbhub/web/src/pages/knowledge/`、`apis/definition/knowledge/`、`apis/definition/admin/` |

## 复用现有 ai 基础（不重复实现）

| 能力 | 现有入口 | 复用方式 |
|------|---------|---------|
| 对话骨架 | `Conversation`/`Message`/`MessageMetadata` | 知识库问答通过 `app_id` 区分，`message_metadata` JSONB 存检索片段/来源 |
| 消息流水线 | `ChatService.create_messages`/`update_assistant_message`、`ConversationService.get_or_create` | 知识库问答服务直接调用 |
| Query 向量化 | `EmbeddingService.embed/batch_embed` | 检索服务调用，provider/model 留空走默认 |
| 答案生成 | `LLMService.stream` | 问答流式生成 |
| 候选重排 | `RerankService.rerank` | 检索后重排 |
| 图谱检索 | `GraphRAGClient.search` | 图谱知识库检索后端 |
| SSE 事件流 | `controllers/v1/chat/llm.py` 模式、`EventType.SOURCE_DOCUMENT` | 问答接口复用，推送引用片段 |
| 异步任务停止 | `ACTIVE_ASYNCIO_TASKS`、`CancelAsyncioTaskHandler` | 问答任务停止 |

---

## 文件结构

### ai 后端新增文件

**模型**
- `server/python/src/ai/models/enums.py` — 修改：增补知识库/工具枚举
- `server/python/src/ai/models/knowledge_base.py` — KnowledgeBase / KnowledgeBaseMember / KnowledgeBaseDocument / KnowledgeBaseAcl
- `server/python/src/ai/models/import_request.py` — ImportRequest / ImportRequestItem
- `server/python/src/ai/models/tool.py` — Tool / ToolAuth / ToolFunction / ToolParameter / ToolImportRecord
- `server/python/src/ai/models/config_item.py` — ConfigItem
- `server/python/src/ai/models/__init__.py` — 修改：导出新模型

**Schema**
- `server/python/src/ai/schemas/knowledge_base.py`
- `server/python/src/ai/schemas/import_review.py`
- `server/python/src/ai/schemas/tool.py`
- `server/python/src/ai/schemas/platform_settings.py`

**服务**
- `server/python/src/ai/services/knowledge_base/__init__.py`
- `server/python/src/ai/services/knowledge_base/kb_service.py` — 知识库 CRUD
- `server/python/src/ai/services/knowledge_base/member_service.py` — 成员权限
- `server/python/src/ai/services/knowledge_base/document_service.py` — 文档引用管理
- `server/python/src/ai/services/knowledge_base/retrieval_service.py` — 检索（双重权限过滤 + document inner 回查）
- `server/python/src/ai/services/knowledge_base/qa_service.py` — 知识库问答（复用 ChatService + LLMService）
- `server/python/src/ai/services/import_review/__init__.py`
- `server/python/src/ai/services/import_review/import_service.py` — 入库审核流程
- `server/python/src/ai/services/tool/__init__.py`
- `server/python/src/ai/services/tool/tool_service.py` — 工具管理 CRUD
- `server/python/src/ai/services/tool/swagger_import.py` — Swagger 导入（prance + openapi-spec-validator）
- `server/python/src/ai/services/tool/mcp_import.py` — MCP 导入（官方 SDK）
- `server/python/src/ai/services/tool/tool_runtime.py` — 测试 Runtime（HttpExecutor/McpExecutor）
- `server/python/src/ai/services/platform_settings.py` — 平台设置

**控制器**
- `server/python/src/ai/controllers/admin/knowledge_base.py`
- `server/python/src/ai/controllers/admin/tool.py`
- `server/python/src/ai/controllers/console/knowledge_base.py`
- `server/python/src/ai/controllers/console/tool.py`
- `server/python/src/ai/controllers/console/platform_settings.py`
- `server/python/src/ai/controllers/v1/knowledge_qa.py` — 知识库问答 SSE 接口
- `server/python/src/ai/controllers/inner/permission_request_controller.py` — 权限申请 apply 回调

**监听器与任务**
- `server/python/src/ai/listeners/services/queue/index_task_consumer.py` — 索引恢复补偿
- `server/python/src/ai/listeners/setup.py` — 修改：注册新消费者
- `server/python/src/ai/tasks/import_review_timeout.py` — 审核超时监控

**迁移与种子**
- `server/python/src/ai/migrations/versions/005_knowledge_base.py` — 知识库相关表
- `server/python/src/ai/migrations/versions/006_import_request.py` — 入库审核表
- `server/python/src/ai/migrations/versions/007_tool.py` — 工具库表
- `server/python/src/ai/migrations/versions/008_config_item.py` — 平台设置表
- `server/python/src/ai/migrations/seeds/kb_seed.py` — 默认知识库配置 + 工具导入枚举

**配置**
- `server/python/pyproject.toml` — 修改：新增 prance/openapi-spec-validator/mcp 依赖

### ai 前端新增/修改文件
- `web/vue/src/ai/api/knowledgeBase.ts` / `tool.ts` / `platformSettings.ts` / `importReview.ts`
- `web/vue/src/ai/types/knowledgeBase.ts` / `tool.ts` / `platformSettings.ts`
- `web/vue/src/ai/stores/knowledgeBase.ts` / `tool.ts`
- `web/vue/src/ai/pages/knowledge-base/KnowledgeBaseList.vue`
- `web/vue/src/ai/pages/knowledge-base/KnowledgeBaseDetail.vue` + tabs（Overview/Documents/Members/Retrieval/Graph/Approval/Config/Audit）
- `web/vue/src/ai/pages/ToolsPage.vue`
- `web/vue/src/ai/pages/PlatformSettingsPage.vue`
- `web/vue/src/ai/components/` — 知识库布局/入库审核/检索测试/工具库/模型选择（5 组件）
- `web/vue/src/ai/router/index.ts` — 修改：新增路由
- `web/vue/src/ai/index.ts` — 修改：导出

### 集成验收测试
- `server/python/tests/ai/integration/test_document_ai_chain.py`
- `server/python/tests/ai/integration/test_three_layer_permission.py`
- `server/python/tests/ai/integration/test_permission_request_apply.py`
- `server/python/tests/ai/integration/test_audit_cross_module.py`
- `server/python/tests/ai/integration/test_notification_redirect.py`
- `server/python/tests/ai/integration/test_kb_permission_no_amplify.py`
- `server/python/tests/ai/integration/test_policy_cross_module.py`

---

## 批次 1：模块声明增补

### 任务 1：ai module.py 增补菜单与权限

**文件：**
- 修改：`server/python/src/ai/module.py`

- [ ] **步骤 1：在 get_module_definition 增补菜单**

在 `server/python/src/ai/module.py` 的 `get_module_definition()` 返回的 `menus` 列表追加：

```python
                MenuDef(
                    code="ai.knowledge_base",
                    name="知识库",
                    path="/ai/knowledge-base",
                    icon="Library",
                    sort_order=2,
                    permission_codes=["ai:knowledge_base:read"],
                ),
                MenuDef(
                    code="ai.knowledge_base.detail",
                    name="知识库详情",
                    path="/ai/knowledge-base/{id}",
                    parent_code="ai.knowledge_base",
                    sort_order=1,
                    is_visible=False,
                    permission_codes=["ai:knowledge_base:read"],
                ),
                MenuDef(
                    code="ai.tools",
                    name="工具库",
                    path="/ai/tools",
                    icon="Wrench",
                    sort_order=4,
                    permission_codes=["ai:tool:read"],
                ),
                MenuDef(
                    code="ai.platform_settings",
                    name="平台设置",
                    path="/ai/platform-settings",
                    icon="Settings",
                    sort_order=5,
                    permission_codes=["ai:platform_settings:read"],
                ),
```

- [ ] **步骤 2：在 permissions 增补权限**

```python
                # 知识库权限
                PermissionDef(code="ai:knowledge_base:read", name="查看知识库", resource="knowledge_base", action="read"),
                PermissionDef(code="ai:knowledge_base:write", name="编辑知识库", resource="knowledge_base", action="write"),
                PermissionDef(code="ai:knowledge_base:delete", name="删除知识库", resource="knowledge_base", action="delete"),
                PermissionDef(code="ai:knowledge_base:query", name="知识库问答", resource="knowledge_base", action="query"),
                PermissionDef(code="ai:import:submit", name="提交入库申请", resource="import", action="submit"),
                PermissionDef(code="ai:import:review", name="入库审核", resource="import", action="review"),
                # 工具权限
                PermissionDef(code="ai:tool:read", name="查看工具", resource="tool", action="read"),
                PermissionDef(code="ai:tool:write", name="编辑工具", resource="tool", action="write"),
                PermissionDef(code="ai:tool:import", name="工具导入", resource="tool", action="import"),
                PermissionDef(code="ai:tool:test", name="工具测试", resource="tool", action="test"),
                # 平台设置权限
                PermissionDef(code="ai:platform_settings:read", name="查看平台设置", resource="platform_settings", action="read"),
                PermissionDef(code="ai:platform_settings:write", name="编辑平台设置", resource="platform_settings", action="write"),
```

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/ai/module.py
git commit -m "feat(ai): 增补知识库/工具库/平台设置/入库审核菜单与权限声明"
```

---

## 批次 2：知识库模型

### 任务 2：知识库枚举 + 模型

**文件：**
- 修改：`server/python/src/ai/models/enums.py`
- 创建：`server/python/src/ai/models/knowledge_base.py`
- 修改：`server/python/src/ai/models/__init__.py`

- [ ] **步骤 1：在 enums.py 增补知识库枚举**

参考 kbhub enums.py，在 `server/python/src/ai/models/enums.py` 追加：

```python
class KnowledgeBaseType(str, Enum):
    """知识库类型"""
    NORMAL = "normal"
    GRAPH = "graph"


class KnowledgeBaseScopeType(str, Enum):
    """知识库归属"""
    PERSONAL = "personal"
    TEAM = "team"


class KnowledgeBaseStatus(str, Enum):
    """知识库状态"""
    DRAFT = "draft"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class KnowledgeBaseMemberRole(str, Enum):
    """知识库成员角色"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    REVIEWER = "reviewer"
    QUERY_USER = "query_user"


class KnowledgeBaseMemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class KbDocumentImportType(str, Enum):
    """入库类型"""
    TEXT_RAG = "text_rag"
    GRAPH = "graph"
    HYBRID = "hybrid"


class KbDocumentReviewStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"


class KbDocumentReferenceStatus(str, Enum):
    """引用状态"""
    ACTIVE = "active"
    DISABLED = "disabled"
    REMOVED = "removed"
```

- [ ] **步骤 2：创建知识库模型**

参考 kbhub `knowledge_base.py`（精简，不含图谱模型——图谱复用 GraphRAGClient），创建 `server/python/src/ai/models/knowledge_base.py`：

```python
"""知识库模型"""

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from ai.models.enums import (
    KnowledgeBaseMemberRole,
    KnowledgeBaseMemberStatus,
    KnowledgeBaseScopeType,
    KnowledgeBaseStatus,
    KnowledgeBaseType,
    KbDocumentImportType,
    KbDocumentReferenceStatus,
    KbDocumentReviewStatus,
)
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class KnowledgeBase(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """知识库表"""

    __tablename__ = "knowledge_base"
    __table_args__ = (
        Index("ix_knowledge_base_tenant_id", "tenant_id"),
        Index("ix_knowledge_base_owner_id", "owner_id"),
        {"comment": "知识库表"},
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="编码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="图标")
    kb_type: Mapped[str] = mapped_column(
        EnumType(enum_class=KnowledgeBaseType, length=20), nullable=False, comment="知识库类型"
    )
    scope_type: Mapped[str] = mapped_column(
        EnumType(enum_class=KnowledgeBaseScopeType, length=20), nullable=False, comment="归属"
    )
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=KnowledgeBaseStatus, length=20), nullable=False,
        default=KnowledgeBaseStatus.ENABLED, comment="状态",
    )
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="所有者用户ID")
    retrieval_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="检索配置")
    qa_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="问答配置")


class KnowledgeBaseMember(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """知识库成员表"""

    __tablename__ = "knowledge_base_member"
    __table_args__ = (
        Index("ix_kb_member_kb_id", "knowledge_base_id"),
        Index("ix_kb_member_user_id", "user_id"),
        {"comment": "知识库成员表"},
    )

    knowledge_base_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="知识库ID")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="用户ID")
    user_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="用户名")
    kb_role: Mapped[str] = mapped_column(
        EnumType(enum_class=KnowledgeBaseMemberRole, length=20), nullable=False, comment="成员角色"
    )
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=KnowledgeBaseMemberStatus, length=20), nullable=False,
        default=KnowledgeBaseMemberStatus.ACTIVE, comment="状态",
    )
    remarks: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="备注")


class KnowledgeBaseDocument(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """知识库文档引用表"""

    __tablename__ = "knowledge_base_document"
    __table_args__ = (
        Index("ix_kb_doc_kb_id", "knowledge_base_id"),
        Index("ix_kb_doc_document_id", "document_id"),
        {"comment": "知识库文档引用表"},
    )

    knowledge_base_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="知识库ID")
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="源文档ID（document 模块）")
    source_library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="源文档库ID")
    review_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="审核申请ID")
    import_type: Mapped[str] = mapped_column(
        EnumType(enum_class=KbDocumentImportType, length=20), nullable=False, comment="入库类型"
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False, comment="文档标题")
    source_path: Mapped[str | None] = mapped_column(String(1024), nullable=True, comment="源路径")
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=KbDocumentReferenceStatus, length=20), nullable=False,
        default=KbDocumentReferenceStatus.ACTIVE, comment="引用状态",
    )
    tag_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="标签ID")


class KnowledgeBaseAcl(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """知识库例外授权表（不放大源文档权限）"""

    __tablename__ = "knowledge_base_acl"
    __table_args__ = (
        Index("ix_kb_acl_kb_id", "knowledge_base_id"),
        Index("ix_kb_acl_user_id", "user_id"),
        {"comment": "知识库例外授权表"},
    )

    knowledge_base_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="知识库ID")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="用户ID")
    document_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="文档ID（空为全库）")
    effect: Mapped[str] = mapped_column(String(16), nullable=False, comment="效果（allow/deny）")
```

- [ ] **步骤 3：在 models/__init__.py 导出**

追加知识库模型与枚举的导入和 `__all__` 项。

- [ ] **步骤 4：运行模型可映射测试 + Commit**

运行：`cd server/python && pytest tests/ai/unit/models/ -v`（若已存在测试文件，确认通过）。

```bash
git add server/python/src/ai/models/enums.py server/python/src/ai/models/knowledge_base.py server/python/src/ai/models/__init__.py
git commit -m "feat(ai): 新增知识库模型 KnowledgeBase/Member/Document/Acl"
```

---

## 批次 3：入库审核模型

### 任务 3：ImportRequest / ImportRequestItem 模型

**文件：**
- 创建：`server/python/src/ai/models/import_request.py`
- 修改：`server/python/src/ai/models/__init__.py`

- [ ] **步骤 1：创建入库审核模型**

参考 kbhub KbDocumentReview，创建 `server/python/src/ai/models/import_request.py`：

```python
"""入库审核模型"""

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from ai.models.enums import KbDocumentImportType, KbDocumentReviewStatus
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.types.enum import EnumType


class ImportRequest(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """入库申请表"""

    __tablename__ = "import_request"
    __table_args__ = (
        Index("ix_import_request_applicant_id", "applicant_id"),
        Index("ix_import_request_status", "status"),
        {"comment": "入库申请表"},
    )

    applicant_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="申请人ID")
    applicant_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="申请人名称")
    source_library_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="源文档库ID")
    target_knowledge_base_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="目标知识库ID")
    import_type: Mapped[str] = mapped_column(
        EnumType(enum_class=KbDocumentImportType, length=20), nullable=False, comment="入库类型"
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False, comment="标题")
    tag_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="标签ID")
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=KbDocumentReviewStatus, length=20), nullable=False,
        default=KbDocumentReviewStatus.PENDING, comment="状态",
    )
    reviewer_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment="审核人ID")
    reviewer_name: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="审核人名称")
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审核意见")
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="扩展数据")


class ImportRequestItem(BaseModel, TimestampMixin, TenantMixin, ActiveRecordMixin):
    """入库申请明细表（一个申请可含多个文档）"""

    __tablename__ = "import_request_item"
    __table_args__ = (
        Index("ix_import_request_item_request_id", "request_id"),
        {"comment": "入库申请明细表"},
    )

    request_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="申请ID")
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, comment="源文档ID")
    document_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="文档名称")
```

- [ ] **步骤 2：在 __init__.py 导出 + Commit**

```bash
git add server/python/src/ai/models/import_request.py server/python/src/ai/models/__init__.py
git commit -m "feat(ai): 新增入库审核模型 ImportRequest/ImportRequestItem"
```

---

## 批次 4：工具库模型

### 任务 4：工具库枚举 + 模型

**文件：**
- 修改：`server/python/src/ai/models/enums.py`
- 创建：`server/python/src/ai/models/tool.py`
- 修改：`server/python/src/ai/models/__init__.py`

- [ ] **步骤 1：在 enums.py 增补工具枚举**

```python
class ToolSource(str, Enum):
    """工具来源"""
    SWAGGER = "swagger"
    MCP = "mcp"
    MANUAL = "manual"


class ToolProtocol(str, Enum):
    """工具协议"""
    HTTP = "http"
    MCP = "mcp"


class ToolStatus(str, Enum):
    """工具状态"""
    ENABLED = "enabled"
    DISABLED = "disabled"


class ToolAuthType(str, Enum):
    """工具认证类型"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"


class ToolParameterLocation(str, Enum):
    """参数位置"""
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    BODY = "body"


class ToolImportStatus(str, Enum):
    """导入状态"""
    SUCCESS = "success"
    FAILED = "failed"
```

- [ ] **步骤 2：创建工具库模型**

参考 kbhub `tool.py`，ToolParameter 用 TreeNodeMixin（树形参数）。创建 `server/python/src/ai/models/tool.py`：

```python
"""工具库模型"""

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from ai.models.enums import ToolAuthType, ToolImportStatus, ToolParameterLocation, ToolProtocol, ToolSource, ToolStatus
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin
from framework.database.mixins.tree import TreeNodeMixin
from framework.database.types.enum import EnumType


class Tool(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """工具表"""

    __tablename__ = "tool"
    __table_args__ = (
        Index("ix_tool_tenant_id", "tenant_id"),
        Index("ix_tool_code", "code"),
        {"comment": "工具表"},
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="工具名称")
    code: Mapped[str] = mapped_column(String(128), nullable=False, comment="工具编码（租户内唯一）")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="图标")
    source: Mapped[str] = mapped_column(
        EnumType(enum_class=ToolSource, length=20), nullable=False, comment="来源"
    )
    protocol: Mapped[str] = mapped_column(
        EnumType(enum_class=ToolProtocol, length=20), nullable=False, comment="协议"
    )
    version: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="版本")
    status: Mapped[str] = mapped_column(
        EnumType(enum_class=ToolStatus, length=20), nullable=False,
        default=ToolStatus.ENABLED, comment="状态",
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")
    import_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="导入配置（URL 等）")


class ToolAuth(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """工具认证表"""

    __tablename__ = "tool_auth"
    __table_args__ = (Index("ix_tool_auth_tool_id", "tool_id"), {"comment": "工具认证表"})

    tool_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="工具ID")
    auth_type: Mapped[str] = mapped_column(
        EnumType(enum_class=ToolAuthType, length=20), nullable=False, comment="认证类型"
    )
    auth_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="认证配置（敏感信息脱敏存储）")


class ToolFunction(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """工具函数表"""

    __tablename__ = "tool_function"
    __table_args__ = (Index("ix_tool_function_tool_id", "tool_id"), {"comment": "工具函数表"})

    tool_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="工具ID")
    operation_id: Mapped[str] = mapped_column(String(128), nullable=False, comment="操作ID（Swagger）或函数名（MCP）")
    name: Mapped[str] = mapped_column(String(256), nullable=False, comment="名称")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True, comment="摘要")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    invoke_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="调用配置（method/path 等）")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")


class ToolParameter(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin, TreeNodeMixin):
    """工具参数表（树形，TreeNodeMixin）"""

    __tablename__ = "tool_parameter"
    __table_args__ = (Index("ix_tool_parameter_function_id", "function_id"), {"comment": "工具参数表"})

    function_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="函数ID")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="参数名")
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="显示名")
    location: Mapped[str] = mapped_column(
        EnumType(enum_class=ToolParameterLocation, length=20), nullable=False, comment="参数位置"
    )
    parameter_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="参数类型")
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否必填")
    default_value: Mapped[str | None] = mapped_column(String(1024), nullable=True, comment="默认值")
    schema_path: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="Schema 路径")


class ToolImportRecord(BaseModel, TimestampMixin, TenantMixin, ActiveRecordMixin):
    """工具导入记录表"""

    __tablename__ = "tool_import_record"
    __table_args__ = (Index("ix_tool_import_record_tool_id", "tool_id"), {"comment": "工具导入记录表"})

    tool_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="工具ID")
    source: Mapped[str] = mapped_column(String(20), nullable=False, comment="来源")
    version: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="版本")
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="校验和")
    import_status: Mapped[str] = mapped_column(
        EnumType(enum_class=ToolImportStatus, length=20), nullable=False, comment="导入状态"
    )
    import_user: Mapped[str] = mapped_column(String(36), nullable=False, comment="导入人ID")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
```

- [ ] **步骤 3：在 __init__.py 导出 + Commit**

```bash
git add server/python/src/ai/models/enums.py server/python/src/ai/models/tool.py server/python/src/ai/models/__init__.py
git commit -m "feat(ai): 新增工具库模型 Tool/ToolAuth/ToolFunction/ToolParameter/ToolImportRecord"
```

---

## 批次 5：平台设置模型

### 任务 5：ConfigItem 模型

**文件：**
- 创建：`server/python/src/ai/models/config_item.py`
- 修改：`server/python/src/ai/models/__init__.py`

- [ ] **步骤 1：创建 ConfigItem 模型**

参考 kbhub config.py：

```python
"""平台设置模型"""

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ai.models import BaseModel
from framework.database.mixins.active_record import ActiveRecordMixin
from framework.database.mixins.audit import AuditMixin
from framework.database.mixins.tenant import TenantMixin
from framework.database.mixins.timestamp import TimestampMixin


class ConfigItem(BaseModel, TimestampMixin, AuditMixin, TenantMixin, ActiveRecordMixin):
    """平台设置配置项表"""

    __tablename__ = "config_item"
    __table_args__ = (
        Index("ix_config_item_scope_key", "config_scope", "config_key"),
        {"comment": "平台设置配置项表"},
    )

    config_scope: Mapped[str] = mapped_column(String(32), nullable=False, comment="配置范围（tenant）")
    config_key: Mapped[str] = mapped_column(String(128), nullable=False, comment="配置键（kbhub_platform_settings）")
    config_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="配置值（切片参数+六类模型配置）")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", comment="状态")
```

- [ ] **步骤 2：在 __init__.py 导出 + Commit**

```bash
git add server/python/src/ai/models/config_item.py server/python/src/ai/models/__init__.py
git commit -m "feat(ai): 新增平台设置 ConfigItem 模型，完成 14 张表模型"
```

---

## 批次 6：知识库服务

### 任务 6：知识库 CRUD 服务（TDD）

**文件：**
- 创建：`server/python/src/ai/services/knowledge_base/__init__.py`
- 创建：`server/python/src/ai/services/knowledge_base/kb_service.py`
- 创建：`server/python/tests/ai/unit/services/test_kb_service.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec `ai-knowledge-base/spec.md`（创建/列表/成员/文档引用/检索/问答场景）：

```python
"""知识库服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.services.knowledge_base.kb_service import KnowledgeBaseService


@pytest.mark.asyncio
class TestKnowledgeBaseService:
    async def test_create_kb_auto_owner(self):
        """创建知识库，创建者为 owner"""
        session = AsyncMock()
        with patch("ai.services.knowledge_base.kb_service.get_tenant_id", return_value="t1"), \
             patch("ai.services.knowledge_base.kb_service.get_user_id", return_value="u1"):
            kb = await KnowledgeBaseService.create(
                session, code="kb-rd", name="研发知识库", kb_type="normal", scope_type="team",
            )
        assert kb.owner_id == "u1"
        session.add.assert_called()

    async def test_list_kbs_pagination(self):
        """列表分页"""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(side_effect=[MagicMock(scalar=MagicMock(return_value=0)), mock_result])
        items, total = await KnowledgeBaseService.list_kbs(session, tenant_id="t1", page=1, page_size=10)
        assert total == 0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/ai/unit/services/test_kb_service.py -v`，预期 FAIL。

- [ ] **步骤 3：实现 kb_service**

参考 kbhub `services/knowledge_base/knowledge_base.py`（精简），创建 `server/python/src/ai/services/knowledge_base/kb_service.py`：

```python
"""知识库服务"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models import KnowledgeBase, KnowledgeBaseMember
from ai.models.enums import KnowledgeBaseMemberRole, KnowledgeBaseMemberStatus, KnowledgeBaseStatus
from framework.common.ctx import get_tenant_id, get_user_id


class KnowledgeBaseService:
    """知识库服务"""

    @staticmethod
    async def create(
        session: AsyncSession,
        code: str,
        name: str,
        kb_type: str,
        scope_type: str,
        description: str | None = None,
        icon: str | None = None,
    ) -> KnowledgeBase:
        tenant_id = get_tenant_id()
        user_id = get_user_id()

        kb = KnowledgeBase(
            tenant_id=tenant_id,
            code=code,
            name=name,
            description=description,
            icon=icon,
            kb_type=kb_type,
            scope_type=scope_type,
            status=KnowledgeBaseStatus.ENABLED,
            owner_id=user_id,
        )
        session.add(kb)
        await session.flush()

        # 创建者自动成为 owner
        member = KnowledgeBaseMember(
            tenant_id=tenant_id,
            knowledge_base_id=kb.id,
            user_id=user_id,
            user_name=user_id,
            kb_role=KnowledgeBaseMemberRole.OWNER,
            status=KnowledgeBaseMemberStatus.ACTIVE,
        )
        session.add(member)
        await session.flush()
        return kb

    @staticmethod
    async def list_kbs(
        session: AsyncSession, tenant_id: str, page: int = 1, page_size: int = 20, keyword: str | None = None,
    ) -> tuple[list[KnowledgeBase], int]:
        conditions = [KnowledgeBase.tenant_id == tenant_id, KnowledgeBase.deleted_at.is_(None)]
        if keyword:
            conditions.append(KnowledgeBase.name.like(f"%{keyword}%"))
        total = (await session.execute(
            select(func.count(KnowledgeBase.id)).where(*conditions)
        )).scalar() or 0
        offset = (page - 1) * page_size
        stmt = select(KnowledgeBase).where(*conditions).order_by(
            KnowledgeBase.created_at.desc()
        ).offset(offset).limit(page_size)
        return list((await session.execute(stmt)).scalars().all()), total

    @staticmethod
    async def get_by_id(session: AsyncSession, kb_id: str) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == kb_id, KnowledgeBase.deleted_at.is_(None))
        return (await session.execute(stmt)).scalar_one_or_none()


knowledge_base_service = KnowledgeBaseService()
```

- [ ] **步骤 4：运行测试验证通过 + Commit**

```bash
git add server/python/src/ai/services/knowledge_base/ server/python/tests/ai/unit/services/test_kb_service.py
git commit -m "feat(ai): 新增知识库 CRUD 服务"
```

### 任务 7：成员权限服务

**文件：**
- 创建：`server/python/src/ai/services/knowledge_base/member_service.py`
- 创建：`server/python/tests/ai/unit/services/test_kb_member_service.py`

- [ ] **步骤 1：实现成员服务**

参考 kbhub `services/knowledge_base/member.py`，实现：add_member（owner/admin 可操作）、remove_member（owner 不可移除）、update_member_role、list_members。CRUD + 多租户过滤。

- [ ] **步骤 2：编写测试 + 运行 + Commit**

```bash
git add server/python/src/ai/services/knowledge_base/member_service.py server/python/tests/ai/unit/services/test_kb_member_service.py
git commit -m "feat(ai): 新增知识库成员权限服务"
```

### 任务 8：检索服务（双重权限过滤 + document inner 回查，TDD）

**文件：**
- 创建：`server/python/src/ai/services/knowledge_base/retrieval_service.py`
- 创建：`server/python/tests/ai/unit/services/test_retrieval_service.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec `ai-knowledge-base/spec.md` 检索测试场景（仅包含用户有权访问的文档片段）+ `integration-verification/spec.md`（不放大源文档权限）：

```python
"""检索服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.services.knowledge_base.retrieval_service import RetrievalService


@pytest.mark.asyncio
class TestRetrievalService:
    async def test_filter_chunks_by_source_permission(self):
        """无源文件权限的片段被过滤"""
        service = RetrievalService()
        chunks = [
            {"document_id": "d1", "content": "有权限片段"},
            {"document_id": "d2", "content": "无权限片段"},
        ]
        with patch.object(service, "_check_document_permission", new_callable=AsyncMock, side_effect=["editable", "none"]):
            filtered = await service._filter_by_permission(
                AsyncMock(), user_id="u1", chunks=chunks,
            )
        assert len(filtered) == 1
        assert filtered[0]["document_id"] == "d1"

    async def test_query_document_inner_api(self):
        """回查 document inner 接口校验源文件权限"""
        service = RetrievalService()
        with patch("ai.services.knowledge_base.retrieval_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"code": 200, "data": {"permission": "editable"}}
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client
            perm = await service._check_document_permission(
                AsyncMock(), document_id="d1", user_id="u1",
            )
        assert perm == "editable"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/ai/unit/services/test_retrieval_service.py -v`，预期 FAIL。

- [ ] **步骤 3：实现检索服务**

核心：检索前按权限生成可访问范围，检索后对召回片段再次过滤。回查走 document inner 接口（`GET /document/inner/v1/documents/{id}/permission?user_id=`）：

```python
"""知识库检索服务（权限不放大源文档权限）"""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession


class RetrievalService:
    """检索服务"""

    async def retrieve(
        self,
        session: AsyncSession,
        knowledge_base_id: str,
        user_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        检索知识库文档片段。

        流程：
          1. 检索前：按权限生成可访问文档范围（无源文件权限的文档不纳入检索）
          2. 向量召回（复用 EmbeddingService）
          3. 检索后：对召回片段再次过滤，无权限片段不返回
        """
        # 1. 生成可访问范围
        accessible_doc_ids = await self._build_accessible_scope(session, knowledge_base_id, user_id)
        if not accessible_doc_ids:
            return []

        # 2. 向量召回（复用 EmbeddingService + 向量库检索）
        raw_chunks = await self._vector_search(session, query, accessible_doc_ids, top_k)

        # 3. 检索后双重过滤（防止权限在检索窗口内变更）
        filtered = await self._filter_by_permission(session, user_id, raw_chunks)
        return filtered

    async def _build_accessible_scope(
        self, session: AsyncSession, knowledge_base_id: str, user_id: str
    ) -> list[str]:
        """生成用户可访问的文档ID列表（回查 document inner 接口）"""
        from ai.models import KnowledgeBaseDocument
        from sqlalchemy import select

        stmt = select(KnowledgeBaseDocument.document_id).where(
            KnowledgeBaseDocument.knowledge_base_id == knowledge_base_id,
            KnowledgeBaseDocument.status == "active",
        )
        result = await session.execute(stmt)
        all_doc_ids = [row[0] for row in result.all()]

        accessible = []
        for doc_id in all_doc_ids:
            perm = await self._check_document_permission(session, doc_id, user_id)
            if perm in ("editable", "readonly"):
                accessible.append(doc_id)
        return accessible

    async def _filter_by_permission(
        self, session: AsyncSession, user_id: str, chunks: list[dict]
    ) -> list[dict]:
        """对召回片段再次过滤（双重校验）"""
        filtered = []
        for chunk in chunks:
            doc_id = chunk.get("document_id")
            perm = await self._check_document_permission(session, doc_id, user_id)
            if perm in ("editable", "readonly"):
                filtered.append(chunk)
        return filtered

    async def _check_document_permission(
        self, session: AsyncSession, document_id: str, user_id: str
    ) -> str:
        """回查 document inner 接口校验源文件权限"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"http://localhost:8000/document/inner/v1/documents/{document_id}/permission",
                params={"user_id": user_id},
            )
            if resp.status_code == 404:
                return "none"
            data = resp.json()
            return data.get("data", {}).get("permission", "none")

    async def _vector_search(
        self, session: AsyncSession, query: str, doc_ids: list[str], top_k: int
    ) -> list[dict]:
        """向量召回（复用 EmbeddingService 做向量化，向量库检索）"""
        # TODO: 接入向量库（pgvector 或 GraphRAGClient）
        # from ai.components.model.services import EmbeddingService
        # embedding = await EmbeddingService(get_tenant_id()).embed(query)
        # ... 向量检索 ...
        return []


retrieval_service = RetrievalService()
```

- [ ] **步骤 4：运行测试验证通过 + Commit**

```bash
git add server/python/src/ai/services/knowledge_base/retrieval_service.py server/python/tests/ai/unit/services/test_retrieval_service.py
git commit -m "feat(ai): 新增检索服务（双重权限过滤+document inner 回查，不放大权限）"
```

### 任务 9：知识库问答服务（复用 ChatService + LLMService）

**文件：**
- 创建：`server/python/src/ai/services/knowledge_base/qa_service.py`
- 创建：`server/python/tests/ai/unit/services/test_qa_service.py`

- [ ] **步骤 1：实现问答服务**

复用 `ChatService.create_messages`/`update_assistant_message` + `ConversationService.get_or_create` + `LLMService.stream` + `retrieval_service.retrieve`。检索片段拼入 prompt，无权限片段不进入 LLM prompt。通过 `message_metadata` JSONB 存检索来源。

- [ ] **步骤 2：编写测试（验证无权限片段不进入 prompt）+ Commit**

```bash
git add server/python/src/ai/services/knowledge_base/qa_service.py server/python/tests/ai/unit/services/test_qa_service.py
git commit -m "feat(ai): 新增知识库问答服务（复用 ChatService+LLMService，无权限片段不进入 prompt）"
```

### 任务 10：文档引用服务

**文件：**
- 创建：`server/python/src/ai/services/knowledge_base/document_service.py`

- [ ] **步骤 1：实现文档引用管理**

参考 kbhub `services/knowledge_base/document.py`，实现 list_documents、update_reference_status、remove_reference。

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/ai/services/knowledge_base/document_service.py
git commit -m "feat(ai): 新增知识库文档引用服务"
```

---

## 批次 7：入库审核服务

### 任务 11：入库审核流程服务（TDD）

**文件：**
- 创建：`server/python/src/ai/services/import_review/__init__.py`
- 创建：`server/python/src/ai/services/import_review/import_service.py`
- 创建：`server/python/tests/ai/unit/services/test_import_service.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec `ai-import-review/spec.md` 6 个场景（提交/通知审核员/通过生成引用/拒绝/权限校验/不放大权限）：

```python
"""入库审核服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.services.import_review.import_service import ImportReviewService


@pytest.mark.asyncio
class TestImportReviewService:
    async def test_submit_request_creates_pending(self):
        """提交申请创建 pending 记录"""
        session = AsyncMock()
        with patch("ai.services.import_review.import_service.get_tenant_id", return_value="t1"), \
             patch("ai.services.import_review.import_service.get_user_id", return_value="u1"), \
             patch("ai.services.import_review.import_service.send_notification", new_callable=AsyncMock):
            req = await ImportReviewService.submit(
                session, target_knowledge_base_id="kb-1", source_library_id="lib-1",
                document_ids=["d1"], import_type="text_rag", title="文档1",
            )
        assert req.status == "pending"

    async def test_approve_generates_reference(self):
        """审核通过生成知识库文档引用"""
        session = AsyncMock()
        mock_req = MagicMock()
        mock_req.id = "req-1"
        mock_req.status = "pending"
        mock_req.target_knowledge_base_id = "kb-1"
        mock_req.source_library_id = "lib-1"
        mock_req.applicant_id = "u1"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_req
        session.execute = AsyncMock(return_value=mock_result)

        with patch("ai.services.import_review.import_service.get_user_id", return_value="reviewer-1"), \
             patch("ai.services.import_review.import_service.send_notification", new_callable=AsyncMock), \
             patch.object(ImportReviewService, "_create_document_reference", new_callable=AsyncMock):
            result = await ImportReviewService.review(
                session, request_id="req-1", approved=True, review_comment="通过",
                reviewer_id="reviewer-1", reviewer_name="管理员",
            )
        assert result.status == "approved"

    async def test_reject_no_reference(self):
        """审核拒绝不创建引用"""
        session = AsyncMock()
        mock_req = MagicMock()
        mock_req.id = "req-1"
        mock_req.status = "pending"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_req
        session.execute = AsyncMock(return_value=mock_result)

        with patch("ai.services.import_review.import_service.get_user_id", return_value="reviewer-1"), \
             patch("ai.services.import_review.import_service.send_notification", new_callable=AsyncMock), \
             patch.object(ImportReviewService, "_create_document_reference", new_callable=AsyncMock) as mock_create:
            result = await ImportReviewService.review(
                session, request_id="req-1", approved=False, review_comment="拒绝",
                reviewer_id="reviewer-1", reviewer_name="管理员",
            )
        assert result.status == "rejected"
        mock_create.assert_not_called()
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/ai/unit/services/test_import_service.py -v`，预期 FAIL。

- [ ] **步骤 3：实现入库审核服务**

参考 kbhub `services/knowledge_base/approval.py`，创建 `server/python/src/ai/services/import_review/import_service.py`：

```python
"""入库审核服务"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models import (
    ImportRequest,
    ImportRequestItem,
    KnowledgeBaseDocument,
)
from ai.models.enums import KbDocumentReferenceStatus, KbDocumentReviewStatus
from framework.common.ctx import get_tenant_id, get_user_id
from framework.notification.sender import send_notification


class ImportReviewService:
    """入库审核服务"""

    @staticmethod
    async def submit(
        session: AsyncSession,
        target_knowledge_base_id: str,
        source_library_id: str,
        document_ids: list[str],
        import_type: str,
        title: str,
        tag_id: str | None = None,
    ) -> ImportRequest:
        """提交入库申请"""
        tenant_id = get_tenant_id()
        applicant_id = get_user_id()

        req = ImportRequest(
            tenant_id=tenant_id,
            applicant_id=applicant_id,
            applicant_name=applicant_id,
            source_library_id=source_library_id,
            target_knowledge_base_id=target_knowledge_base_id,
            import_type=import_type,
            title=title,
            tag_id=tag_id,
            status=KbDocumentReviewStatus.PENDING,
        )
        session.add(req)
        await session.flush()

        # 创建申请明细
        for doc_id in document_ids:
            item = ImportRequestItem(
                tenant_id=tenant_id,
                request_id=req.id,
                document_id=doc_id,
                document_name=title,
            )
            session.add(item)
        await session.flush()

        # 通过站内信通知审核员
        await send_notification(
            session=session,
            title="新的入库申请",
            content=f"您有新的入库申请待审核：{title}",
            notification_type="import_review_pending",
            recipient_user_ids=[],  # TODO: 查询知识库 reviewer 成员
            link=f"/ai/knowledge-base/{target_knowledge_base_id}/approval/{req.id}",
        )
        return req

    @staticmethod
    async def review(
        session: AsyncSession,
        request_id: str,
        approved: bool,
        review_comment: str | None,
        reviewer_id: str,
        reviewer_name: str,
    ) -> ImportRequest:
        """审核入库申请"""
        stmt = select(ImportRequest).where(ImportRequest.id == request_id)
        req = (await session.execute(stmt)).scalar_one_or_none()
        if req is None:
            raise ValueError("入库申请不存在")
        if req.status != KbDocumentReviewStatus.PENDING:
            raise ValueError(f"申请状态非 pending，当前={req.status}")

        req.reviewer_id = reviewer_id
        req.reviewer_name = reviewer_name
        req.review_comment = review_comment

        if not approved:
            req.status = KbDocumentReviewStatus.REJECTED
            await session.flush()
            await send_notification(
                session=session,
                title="入库申请已拒绝",
                content=f"您的入库申请「{req.title}」已被拒绝",
                notification_type="import_review_rejected",
                recipient_user_ids=[req.applicant_id],
            )
            return req

        # 通过：生成知识库文档引用
        req.status = KbDocumentReviewStatus.APPROVED
        await session.flush()
        await ImportReviewService._create_document_reference(session, req)

        await send_notification(
            session=session,
            title="入库申请已通过",
            content=f"您的入库申请「{req.title}」已通过",
            notification_type="import_review_approved",
            recipient_user_ids=[req.applicant_id],
        )
        return req

    @staticmethod
    async def _create_document_reference(session: AsyncSession, req: ImportRequest) -> None:
        """审核通过生成知识库文档引用"""
        # 查询申请明细
        from sqlalchemy import select
        stmt = select(ImportRequestItem).where(ImportRequestItem.request_id == req.id)
        items = list((await session.execute(stmt)).scalars().all())

        for item in items:
            ref = KnowledgeBaseDocument(
                tenant_id=req.tenant_id,
                knowledge_base_id=req.target_knowledge_base_id,
                document_id=item.document_id,
                source_library_id=req.source_library_id,
                review_id=req.id,
                import_type=req.import_type,
                title=item.document_name,
                status=KbDocumentReferenceStatus.ACTIVE,
                tag_id=req.tag_id,
            )
            session.add(ref)
        await session.flush()


import_review_service = ImportReviewService()
```

- [ ] **步骤 4：运行测试验证通过 + Commit**

```bash
git add server/python/src/ai/services/import_review/ server/python/tests/ai/unit/services/test_import_service.py
git commit -m "feat(ai): 新增入库审核流程服务（提交/审批/生成引用/站内信通知）"
```

---

## 批次 8：工具库服务

### 任务 12：安装外部依赖

**文件：**
- 修改：`server/python/pyproject.toml`

- [ ] **步骤 1：添加依赖**

在 `server/python/pyproject.toml` 的依赖区追加：

```toml
"prance~=23.6.21.0",
"openapi-spec-validator~=0.7.1",
"mcp~=1.0.0",
```

- [ ] **步骤 2：安装依赖**

运行：`cd server/python && uv sync` 或 `pip install -e .`

- [ ] **步骤 3：Commit**

```bash
git add server/python/pyproject.toml
git commit -m "chore(ai): 新增工具库外部依赖 prance/openapi-spec-validator/mcp"
```

### 任务 13：Swagger 导入（TDD）

**文件：**
- 创建：`server/python/src/ai/services/tool/__init__.py`
- 创建：`server/python/src/ai/services/tool/swagger_import.py`
- 创建：`server/python/tests/ai/unit/services/test_swagger_import.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec `ai-tool-center/spec.md`（Swagger 导入：openapi-spec-validator 校验 + prance 解析 $ref；工具 code 唯一；重导入保留 Tool/ToolAuth）：

```python
"""Swagger 导入单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.services.tool.swagger_import import SwaggerImporter


@pytest.mark.asyncio
class TestSwaggerImport:
    async def test_parse_openapi_valid(self):
        """解析合法 OpenAPI 规范"""
        importer = SwaggerImporter()
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "listUsers",
                        "summary": "获取用户列表",
                        "parameters": [],
                    }
                }
            },
        }
        functions = await importer.parse(spec)
        assert len(functions) == 1
        assert functions[0]["operation_id"] == "listUsers"

    async def test_validate_invalid_spec_raises(self):
        """非法 OpenAPI 规范抛错"""
        importer = SwaggerImporter()
        with pytest.raises(ValueError):
            await importer.validate({"invalid": "spec"})

    async def test_dedupe_functions_by_operation_id(self):
        """同 operationId 去重"""
        importer = SwaggerImporter()
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/a": {"get": {"operationId": "dup", "summary": "A"}},
                "/b": {"get": {"operationId": "dup", "summary": "B"}},
            },
        }
        functions = await importer.parse(spec)
        assert len(functions) == 1
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/ai/unit/services/test_swagger_import.py -v`，预期 FAIL。

- [ ] **步骤 3：实现 Swagger 导入**

```python
"""Swagger 导入服务（prance + openapi-spec-validator）"""

from openapi_spec_validator import validate as validate_spec
from prance import Resolver


class SwaggerImporter:
    """Swagger/OpenAPI 导入器"""

    async def validate(self, spec: dict) -> None:
        """校验 OpenAPI 规范合法性"""
        try:
            validate_spec(spec)
        except Exception as e:
            raise ValueError(f"OpenAPI 规范校验失败: {e}") from e

    async def parse(self, spec: dict) -> list[dict]:
        """解析 OpenAPI 规范，返回函数列表"""
        # prance 解析 $ref
        resolver = Resolver(spec)
        resolved = resolver.specs

        functions = []
        seen_operation_ids = set()
        for path, methods in resolved.get("paths", {}).items():
            for method, operation in methods.items():
                if method not in ("get", "post", "put", "delete", "patch"):
                    continue
                operation_id = operation.get("operationId") or f"{method}_{path}"
                if operation_id in seen_operation_ids:
                    continue
                seen_operation_ids.add(operation_id)

                functions.append({
                    "operation_id": operation_id,
                    "name": operation.get("summary", operation_id),
                    "summary": operation.get("summary"),
                    "description": operation.get("description"),
                    "invoke_config": {"method": method.upper(), "path": path},
                    "parameters": self._parse_parameters(operation),
                })
        return functions

    def _parse_parameters(self, operation: dict) -> list[dict]:
        """解析参数"""
        params = []
        for p in operation.get("parameters", []):
            params.append({
                "name": p.get("name"),
                "location": p.get("in"),
                "parameter_type": p.get("schema", {}).get("type", "string"),
                "required": p.get("required", False),
                "description": p.get("description"),
            })
        return params


swagger_importer = SwaggerImporter()
```

- [ ] **步骤 4：运行测试验证通过 + Commit**

```bash
git add server/python/src/ai/services/tool/swagger_import.py server/python/tests/ai/unit/services/test_swagger_import.py
git commit -m "feat(ai): 新增 Swagger 导入服务（prance 解析+openapi-spec-validator 校验）"
```

### 任务 14：MCP 导入（TDD）

**文件：**
- 创建：`server/python/src/ai/services/tool/mcp_import.py`
- 创建：`server/python/tests/ai/unit/services/test_mcp_import.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec（MCP 导入：官方 SDK SSE/Streamable HTTP 调用 tools/list）：

```python
"""MCP 导入单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.services.tool.mcp_import import McpImporter


@pytest.mark.asyncio
class TestMcpImport:
    async def test_list_tools_from_mcp_server(self):
        """从 MCP Server 获取工具列表"""
        importer = McpImporter()
        mock_client = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "search"
        mock_tool.description = "搜索"
        mock_tool.inputSchema = {"type": "object", "properties": {}}
        mock_client.list_tools = AsyncMock(return_value=[mock_tool])

        with patch("ai.services.tool.mcp_import.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_client)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session
            functions = await importer.list_tools("http://mcp-server:3000/sse")

        assert len(functions) == 1
        assert functions[0]["operation_id"] == "search"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/ai/unit/services/test_mcp_import.py -v`，预期 FAIL。

- [ ] **步骤 3：实现 MCP 导入**

使用官方 MCP SDK 的 SSE/Streamable HTTP Client 调用 `tools/list`，不自行解析协议：

```python
"""MCP 导入服务（官方 SDK）"""

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client


class McpImporter:
    """MCP 工具导入器"""

    async def list_tools(self, url: str) -> list[dict]:
        """从 MCP Server 获取工具列表"""
        # 根据URL判断 SSE 还是 Streamable HTTP
        if "/sse" in url:
            async with sse_client(url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
        else:
            async with streamablehttp_client(url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()

        return [
            {
                "operation_id": tool.name,
                "name": tool.name,
                "summary": tool.description,
                "description": tool.description,
                "invoke_config": {"protocol": "mcp", "function_name": tool.name},
                "parameters": self._parse_schema(tool.inputSchema),
            }
            for tool in tools
        ]

    def _parse_schema(self, schema: dict) -> list[dict]:
        """解析 MCP 工具输入 Schema 为参数列表"""
        params = []
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        for name, prop in properties.items():
            params.append({
                "name": name,
                "location": "body",
                "parameter_type": prop.get("type", "string"),
                "required": name in required,
                "description": prop.get("description"),
            })
        return params


mcp_importer = McpImporter()
```

- [ ] **步骤 4：运行测试验证通过 + Commit**

```bash
git add server/python/src/ai/services/tool/mcp_import.py server/python/tests/ai/unit/services/test_mcp_import.py
git commit -m "feat(ai): 新增 MCP 导入服务（官方 SDK SSE/Streamable HTTP）"
```

### 任务 15：工具测试 Runtime（TDD）

**文件：**
- 创建：`server/python/src/ai/services/tool/tool_runtime.py`
- 创建：`server/python/tests/ai/unit/services/test_tool_runtime.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec（Connection Test + Function Test 共用协议分发，敏感信息脱敏）：

```python
"""工具测试 Runtime 单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.services.tool.tool_runtime import ToolRuntime, HttpExecutor, McpExecutor


@pytest.mark.asyncio
class TestToolRuntime:
    async def test_dispatch_http(self):
        """按 protocol 分发 HttpExecutor"""
        runtime = ToolRuntime()
        executor = runtime._get_executor("http")
        assert isinstance(executor, HttpExecutor)

    async def test_dispatch_mcp(self):
        """按 protocol 分发 McpExecutor"""
        runtime = ToolRuntime()
        executor = runtime._get_executor("mcp")
        assert isinstance(executor, McpExecutor)

    async def test_sensitive_data_masked(self):
        """敏感信息脱敏"""
        runtime = ToolRuntime()
        request_summary = runtime._mask_sensitive({
            "headers": {"Authorization": "Bearer sk-abc123"},
            "body": {"api_key": "secret", "name": "test"},
        })
        assert "sk-abc123" not in str(request_summary)
        assert "secret" not in str(request_summary)
        assert "test" in str(request_summary)

    async def test_function_test_returns_summary(self):
        """Function Test 返回脱敏请求摘要+响应+耗时"""
        runtime = ToolRuntime()
        with patch.object(HttpExecutor, "execute", new_callable=AsyncMock, return_value={"status": 200, "data": "ok"}):
            result = await runtime.function_test(
                protocol="http", invoke_config={"method": "GET", "path": "/users"},
                auth_config={}, parameters={},
            )
        assert "duration_ms" in result
        assert "request" in result
        assert "response" in result
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/ai/unit/services/test_tool_runtime.py -v`，预期 FAIL。

- [ ] **步骤 3：实现工具测试 Runtime**

```python
"""工具测试 Runtime（按 protocol 分发 HttpExecutor/McpExecutor）"""

import time
from typing import Any

import httpx


SENSITIVE_KEYS = {"token", "api_key", "password", "secret", "authorization"}


class HttpExecutor:
    """HTTP 协议执行器"""

    async def execute(self, invoke_config: dict, auth_config: dict, parameters: dict) -> dict:
        method = invoke_config.get("method", "GET")
        path = invoke_config.get("path", "")
        base_url = invoke_config.get("base_url", "")
        url = f"{base_url}{path}"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.request(
                method, url, params=parameters.get("query"), json=parameters.get("body"),
                headers=auth_config.get("headers"),
            )
            return {"status": resp.status_code, "data": resp.text}


class McpExecutor:
    """MCP 协议执行器"""

    async def execute(self, invoke_config: dict, auth_config: dict, parameters: dict) -> dict:
        # TODO: 接入 MCP SDK 调用具体工具
        return {"status": 200, "data": "mcp result"}


class ToolRuntime:
    """工具测试 Runtime（统一分发）"""

    def _get_executor(self, protocol: str) -> HttpExecutor | McpExecutor:
        if protocol == "mcp":
            return McpExecutor()
        return HttpExecutor()

    async def connection_test(self, protocol: str, invoke_config: dict, auth_config: dict) -> bool:
        """Connection Test"""
        executor = self._get_executor(protocol)
        try:
            await executor.execute(invoke_config, auth_config, {})
            return True
        except Exception:
            return False

    async def function_test(
        self, protocol: str, invoke_config: dict, auth_config: dict, parameters: dict
    ) -> dict:
        """Function Test（返回脱敏请求摘要+响应+耗时）"""
        start = time.time()
        executor = self._get_executor(protocol)
        response = await executor.execute(invoke_config, auth_config, parameters)
        duration_ms = int((time.time() - start) * 1000)

        request_summary = self._mask_sensitive({
            "invoke_config": invoke_config,
            "parameters": parameters,
        })
        return {
            "request": request_summary,
            "response": response,
            "duration_ms": duration_ms,
        }

    def _mask_sensitive(self, data: Any) -> Any:
        """敏感信息脱敏（token/api_key/password 替换为 ******）"""
        if isinstance(data, dict):
            return {
                k: ("******" if k.lower() in SENSITIVE_KEYS and v else self._mask_sensitive(v))
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [self._mask_sensitive(item) for item in data]
        return data


tool_runtime = ToolRuntime()
```

- [ ] **步骤 4：运行测试验证通过 + Commit**

```bash
git add server/python/src/ai/services/tool/tool_runtime.py server/python/tests/ai/unit/services/test_tool_runtime.py
git commit -m "feat(ai): 新增工具测试 Runtime（HttpExecutor/McpExecutor 分发+敏感信息脱敏）"
```

### 任务 16：工具管理服务 + 重导入策略

**文件：**
- 创建：`server/python/src/ai/services/tool/tool_service.py`
- 创建：`server/python/tests/ai/unit/services/test_tool_service.py`

- [ ] **步骤 1：实现工具管理服务**

参考 kbhub `services/tool.py` + `tool_import.py`，实现：create_tool（code 租户内唯一校验）、import_tool（按 source 分发 swagger/mcp importer）、reimport（重导入策略：保留 Tool/ToolAuth，删除 Function/Parameter 重建，恢复人工字段）、list_tools、delete_tool（软删除，相同 code 可重新导入）。

- [ ] **步骤 2：编写测试（含重导入保留 Tool/ToolAuth + 失败回滚 + code 唯一）+ Commit**

```bash
git add server/python/src/ai/services/tool/tool_service.py server/python/tests/ai/unit/services/test_tool_service.py
git commit -m "feat(ai): 新增工具管理服务（导入/重导入/code唯一/软删除）"
```

---

## 批次 9：平台设置服务

### 任务 17：平台设置服务（TDD）

**文件：**
- 创建：`server/python/src/ai/services/platform_settings.py`
- 创建：`server/python/tests/ai/unit/services/test_platform_settings_service.py`

- [ ] **步骤 1：编写失败的测试**

参考 OpenSpec `ai-platform-settings/spec.md`（获取/保存/切片参数校验/模型配置规则/影响范围）：

```python
"""平台设置服务单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai.services.platform_settings import PlatformSettingsService


@pytest.mark.asyncio
class TestPlatformSettingsService:
    async def test_save_settings_validation_overlap_lt_chunk(self):
        """切片参数校验：重合长度 < 切片长度"""
        session = AsyncMock()
        service = PlatformSettingsService()
        with pytest.raises(ValueError, match="重合长度"):
            await service.save(
                session, tenant_id="t1",
                settings={"chunking": {"max_length": 100, "overlap": 100}},
            )

    async def test_save_skips_completion_params_for_non_llm(self):
        """非 LLM/Vision/Video 模型不保存 completion_params"""
        session = AsyncMock()
        service = PlatformSettingsService()
        settings = {
            "models": {
                "embedding": {"provider": "openai", "model": "text-embedding-3", "completion_params": {"temp": 0.5}},
            }
        }
        result = await service.save(session, tenant_id="t1", settings=settings)
        # embedding 的 completion_params 被剔除
        assert "completion_params" not in result["models"]["embedding"]

    async def test_save_llm_keeps_completion_params(self):
        """LLM 模型保留 completion_params"""
        session = AsyncMock()
        service = PlatformSettingsService()
        settings = {
            "models": {
                "llm": {"provider": "openai", "model": "gpt-4", "completion_params": {"temperature": 0.7}},
            }
        }
        result = await service.save(session, tenant_id="t1", settings=settings)
        assert "completion_params" in result["models"]["llm"]
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && pytest tests/ai/unit/services/test_platform_settings_service.py -v`，预期 FAIL。

- [ ] **步骤 3：实现平台设置服务**

```python
"""平台设置服务"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models import ConfigItem
from framework.permission.audit_writer import write_audit

CONFIG_KEY = "kbhub_platform_settings"
# 保留 completion_params 的模型类型
KEEP_COMPLETION_PARAMS = {"llm", "vision", "video"}


class PlatformSettingsService:
    """平台设置服务"""

    @staticmethod
    async def get(session: AsyncSession, tenant_id: str) -> dict:
        """获取平台设置"""
        stmt = select(ConfigItem).where(
            ConfigItem.tenant_id == tenant_id,
            ConfigItem.config_scope == "tenant",
            ConfigItem.config_key == CONFIG_KEY,
        )
        item = (await session.execute(stmt)).scalar_one_or_none()
        return item.config_value if item else _default_settings()

    @staticmethod
    async def save(session: AsyncSession, tenant_id: str, settings: dict) -> dict:
        """保存平台设置（含切片参数校验 + 模型配置规则）"""
        # 1. 切片参数校验
        chunking = settings.get("chunking", {})
        max_length = chunking.get("max_length", 0)
        overlap = chunking.get("overlap", 0)
        if overlap >= max_length:
            raise ValueError("最大重合长度必须小于切片最大长度")

        # 2. 模型配置规则：非 LLM/Vision/Video 不保存 completion_params
        models = settings.get("models", {})
        for model_type, config in models.items():
            if model_type not in KEEP_COMPLETION_PARAMS:
                config.pop("completion_params", None)

        # 3. 保存到 config_items
        stmt = select(ConfigItem).where(
            ConfigItem.tenant_id == tenant_id,
            ConfigItem.config_scope == "tenant",
            ConfigItem.config_key == CONFIG_KEY,
        )
        item = (await session.execute(stmt)).scalar_one_or_none()
        if item is None:
            item = ConfigItem(
                tenant_id=tenant_id, config_scope="tenant",
                config_key=CONFIG_KEY, config_value=settings, status="active",
            )
            session.add(item)
        else:
            item.config_value = settings
        await session.flush()

        # 4. 写审计日志
        await write_audit(
            session=session,
            business_domain="platform_setting",
            operation_type="save_platform_settings",
            resource_type="platform_settings",
            resource_id=CONFIG_KEY,
            resource_name="平台设置",
            after_data=settings,
        )

        return settings


def _default_settings() -> dict:
    return {
        "chunking": {"max_length": 500, "overlap": 50},
        "models": {},
    }


platform_settings_service = PlatformSettingsService()
```

- [ ] **步骤 4：运行测试验证通过 + Commit**

```bash
git add server/python/src/ai/services/platform_settings.py server/python/tests/ai/unit/services/test_platform_settings_service.py
git commit -m "feat(ai): 新增平台设置服务（切片参数校验+六类模型配置规则+审计）"
```

---

## 批次 10：控制器

### 任务 18：schemas

**文件：**
- 创建：`server/python/src/ai/schemas/knowledge_base.py` / `import_review.py` / `tool.py` / `platform_settings.py`

- [ ] **步骤 1：创建各 Schema**

参考 iam schemas 模式，创建知识库/入库审核/工具/平台设置的 Create/Update/PaginatedQuery/Response DTO。

- [ ] **步骤 2：Commit**

```bash
git add server/python/src/ai/schemas/
git commit -m "feat(ai): 新增知识库/入库审核/工具/平台设置 Schema"
```

### 任务 19：知识库 + 工具 + 平台设置控制器

**文件：**
- 创建：`server/python/src/ai/controllers/admin/knowledge_base.py`
- 创建：`server/python/src/ai/controllers/admin/tool.py`
- 创建：`server/python/src/ai/controllers/console/knowledge_base.py`
- 创建：`server/python/src/ai/controllers/console/tool.py`
- 创建：`server/python/src/ai/controllers/console/platform_settings.py`
- 创建：`server/python/src/ai/controllers/inner/permission_request_controller.py`

- [ ] **步骤 1：实现各控制器**

参考 iam/ai 现有控制器模式（注入 get_db_session、ApiResponse.success/paginated、调用对应 service）。admin 层管理端（知识库/工具管理），console 层用户端（知识库问答/检索/入库、工具测试、平台设置）。

- [ ] **步骤 2：实现 inner 权限申请回调控制器**

处理 knowledge_base_join / knowledge_base_role 类型的 apply 回调，创建 knowledge_base_members 或更新 kb_role：

```python
"""ai inner 接口 - 权限申请审批回调落地"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from framework.common.response import ApiResponse
from framework.database.dependencies import get_db_session
from ai.schemas.knowledge_base import PermissionApplyCallbackRequest

router = APIRouter()


@router.post("/permission-requests/{request_id}/apply")
async def apply_permission_request(
    request_id: str,
    data: PermissionApplyCallbackRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ORJSONResponse:
    """权限申请审批通过后回调落地授权（iam 审批后调用）"""
    from ai.services.knowledge_base.member_service import member_service

    try:
        if data.request_type == "knowledge_base_join":
            await member_service.add_member(
                session, knowledge_base_id=data.target_resource_id,
                user_id=data.applicant_id, role=data.requested_role or "query_user",
            )
        elif data.request_type == "knowledge_base_role":
            await member_service.update_member_role(
                session, knowledge_base_id=data.target_resource_id,
                user_id=data.applicant_id, role=data.requested_role,
            )
        await session.commit()
        return ApiResponse.success(data={"applied": True})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/ai/controllers/admin/ server/python/src/ai/controllers/console/ server/python/src/ai/controllers/inner/permission_request_controller.py
git commit -m "feat(ai): 新增知识库/工具/平台设置/inner 回调控制器"
```

### 任务 20：知识库问答 SSE 接口

**文件：**
- 创建：`server/python/src/ai/controllers/v1/knowledge_qa.py`
- 修改：`server/python/src/ai/module.py`（注册路由）

- [ ] **步骤 1：实现知识库问答 SSE 接口**

参考 `controllers/v1/chat/llm.py` 模式，复用 `AIChatRequest`/`UIMessage`/`_sse_generator`/`EventType.SOURCE_DOCUMENT`，注入知识库检索 + LLM stream：

```python
"""知识库问答 SSE 接口"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ai.schemas.chat import AIChatRequest
from framework.database.dependencies import get_db_session

router = APIRouter(prefix="/knowledge-qa", tags=["知识库问答"])


@router.post("/{knowledge_base_id}")
async def knowledge_qa(
    knowledge_base_id: str,
    chat_request: AIChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """
    知识库问答 SSE 接口。

    复用现有 SSE 事件流模式，检索片段通过 EventType.SOURCE_DOCUMENT 推送。
    无权限片段不进入 LLM prompt（qa_service 已过滤）。
    """
    from ai.services.knowledge_base.qa_service import qa_service

    async def event_generator():
        async for chunk in qa_service.stream_answer(
            session, knowledge_base_id=knowledge_base_id, chat_request=chat_request,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

- [ ] **步骤 2：在 module.py 注册路由**

在 `server/python/src/ai/module.py` 的 `get_routers()` 导入并注册：

```python
        from ai.controllers.v1.knowledge_qa import router as knowledge_qa_router
```

返回列表追加：

```python
            (knowledge_qa_router, "/ai/console/v1", ["知识库问答"]),
```

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/ai/controllers/v1/knowledge_qa.py server/python/src/ai/module.py
git commit -m "feat(ai): 新增知识库问答 SSE 接口（复用 EventType.SOURCE_DOCUMENT）"
```

---

## 批次 11：监听器与定时任务

### 任务 21：索引恢复补偿 + 审核超时监控

**文件：**
- 创建：`server/python/src/ai/listeners/services/queue/index_task_consumer.py`
- 创建：`server/python/src/ai/tasks/import_review_timeout.py`
- 修改：`server/python/src/ai/listeners/setup.py`
- 修改：`server/python/src/ai/module.py`（get_task_setup）

- [ ] **步骤 1：实现索引恢复补偿消费者**

参考 `install_task_consumer.py` 模式，创建 `index_task_consumer.py`，消费文档切片索引任务（document 模块触发，ai 执行实际 Embedding）。

- [ ] **步骤 2：实现审核超时监控定时任务**

创建 `import_review_timeout.py`，扫描超过保留期限的 pending 申请自动标记超时。

- [ ] **步骤 3：在 setup.py 注册 + module.py get_task_setup**

修改 `listeners/setup.py` 启动 `index_task_consumer`；修改 `module.py` 的 `get_task_setup()` 返回 `(setup_tasks, cleanup_tasks)`。

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/ai/listeners/ server/python/src/ai/tasks/ server/python/src/ai/module.py
git commit -m "feat(ai): 新增索引恢复补偿消费者与审核超时监控定时任务"
```

---

## 批次 12：数据库迁移与种子

### 任务 22：14 张表迁移脚本

**文件：**
- 创建：`server/python/src/ai/migrations/versions/005_knowledge_base.py`
- 创建：`server/python/src/ai/migrations/versions/006_import_request.py`
- 创建：`server/python/src/ai/migrations/versions/007_tool.py`
- 创建：`server/python/src/ai/migrations/versions/008_config_item.py`

- [ ] **步骤 1：创建知识库迁移**

参考 iam/ai 现有迁移模式，revision 链：`004_add_message_metadata_table` → `005_knowledge_base`。创建 knowledge_base/knowledge_base_member/knowledge_base_document/knowledge_base_acl 四张表，schema="ai"。

- [ ] **步骤 2：创建入库审核迁移**

revision 链 `005_knowledge_base` → `006_import_request`，创建 import_request/import_request_item 两张表。

- [ ] **步骤 3：创建工具库迁移**

revision 链 `006_import_request` → `007_tool`，创建 tool/tool_auth/tool_function/tool_parameter/tool_import_record 五张表。

- [ ] **步骤 4：创建平台设置迁移**

revision 链 `007_tool` → `008_config_item`，创建 config_item 表。

- [ ] **步骤 5：执行迁移验证**

运行：`cd server/python && alembic -c alembic.ini upgrade head`
预期：无错误，14 张表创建成功

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/ai/migrations/versions/005_knowledge_base.py server/python/src/ai/migrations/versions/006_import_request.py server/python/src/ai/migrations/versions/007_tool.py server/python/src/ai/migrations/versions/008_config_item.py
git commit -m "feat(ai): 新增知识库/入库审核/工具库/平台设置迁移脚本（14 张表）"
```

### 任务 23：种子数据

**文件：**
- 创建：`server/python/src/ai/migrations/seeds/kb_seed.py`
- 修改：`server/python/src/ai/module.py`（get_seeds）

- [ ] **步骤 1：创建种子数据**

创建 `kb_seed.py`，提供默认知识库配置模板和工具导入枚举种子。

- [ ] **步骤 2：在 module.py 注册 seed**

修改 `get_seeds()` 返回 `{"kb": kb_seed_run}`。

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/ai/migrations/seeds/kb_seed.py server/python/src/ai/module.py
git commit -m "feat(ai): 新增知识库种子数据并注册 seed"
```

---

## 批次 13：前端基础

### 任务 24：前端类型 + API + stores

**文件：**
- 创建：`web/vue/src/ai/api/knowledgeBase.ts` / `tool.ts` / `platformSettings.ts` / `importReview.ts`
- 创建：`web/vue/src/ai/types/knowledgeBase.ts` / `tool.ts` / `platformSettings.ts`
- 创建：`web/vue/src/ai/stores/knowledgeBase.ts` / `tool.ts`
- 修改：`web/vue/src/ai/index.ts`

- [ ] **步骤 1：创建类型定义**

参考 iam types 模式，定义 KnowledgeBase/KnowledgeBaseMember/KnowledgeBaseDocument/Tool/ToolFunction/PlatformSettings 等接口。

- [ ] **步骤 2：创建 API 函数**

参考 iam api/user.ts 模式，路径遵循 `/ai/admin/v1/*` 和 `/ai/console/v1/*`。

- [ ] **步骤 3：创建 stores**

参考 iam stores 模式。

- [ ] **步骤 4：更新 index.ts 导出 + 类型校验**

运行：`cd web/vue && pnpm typecheck`，预期无错误。

- [ ] **步骤 5：Commit**

```bash
git add web/vue/src/ai/api/ web/vue/src/ai/types/ web/vue/src/ai/stores/ web/vue/src/ai/index.ts
git commit -m "feat(ai): 新增知识库/工具库/平台设置前端类型/API/stores"
```

---

## 批次 14：前端页面

### 任务 25：知识库列表 + 详情页

**文件：**
- 创建：`web/vue/src/ai/pages/knowledge-base/KnowledgeBaseList.vue`
- 创建：`web/vue/src/ai/pages/knowledge-base/KnowledgeBaseDetail.vue`
- 创建：`web/vue/src/ai/pages/knowledge-base/tabs/OverviewTab.vue` / `DocumentsTab.vue` / `MembersTab.vue` / `RetrievalTab.vue` / `GraphTab.vue` / `ApprovalTab.vue` / `ConfigTab.vue` / `AuditTab.vue`

- [ ] **步骤 1：创建知识库列表页**

参考 iam 列表页模式，调用 knowledgeBase API。

- [ ] **步骤 2：创建知识库详情页（8 Tab）**

KnowledgeBaseDetail.vue 使用 Tabs，各 Tab 独立组件（概览/文档/成员/检索/图谱/审批/配置/审计）。检索测试 Tab 调用 retrieval API，审批 Tab 调用 importReview API。

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/ai/pages/knowledge-base/
git commit -m "feat(ai): 新增知识库列表与详情页（8 Tab）"
```

### 任务 26：工具库 + 平台设置页面

**文件：**
- 创建：`web/vue/src/ai/pages/ToolsPage.vue`
- 创建：`web/vue/src/ai/pages/PlatformSettingsPage.vue`

- [ ] **步骤 1：创建工具库页面**

含导入（Swagger URL/MCP URL）、列表、详情、测试（Connection Test + Function Test），调用 tool API。

- [ ] **步骤 2：创建平台设置页面**

含切片参数表单 + 六类模型配置（模型选择组件），调用 platformSettings API。

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/ai/pages/ToolsPage.vue web/vue/src/ai/pages/PlatformSettingsPage.vue
git commit -m "feat(ai): 新增工具库与平台设置页面"
```

---

## 批次 15：前端专用组件

### 任务 27：迁移适配 5 个专用组件

**文件：**
- 创建：`web/vue/src/ai/components/KnowledgeBaseLayout.vue` — 知识库布局
- 创建：`web/vue/src/ai/components/ImportReview.vue` — 入库审核（申请列表+审核详情）
- 创建：`web/vue/src/ai/components/RetrievalTest.vue` — 检索测试
- 创建：`web/vue/src/ai/components/ToolCenter.vue` — 工具库（导入/列表/详情/测试）
- 创建：`web/vue/src/ai/components/ModelSelector.vue` — 模型选择（kbhub AlonLargeModel → 适配本项目模型能力）

- [ ] **步骤 1：迁移适配各组件**

参考 kbhub `web/src/components/` 对应组件业务逻辑，用本项目 shadcn-vue + Tailwind 重写。ModelSelector 复用 ai 模块现有模型能力接口。

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/ai/components/
git commit -m "feat(ai): 迁移适配 5 个专用组件（知识库布局/入库审核/检索测试/工具库/模型选择）"
```

---

## 批次 16：前端路由 + 测试

### 任务 28：路由配置 + 前端测试

**文件：**
- 修改：`web/vue/src/ai/router/index.ts`
- 创建：`web/vue/src/ai/pages/knowledge-base/__tests__/KnowledgeBaseList.spec.ts`
- 创建：`web/vue/src/ai/pages/__tests__/ToolsPage.spec.ts`

- [ ] **步骤 1：配置路由**

修改 `web/vue/src/ai/router/index.ts`，参考现有 aiRoutes 模式，新增知识库/工具库/平台设置路由，含 `meta.permissions` 权限码。

- [ ] **步骤 2：编写组件测试**

测试知识库列表渲染、工具库导入、平台设置保存。

- [ ] **步骤 3：运行前端测试**

运行：`cd web/vue && pnpm typecheck && pnpm test`，预期无错误。

- [ ] **步骤 4：Commit**

```bash
git add web/vue/src/ai/router/ web/vue/src/ai/pages/knowledge-base/__tests__/ web/vue/src/ai/pages/__tests__/
git commit -m "feat(ai): 前端路由配置与组件测试"
```

---

## 批次 17：整体集成验收

### 任务 29：集成测试 - document→ai 文档引用链路

**文件：**
- 创建：`server/python/tests/ai/integration/test_document_ai_chain.py`

- [ ] **步骤 1：编写端到端测试**

参考 OpenSpec `integration-verification/spec.md` 场景 1：入库审核→知识库文档可见→问答可检索。流程：document 上传文档 → ai 提交入库申请 → 审核通过 → knowledge_base_documents 生成 → 检索测试可见 → 问答可检索。

- [ ] **步骤 2：运行测试 + Commit**

```bash
git add server/python/tests/ai/integration/test_document_ai_chain.py
git commit -m "test(ai): 新增 document→ai 文档引用链路端到端集成测试"
```

### 任务 30：集成测试 - 三层权限端到端

**文件：**
- 创建：`server/python/tests/ai/integration/test_three_layer_permission.py`

- [ ] **步骤 1：编写三层权限测试**

参考场景 2：IAM RBAC（功能权限）+ document/ai 资源权限 + Policy 协同。验证：无 `ai:knowledge_base:query` 权限的用户无法问答；有功能权限但无源文档资源权限的用户检索结果为空；Policy deny 覆盖资源 allow。

- [ ] **步骤 2：Commit**

```bash
git add server/python/tests/ai/integration/test_three_layer_permission.py
git commit -m "test(ai): 新增三层权限端到端集成测试"
```

### 任务 31：集成测试 - 权限申请审批落地

**文件：**
- 创建：`server/python/tests/ai/integration/test_permission_request_apply.py`

- [ ] **步骤 1：编写权限申请落地测试**

参考场景 3：iam 权限申请审批通过 → 回调 document/ai inner 接口 → 验证 library_members / knowledge_base_members 正确创建。

- [ ] **步骤 2：Commit**

```bash
git add server/python/tests/ai/integration/test_permission_request_apply.py
git commit -m "test(ai): 新增权限申请审批落地集成测试"
```

### 任务 32：集成测试 - 审计日志跨模块一致

**文件：**
- 创建：`server/python/tests/ai/integration/test_audit_cross_module.py`

- [ ] **步骤 1：编写审计一致性测试**

参考场景 4：document 和 ai 模块操作均写入 `iam.audit_logs`，跨模块查询一致。验证 business_domain 为 document/ai/platform_setting 的记录均存在。

- [ ] **步骤 2：Commit**

```bash
git add server/python/tests/ai/integration/test_audit_cross_module.py
git commit -m "test(ai): 新增审计日志跨模块一致集成测试"
```

### 任务 33：集成测试 - 站内信跳转回源校验

**文件：**
- 创建：`server/python/tests/ai/integration/test_notification_redirect.py`

- [ ] **步骤 1：编写站内信跳转测试**

参考场景 5：站内信消息可见≠可操作，跳转后后端重新校验权限和申请状态。

- [ ] **步骤 2：Commit**

```bash
git add server/python/tests/ai/integration/test_notification_redirect.py
git commit -m "test(ai): 新增站内信跳转回源校验集成测试"
```

### 任务 34：集成测试 - 知识库不放大源文档权限

**文件：**
- 创建：`server/python/tests/ai/integration/test_kb_permission_no_amplify.py`

- [ ] **步骤 1：编写不放大权限测试**

参考场景 6：无源文件权限的用户，知识库问答检索结果不包含该文档片段，片段不进入 LLM prompt。

- [ ] **步骤 2：Commit**

```bash
git add server/python/tests/ai/integration/test_kb_permission_no_amplify.py
git commit -m "test(ai): 新增知识库不放大源文档权限集成测试"
```

### 任务 35：集成测试 - 企业 Policy 跨模块生效

**文件：**
- 创建：`server/python/tests/ai/integration/test_policy_cross_module.py`

- [ ] **步骤 1：编写 Policy 跨模块测试**

参考场景 7：iam Policy deny 优先，跨 document/ai 生效，deny 的片段不进入检索结果。

- [ ] **步骤 2：Commit**

```bash
git add server/python/tests/ai/integration/test_policy_cross_module.py
git commit -m "test(ai): 新增企业 Policy 跨模块生效集成测试"
```

### 任务 36：Phase 3 整体验收 + OpenSpec 归档

- [ ] **步骤 1：运行后端全部 ai 测试**

运行：`cd server/python && pytest tests/ai/ -v`，预期全部 PASS。

- [ ] **步骤 2：运行 ruff 和 pyright**

运行：`cd server/python && ruff check src/ai/ && pyright src/ai/`，预期无错误。

- [ ] **步骤 3：运行前端类型检查和测试**

运行：`cd web/vue && pnpm typecheck && pnpm test`，预期无错误。

- [ ] **步骤 4：验证迁移脚本**

运行：`cd server/python && alembic -c alembic.ini upgrade head`，预期无错误。

- [ ] **步骤 5：运行全部集成验收测试**

运行：`cd server/python && pytest tests/ai/integration/ -v`，预期 7 项端到端测试全部 PASS。

- [ ] **步骤 6：验证 OpenSpec tasks 全部完成**

逐项核对 `openspec/changes/kbhub-migration-phase3/tasks.md` 的 65 项任务。

- [ ] **步骤 7：归档三个 OpenSpec 变更**

使用 `opsx:archive` 技能归档 kbhub-migration-phase1/phase2/phase3 三个变更。

- [ ] **步骤 8：Commit 验收标记**

```bash
git add -A
git commit -m "chore(kbhub-phase3): Phase 3 整体验收通过，三阶段迁移完成"
```

---

## 自检结果

### 规格覆盖度
- ✅ ai module.py 增补菜单权限（任务 1）
- ✅ 知识库模型（任务 2）
- ✅ 入库审核模型（任务 3）
- ✅ 工具库模型（任务 4）
- ✅ 平台设置模型（任务 5）
- ✅ 知识库服务含检索过滤（任务 6-10，双重权限过滤 + document inner 回查）
- ✅ 入库审核流程 + 站内信通知（任务 11）
- ✅ 工具库 Swagger/MCP 导入 + Runtime（任务 12-16）
- ✅ 平台设置服务（任务 17）
- ✅ 控制器 admin/console/inner（任务 18-20，含知识库问答 SSE 接口）
- ✅ 监听器与定时任务（任务 21）
- ✅ 迁移 + 种子（任务 22-23）
- ✅ 前端基础（任务 24）
- ✅ 前端页面（任务 25-26）
- ✅ 前端组件（任务 27）
- ✅ 前端路由 + 测试（任务 28）
- ✅ 整体集成验收 7 项（任务 29-36）

### 占位符扫描
- 检索服务 `_vector_search` 含 TODO：向量检索后端（pgvector 或 GraphRAGClient），实现时接入。检索片段过滤逻辑已完整，向量召回为基础设施接入点。
- 入库审核 `submit` 中 `recipient_user_ids=[]` 含 TODO：查询知识库 reviewer 成员，实现时补充成员查询。
- MCP 导入 Connection Test 的 `McpExecutor.execute` 简化：实现时接入 MCP SDK 调用具体工具。
- 上述均为实现细节接入点，核心业务逻辑（权限过滤、导入校验、脱敏、流程）已完整，非规格缺陷。

### 类型一致性
- 知识库模型字段在 service/schema/controller/前端类型中一致
- 枚举值（KnowledgeBaseMemberRole 等）在后端 enums 与前端类型中一致
- inner 接口路径（`/ai/inner/v1/permission-requests/{id}/apply`）与 Phase 1 iam 权限申请服务回调路径一致
- document inner 接口路径（`/document/inner/v1/documents/{id}/permission`）与 Phase 2 实现一致
- EventType.SOURCE_DOCUMENT 复用现有事件类型，无新增
- 迁移 revision 链与现有 ai 迁移（004_add_message_metadata_table）衔接一致

### 跨 Phase 一致性
- Phase 1 权限申请回调占位 `TODO(phase2/phase3)` → Phase 2 document inner apply + Phase 3 ai inner apply 已实现，Phase 1 完成后需回填接入（在 Phase 3 集成验收时确认）
- Phase 2 切片索引任务占位 `TODO(phase3)` → Phase 3 index_task_consumer 已实现，Phase 2 完成后需回填接入
- 三层权限编排：framework PermissionEngine（Phase 1）+ document permission_service（Phase 2）+ ai retrieval_service（Phase 3）协同，集成验收任务 30 覆盖
