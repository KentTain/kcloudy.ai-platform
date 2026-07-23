# kbhub 迁移实现设计

> 日期：2026-07-23
> 依据：`docs/requirements/12.Alon知识库迁移方案.md` + OpenSpec 变更（Phase 1/2/3）

---

## 1. 整体架构与执行策略

### 1.1 执行模式

**严格顺序** Phase 1→2→3，每个 Phase 内**逐批增量**实现 + 验证 + commit。

### 1.2 跨 Phase 一致性约束

| 约束 | 说明 |
|------|------|
| 后端模式统一 | ModuleDefinition 声明 → BaseModel+Mixin 模型 → static 服务方法 → admin/console/inner 三层控制器 |
| 前端模式统一 | ModuleDescriptor → api/ → types/ → stores/ → pages/ → components/ → router/ |
| API 路径规范 | `/{module}/{admin\|console\|inner}/v1/{resource}` |
| 权限码规范 | `{module}:{resource}:{action}`，在 module.py 的 PermissionDef 中声明 |
| 审计接入 | 所有写操作通过 `@audit_log` 装饰器或 `write_audit` 辅助记录 |
| 软删除 | 所有业务模型混入 ActiveRecordMixin，使用 `deleted_at` 软删除 |
| 多租户 | 所有业务模型混入 TenantMixin，查询自动注入 `tenant_id` 过滤 |

### 1.3 迁移实现核心方法

1. **参考 kbhub 源码精简迁移**：读取源码理解业务逻辑，剔除 Alon 平台特有依赖（BaseExtension、alon.models.events 等），替换为 framework 机制
2. **不逐行移植**：以 spec 场景为驱动，理解意图后用本项目模式重写
3. **kbhub 巨型文件拆分**：如 permission.py 7.8万行 → document 多个服务文件

### 1.4 前置条件

| 条件 | 状态 |
|------|------|
| kbhub 源码本地可访问 | ✅ |
| MinIO 已就绪 | ✅ |
| 外部依赖（prance/openapi-spec-validator/MCP SDK） | Phase 3 时安装 |

---

## 2. Phase 1 实现设计 — 基础设施 + iam 扩展

### 2.1 任务批次

| 批次 | 内容 | 关键实现点 | 验证 |
|------|------|-----------|------|
| 1 | 文档准备 | 更新 6 个 CLAUDE.md | 文档与目录一致 |
| 2 | framework 权限引擎 | `permission/engine.py`（Protocol 接口）、`permission/policy_evaluator.py`（JSON 条件匹配）、`permission/audit_writer.py`（延迟导入 iam） | 单元测试 |
| 3 | framework 站内信辅助 | `notification/sender.py`（延迟导入 iam Notification） | 单元测试 |
| 4 | iam 站内信 | Notification/NotificationRead 模型 + 服务 + admin/console 控制器 | 接口测试 |
| 5 | iam 权限申请 | PermissionRequest/PermissionCacheEvent 模型 + 服务（含审批回调 inner 接口）+ admin/console 控制器 | 接口测试 |
| 6 | iam Policy | Policy 模型 + 服务 + admin 控制器 | 接口测试 |
| 7 | iam 组织/用户增强 + 迁移 | 增强 organization_service/user_service + 5 张表迁移 + 种子数据 | 迁移可执行 |
| 8 | iam 前端 | 3 页面 + 2 组件迁移适配 | E2E |

### 2.2 关键设计决策

1. **framework 延迟导入**：`audit_writer.py` 和 `sender.py` 在函数内延迟导入 iam 模型，避免 framework → iam 循环依赖
2. **权限引擎 Protocol 接口**：定义 `PermissionEngineProtocol`，各业务模块实现具体判定逻辑，framework 只编排调用顺序
3. **Policy 条件用 JSON 结构化**：`{"field": "resource_type", "op": "eq", "value": "document"}` 格式，支持 and/or 组合
4. **权限申请回调**：iam 审批通过后调用业务模块 inner 接口落地授权

### 2.3 新增文件清单

**framework**：
- `permission/engine.py` — 权限判定引擎接口
- `permission/policy_evaluator.py` — Policy 求值器
- `permission/audit_writer.py` — 审计写入辅助
- `notification/sender.py` — 站内信发送辅助

**iam**：
- `models/notification.py` — Notification/NotificationRead
- `models/permission_request.py` — PermissionRequest/PermissionCacheEvent
- `models/policy.py` — Policy
- `schemas/notification.py`、`schemas/permission_request.py`、`schemas/policy.py`
- `services/notification_service.py`、`services/permission_request_service.py`、`services/policy_service.py`
- `controllers/admin/notification_controller.py`、`controllers/admin/permission_request_controller.py`、`controllers/admin/policy_controller.py`
- `controllers/console/notification_controller.py`、`controllers/console/permission_request_controller.py`

