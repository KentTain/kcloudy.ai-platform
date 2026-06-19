# conversation-service 规范

## 目的
待定 - 由归档变更 service-layer-optimization 创建。归档后请更新目的。
## 需求
### 需求: 会话列表查询聚合方法

系统 SHALL 提供 `ConversationService.list_with_message_count()` 聚合方法，返回包含消息数量的会话列表。

#### 场景: 成功获取会话列表
- **当** 调用 `list_with_message_count(tenant_id)` 方法
- **那么** 返回当前租户所有未删除会话，每个会话包含消息数量

#### 场景: 空租户返回空列表
- **当** 租户没有任何会话
- **那么** 返回空列表

### 需求: 会话获取或创建聚合方法

系统 SHALL 提供 `ConversationService.get_or_create()` 聚合方法，支持获取已有会话或创建新会话。

#### 场景: 获取已有会话
- **当** 调用 `get_or_create(tenant_id, conversation_id)` 且会话已存在
- **那么** 返回 `(conversation, False)` 表示未新建

#### 场景: 创建新会话
- **当** 调用 `get_or_create(tenant_id, None)` 或会话不存在
- **那么** 创建新会话并返回 `(conversation, True)` 表示新建

### 需求: 会话软删除聚合方法

系统 SHALL 提供 `ConversationService.soft_delete()` 聚合方法，将会话状态设为 DELETED。

#### 场景: 成功软删除会话
- **当** 调用 `soft_delete(tenant_id, conversation_id)` 且会话存在
- **那么** 会话状态变为 DELETED，返回 True

#### 场景: 会话不存在
- **当** 调用 `soft_delete(tenant_id, conversation_id)` 且会话不存在
- **那么** 返回 False

### 需求: 会话更新聚合方法

系统 SHALL 提供 `ConversationService.update_name()` 聚合方法，更新会话名称。

#### 场景: 成功更新会话名称
- **当** 调用 `update_name(conversation_id, new_name)` 且会话存在
- **那么** 会话名称更新成功

### 需求: Service 层禁止跨层操作

`ConversationService` 禁止直接操作数据库 Session，必须通过 Model 层的方法执行数据库操作。

#### 场景: 使用 Model 层方法
- **当** Service 需要查询或修改数据
- **那么** 必须调用 Model 的类方法（如 `Model.one_by_conditions()`、`Model.update_by_id()`）

