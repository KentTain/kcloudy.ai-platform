## 上下文

### 背景

项目采用三层架构（Controller → Service → Model），但在 AI 模块中存在 Controller 直接操作数据库的违规情况。同时，Tenant 模块的资源配置查询存在性能问题，IAM 模块部分代码风格需要优化。

### 当前状态

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           当前问题架构图                                     │
└─────────────────────────────────────────────────────────────────────────────┘

AI 模块（跨层问题）：
┌──────────────────┐
│  Controller      │ ─── 直接 SQL 查询 ───▶ Database
│  conversation.py │                         │
│  llm.py          │ ◀── 直接 Session 操作 ──┘
└──────────────────┘
        ❌ 违反分层原则

Tenant 模块（性能问题）：
┌──────────────────┐
│  tenant_         │     await query_1()  ──▶ 100ms
│  controller.py   │     await query_2()  ──▶ 100ms
│                  │     await query_3()  ──▶ 100ms
│  build_tenant_vo│     await query_4()  ──▶ 100ms
│                  │     await query_5()  ──▶ 100ms
└──────────────────┘
        ⚠️ 总耗时 ~500ms（串行）

IAM 模块（代码风格）：
┌──────────────────┐
│  user_controller │     data = {
│  department_     │         "id": d.id,
│  controller      │         "name": d.name,
│                  │         ...  # 手动组装
│                  │     }
└──────────────────┘
        💡 可用 Schema.from_entity() 替代
```

### 约束

- API 响应格式保持不变，确保向后兼容
- 不引入新的外部依赖
- 遵循现有 Service 单例模式
- 数据库操作使用 `async_session` 上下文管理器

## 目标 / 非目标

**目标：**

1. 修复 AI 模块跨层访问问题，将数据库操作迁移到 Service 层
2. 优化 Tenant 模块 `build_tenant_vo()` 函数，使用 `asyncio.gather` 并行查询
3. 改进 IAM 模块代码风格，使用 Schema `from_entity()` 方法替代手动字典组装

**非目标：**

- 不修改 API 端点路径或响应格式
- 不引入新的数据库表或字段
- 不修改前端代码
- 不处理 Rust/Java/.NET 等其他技术栈

## 决策

### 决策 1：AI 模块 Service 层设计

**选择方案**：创建独立的 `ConversationService` 和 `ChatService`

**理由**：
- 符合单一职责原则
- 与现有 `UserService`、`DepartmentService` 模式一致
- 便于单元测试和维护

**替代方案**：
- ❌ 将逻辑放入 `CredentialService`：职责不清
- ❌ 创建单一的 `AIService`：过于臃肿

**文件结构**：

```
ai/services/
├── __init__.py
├── credential_service.py    # 已存在
├── conversation_service.py  # 新增
├── chat_service.py          # 新增
└── plugin.py                # 已存在
```

**ConversationService 聚合方法**：

```python
class ConversationService:
    @staticmethod
    async def list_with_message_count(tenant_id: str) -> list[ConversationListItem]:
        """获取会话列表（含消息数量）- 并行查询优化"""
        
    @staticmethod
    async def get_or_create(tenant_id: str, conversation_id: str | None) -> tuple[Conversation, bool]:
        """获取或创建会话，返回 (会话, 是否新建)"""
        
    @staticmethod
    async def soft_delete(tenant_id: str, conversation_id: str) -> bool:
        """软删除会话"""
```

**ChatService 聚合方法**：

```python
class ChatService:
    @staticmethod
    async def create_messages(tenant_id: str, conversation_id: str, user_query: str, message_id: str) -> tuple[Message, Message]:
        """创建用户消息和助手消息（待响应）"""
        
    @staticmethod
    async def update_assistant_message(message_id: str, content: str, status: MessageStatus, token_count: int | None = None) -> Message:
        """更新助手消息内容和状态"""
        
    @staticmethod
    async def update_conversation_name(conversation_id: str, name: str) -> None:
        """更新会话名称"""
```

### 决策 2：Tenant 模块并行查询优化

**选择方案**：在 Controller 层使用 `asyncio.gather` 并行化

**理由**：
- 改动最小，无需修改 Service 层
- 性能提升明显（~500ms → ~100ms）
- 已有 `iam/services/user_service.py:get_user_detail()` 使用此模式

**实现方式**：

```python
# 改造前（串行）
db_ref = await _get_resource_ref(tenant.db_config_id, DatabaseConfigService)
storage_ref = await _get_resource_ref(tenant.storage_config_id, StorageConfigService)
cache_ref = await _get_resource_ref(tenant.cache_config_id, CacheConfigService)
queue_ref = await _get_resource_ref(tenant.queue_config_id, QueueConfigService)
pubsub_ref = await _get_resource_ref(tenant.pubsub_config_id, PubSubConfigService)