**前端 iam**：
- `pages/notifications.vue`、`pages/permission-requests.vue`、`pages/policies.vue`
- 组件：站内信组件、权限排障面板

---

## 3. Phase 2 实现设计 — document 模块

### 3.1 任务批次

| 批次 | 内容 | 关键实现点 | 验证 |
|------|------|-----------|------|
| 1 | 模块声明 + 基础模型 | `module.py` + Library/LibraryMember/Folder/Document/DocumentVersion + enums | 权限码同步 |
| 2 | 权限模型 | LibraryRole/LibraryRoleMember/ResourceAcl | 模型可映射 |
| 3 | 标签+人设模型 | Tag/TagGroup/Persona | 模型可映射 |
| 4 | 元数据模型 | ResourceMetadata/LibraryMetadataField | 模型可映射 |
| 5 | 权限判定引擎 | `permission_service.py`：owner/admin → 全员+权限组+直授权 → 继承链 → Policy | 单元测试 |
| 6 | 业务服务 | library/folder/document/member/permission_config/tag/persona/recycle/metadata | 单元测试 |
| 7 | 控制器 + schemas | admin/console/inner + DTO | 接口测试 |
| 8 | 任务+监听 | document_index_task + listeners | 可调度 |
| 9 | 迁移+种子 | 16 张表 + 种子数据 | 迁移可执行 |
| 10 | 审计接入 | 各写操作加 `@audit_log` | 审计写入正确 |
| 11 | 前端基础 | api/types/stores/composables | 类型校验 |
| 12 | 前端页面 | 文档库列表+详情、标签管理、人设管理 | 联调通过 |
| 13 | 前端组件 | 布局/文件详情/目录树/成员选择器/权限配置/标签选择器/人设编辑器/审计展示 | 复用 UI 规范 |
| 14 | 前端路由+权限+测试 | router + 权限码 + 单元测试 + E2E | 测试通过 |

### 3.2 关键设计决策

1. **Folder 用 TreeNodeMixin**：`parent_id` 不加外键，树操作用内置方法
2. **权限继承链**：文档库根 → 目录 → 文件，沿 `parent_ids` 计算，支持关闭/重新开启继承
3. **inner 接口**：`GET /document/inner/v1/documents/{id}/permission` + `GET /document/inner/v1/libraries/{id}/members`，无认证
4. **文档切片索引**：document 触发任务 + 记录状态，实际切片由 ai 模块执行
5. **文件存储**：对接 MinIO
6. **kbhub 源码参考**：精简重写 permission_service.py（预计 500-800 行 vs 原始 7.8 万行）

### 3.3 新增文件清单

**document 后端**：
- `module.py` — ModuleDefinition
- `models/library.py`、`models/folder.py`、`models/document.py`、`models/permission.py`、`models/tag.py`、`models/persona.py`、`models/metadata.py`、`models/enums.py`
- `services/library_service.py`、`services/folder_service.py`、`services/document_service.py`、`services/member_service.py`、`services/permission_service.py`、`services/permission_config_service.py`、`services/tag_service.py`、`services/persona_service.py`、`services/recycle_service.py`、`services/metadata_service.py`
- `controllers/admin/`、`controllers/console/`、`controllers/inner/`
- `tasks/document_index_task.py`、`listeners/`
- `migrations/`

**document 前端**：
- `api/`、`types/`、`stores/`、`composables/`
- `pages/library/`、`pages/tags.vue`、`pages/personas.vue`
- `components/`（8 个迁移适配组件）
- `router/`

---

## 4. Phase 3 实现设计 — ai 模块 + 集成验收

### 4.1 任务批次

