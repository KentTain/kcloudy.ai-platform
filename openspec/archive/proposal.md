## 为什么

当前项目存在三个违反架构规范或性能优化的问题：

1. **AI 模块跨层访问**：`conversation.py` 和 `chat/llm.py` 直接在 Controller 层执行数据库查询，违反三层架构原则（Controller → Service → Model）
2. **Tenant 模块性能问题**：`build_tenant_vo()` 函数中 5 次 async 调用串行执行，浪费约 4 倍等待时间
3. **IAM 模块代码风格**：多处手动字典组装响应数据，可改用 Schema `from_entity()` 方法提升一致性

这些问题在上一轮 `service-layer-schema-conversion` 变更中被识别但未处理，现在需要系统性解决。

## 变更内容

### 新增

- **AI 模块 Service 层聚合方法**：
  - 创建 `ConversationService` 并提供 `list_conversations_with_message_count()` 聚合方法
  - 创建 `ChatService` 并提供会话创建、消息创建等聚合方法

- **Tenant 模块并行查询优化**：
  - 使用 `asyncio.gather` 并行化 5 次资源配置查询
  - 创建 `TenantDetailResponse` 聚合 Schema 提供 `from_tenant()` 方法

- **IAM 模块 Schema 转换方法**：
  - 添加 `UserRolesResponse` Schema 处理用户角色列表响应
  - 添加 `UserDepartmentsResponse` Schema 处理用户部门列表响应
  - 添加 `DepartmentListResponse` Schema 替代手动字典组装

### 修改

- `ai/controllers/v1/conversation.py`：移除直接数据库操作，改用 Service 调用
- `ai/controllers/v1/chat/llm.py`：移除直接数据库操作，改用 Service 调用
- `tenant/controllers/admin/tenant_controller.py`：并行化 `build_tenant_vo()` 查询
- `iam/controllers/admin/user_controller.py`：使用 Schema 转换方法替代手动字典组装
- `iam/controllers/admin/department_controller.py`：使用 Schema 转换方法替代手动字典组装

## 功能 (Capabilities)

### 新增功能

- `conversation-service`: AI 模块会话管理 Service 层，包含会话列表查询、会话创建/删除等聚合方法
- `chat-service`: AI 模块聊天 Service 层，包含消息创建、状态更新等聚合方法
- `tenant-detail-response`: 租户详情聚合响应 Schema，支持并行查询优化

### 修改功能

- `iam-admin-api`: IAM 管理端 API 响应构建方式，改用 Schema `from_entity()` 方法
- `tenant-admin-api`: 租户管理端 API 响应构建方式，优化并行查询性能

## 影响

### 受影响文件

| 模块 | 文件 | 变更类型 |
|------|------|----------|
| AI | `controllers/v1/conversation.py` | 重构 |
| AI | `controllers/v1/chat/llm.py` | 重构 |
| AI | `services/conversation_service.py` | 新增 |
| AI | `services/chat_service.py` | 新增 |
| AI | `schemas/conversation.py` | 修改 |
| Tenant | `controllers/admin/tenant_controller.py` | 优化 |
| Tenant | `schemas/admin/tenant.py` | 修改 |
| IAM | `controllers/admin/user_controller.py` | 重构 |
| IAM | `controllers/admin/department_controller.py` | 重构 |
| IAM | `schemas/user.py` | 修改 |
| IAM | `schemas/department.py` | 修改 |

### API 兼容性

- **无破坏性变更**：所有 API 端点保持不变，响应格式不变
- 内部实现优化，对外接口完全兼容

### 性能影响

- Tenant 模块租户详情查询：预计响应时间减少约 60-80%（5 次串行查询 → 并行）
- AI 模块：无性能影响，仅架构改进