# 改造后（并行）
db_ref, storage_ref, cache_ref, queue_ref, pubsub_ref = await asyncio.gather(
    _get_resource_ref(tenant.db_config_id, DatabaseConfigService),
    _get_resource_ref(tenant.storage_config_id, StorageConfigService),
    _get_resource_ref(tenant.cache_config_id, CacheConfigService),
    _get_resource_ref(tenant.queue_config_id, QueueConfigService),
    _get_resource_ref(tenant.pubsub_config_id, PubSubConfigService),
)
```

**替代方案**：
- ❌ 创建 `TenantDetailService.get_tenant_detail()` 聚合方法：过度设计，当前函数已足够清晰
- ❌ 使用 `asyncio.TaskGroup` (Python 3.11+)：`gather` 已满足需求

### 决策 3：IAM 模块 Schema 转换方法

**选择方案**：添加专用响应 Schema 和 `from_entity()` 方法

**理由**：
- 与已实现的 `UserDetailResponse.from_user()` 模式一致
- 提供类型安全保障
- 便于 IDE 自动补全

**新增 Schema**：

```python
# iam/schemas/user.py

class UserRoleItem(BaseModel):
    """用户角色项"""
    id: str
    code: str
    name: str
    description: str | None = None

    @classmethod
    def from_role(cls, role: "Role") -> "UserRoleItem":
        return cls(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
        )

class UserRolesResponse(BaseModel):
    """用户角色列表响应"""
    roles: list[UserRoleItem] = Field(default_factory=list)

    @classmethod
    def from_roles(cls, roles: list["Role"]) -> "UserRolesResponse":
        return cls(roles=[UserRoleItem.from_role(r) for r in roles])

# iam/schemas/department.py

class DepartmentListItem(BaseModel):
    """部门列表项"""
    id: str
    name: str
    code: str | None = None
    parent_id: str | None = None
    sort_order: int = 0
    leader_id: str | None = None
    status: str = "active"

    @classmethod
    def from_department(cls, dept: "Department") -> "DepartmentListItem":
        return cls(
            id=dept.id,
            name=dept.name,
            code=dept.code,
            parent_id=dept.parent_id,
            sort_order=dept.sort_order,
            leader_id=dept.leader_id,
            status=dept.status,
        )

class DepartmentListResponse(BaseModel):
    """部门列表响应"""
    items: list[DepartmentListItem] = Field(default_factory=list)

    @classmethod
    def from_departments(cls, departments: list["Department"]) -> "DepartmentListResponse":
        return cls(items=[DepartmentListItem.from_department(d) for d in departments])
```

**替代方案**：
- ❌ 使用 `model_config = ConfigDict(from_attributes=True)`：无法处理字段重命名和计算字段
- ❌ 保持现状：代码风格不一致

## 风险 / 权衡

### 风险 1：AI 模块重构可能影响流式响应

**风险描述**：`llm.py` 的流式响应逻辑复杂，重构可能导致 SSE 事件丢失或顺序错误。

**缓解措施**：
- 保持流式响应逻辑在 Controller 层
- Service 层只处理数据库 CRUD 操作
- 添加单元测试验证流式响应完整性

### 风险 2：并行查询可能增加数据库连接压力

**风险描述**：Tenant 模块 5 个并行查询可能同时占用 5 个数据库连接。

**缓解措施**：
- 当前连接池配置足够（默认 10 个连接）
- 查询均为简单主键查询，执行时间极短（<10ms）
- 如需进一步优化，可考虑批量查询接口

### 风险 3：Schema 转换方法可能导致循环导入

**风险描述**：`from_entity()` 方法中引用 Model 类型可能导致循环导入。

**缓解措施**：
- 使用 `from __future__ import annotations` 支持前向引用
- 使用 `TYPE_CHECKING` 条件导入
- 遵循现有 `UserDetailResponse` 的实现模式

## 迁移计划

### 阶段 1：Tenant 模块优化（低风险）

1. 修改 `build_tenant_vo()` 使用 `asyncio.gather`
2. 修改 `get_tenant_resources()` 和 `update_tenant_resources()` 同理
3. 运行现有测试验证

### 阶段 2：IAM 模块代码风格改进（低风险）

1. 添加 `UserRoleItem`、`UserRolesResponse` Schema
2. 添加 `DepartmentListItem`、`DepartmentListResponse` Schema
3. 修改 Controller 使用新 Schema
4. 运行现有测试验证

### 阶段 3：AI 模块重构（中风险）

1. 创建 `ConversationService` 及其聚合方法
2. 创建 `ChatService` 及其聚合方法
3. 重构 `conversation.py` Controller
4. 重构 `llm.py` Controller
5. 添加单元测试
6. 手动测试流式响应

### 回滚策略

每个阶段独立提交，如发现问题可单独回滚：

```
git revert <commit-hash>
```

## 开放问题

1. **ChatService 是否需要事务支持？**
   - 当前设计使用独立的 `async_session`，每个操作是独立事务
   - 如需跨操作事务，需传入 `session` 参数
   - 建议：保持当前设计，按需扩展

2. **是否需要为并行查询添加超时控制？**
   - 当前实现无超时限制
   - 如单个查询卡住，会影响整体响应时间
   - 建议：暂不添加，监控后再决定

3. **DepartmentListItem 是否需要包含 leader 信息？**
   - 当前返回 `leader_id`，前端可能需要 `leader_name`
   - 建议：保持当前设计，按需扩展（需要关联查询 User 表）