| 批次 | 内容 | 关键实现点 | 验证 |
|------|------|-----------|------|
| 1 | 模块声明增补 | ai `module.py` 增补菜单+PermissionDef | 权限码同步 |
| 2 | 知识库模型 | KnowledgeBase/Member/Document/Acl + enums | 模型可映射 |
| 3 | 入库审核模型 | ImportRequest/ImportRequestItem | 模型可映射 |
| 4 | 工具库模型 | Tool/ToolAuth/ToolFunction/ToolParameter/ToolImportRecord | 模型可映射 |
| 5 | 平台设置模型 | ConfigItem | 模型可映射 |
| 6 | 知识库服务 | CRUD + 成员权限 + 检索过滤 + 问答（双重权限过滤 + document inner 回查） | 单元测试 |
| 7 | 入库审核服务 | 申请提交 → 站内信通知 → 审核通过生成引用 | 流程测试 |
| 8 | 工具库服务 | Swagger导入 + MCP导入 + Runtime + 重导入 + 脱敏 | 导入测试 |
| 9 | 平台设置服务 | 切片参数 + 六类模型配置 + 参数校验 | 服务测试 |
| 10 | 控制器 + schemas | admin/console/inner | 接口测试 |
| 11 | 监听器+定时任务 | 入库审核消息 + 索引恢复补偿 + 审核超时监控 | 可调度 |
| 12 | 迁移+种子 | 14 张表 + 种子数据 | 迁移可执行 |
| 13 | 前端基础 | api/types/stores 增补 | 类型校验 |
| 14 | 前端页面 | 知识库列表+详情、工具库、平台设置、智能问答 | 联调通过 |
| 15 | 前端组件 | 知识库布局/入库审核/检索测试/工具库/模型选择 | 复用 UI 规范 |
| 16 | 前端测试 | 单元测试 + E2E | 测试通过 |
| 17 | 集成验收 | 7 项端到端验证 | 全部通过 |

### 4.2 关键设计决策

1. **知识库问答不放大权限**：检索前后双重过滤，无权限片段不进入 LLM prompt；回查走 document inner 接口
2. **工具库统一 Runtime**：按 `Tool.protocol` 分发 HttpExecutor/McpExecutor
3. **工具库统一模型**：不区分 Swagger/MCP，protocol 字段区分
4. **重导入策略**：保留 Tool+ToolAuth，删除 Function+Parameter 重建，恢复人工编辑字段
5. **平台设置存储**：保存到 `ai.config_items`（`config_scope=tenant`，`config_key=kbhub_platform_settings`）
6. **智能问答复用 ai-elements**：使用现有 Conversation/Message 模型和对话 UI 组件

### 4.3 新增文件清单

**ai 后端**：
- `models/knowledge_base.py`、`models/import_request.py`、`models/tool.py`、`models/config_item.py`、`models/enums.py`（增补）
- `services/knowledge_base/kb_service.py`、`services/knowledge_base/member_service.py`、`services/knowledge_base/document_service.py`、`services/knowledge_base/retrieval_service.py`、`services/knowledge_base/chat_service.py`
- `services/import_review/import_service.py`
- `services/tool/tool_service.py`、`services/tool/swagger_import.py`、`services/tool/mcp_import.py`、`services/tool/tool_runtime.py`
- `services/platform_settings.py`
- `controllers/admin/knowledge_base.py`、`controllers/console/knowledge_base.py`、`controllers/admin/tool.py`、`controllers/console/tool.py`、`controllers/console/platform_settings.py`、`controllers/inner/`
- `listeners/`、`tasks/`
- `migrations/`

**ai 前端**：
- `api/`（增补）、`types/`（增补）、`stores/`（增补）
- `pages/knowledge-base/`、`pages/tools.vue`、`pages/platform-settings.vue`
- `components/`（5 个迁移适配组件）

### 4.4 集成验收项

| # | 验证项 | 方法 |
|---|--------|------|
| 1 | document→ai 文档引用链路 | 入库审核→知识库文档可见→问答可检索 |
| 2 | 三层权限协同 | RBAC+资源权限+Policy 端到端 |
| 3 | 权限申请审批落地 | iam→document/ai 回调授权 |
| 4 | 审计日志跨模块一致 | 各模块操作均出现在 iam.audit_logs |
| 5 | 站内信跳转回源校验 | 后端重新校验权限和申请状态 |
| 6 | 知识库不放大权限 | 无权限片段不进入检索上下文和 LLM prompt |
| 7 | Policy 跨模块生效 | deny 优先，片段不进入检索结果 |

---

## 5. 风险与对策

| 风险 | 对策 |
|------|------|
| kbhub 巨型文件迁移遗漏 Alon 特有逻辑 | 以 spec 场景为驱动，不逐行移植；每批完成后对照 spec 验证 |
| 权限判定引擎复杂度 | 精简实现，单元测试覆盖所有判定路径 |
| framework→iam 循环依赖 | 延迟导入 + Protocol 接口 |
| 工具库外部依赖不稳定 | 校验前置、超时控制、重导入失败回滚 |
| 知识库放大源文档权限 | 检索前后双重过滤 + document inner 回查 + 集成验证 |
| 跨模块联调（document↔ai） | Phase 2 inner 接口先行稳定，Phase 3 集成验证覆盖 |
