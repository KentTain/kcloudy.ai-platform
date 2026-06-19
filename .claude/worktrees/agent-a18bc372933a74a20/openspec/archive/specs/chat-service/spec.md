## 新增需求

### 需求: 消息创建聚合方法

系统 SHALL 提供 `ChatService.create_messages()` 聚合方法，一次性创建用户消息和助手消息（待响应状态）。

#### 场景: 成功创建消息对
- **当** 调用 `create_messages(tenant_id, conversation_id, user_query, message_id)`
- **那么** 创建两条消息：用户消息（状态为 PENDING）和助手消息（状态为 PENDING），返回消息元组

#### 场景: 消息关联正确的会话
- **当** 创建消息时
- **那么** 消息的 `conversation_id`、`tenant_id`、`app_id` 必须正确关联

### 需求: 消息状态更新聚合方法

系统 SHALL 提供 `ChatService.update_assistant_message()` 聚合方法，更新助手消息内容、状态和 Token 统计。

#### 场景: 成功更新消息
- **当** 调用 `update_assistant_message(message_id, content, status, token_count)`
- **那么** 消息内容、状态和 Token 统计更新成功

#### 场景: 记录错误信息
- **当** 状态为 ERROR 时
- **那么** 错误信息记录到 `message_metadata` 字段

### 需求: 会话名称更新聚合方法

系统 SHALL 提供 `ChatService.update_conversation_name()` 聚合方法，更新会话显示名称。

#### 场景: 成功更新会话名称
- **当** 调用 `update_conversation_name(conversation_id, name)`
- **那么** 会话名称更新成功

### 需求: Service 层禁止跨层操作

`ChatService` 禁止直接操作数据库 Session，必须通过 Model 层的方法执行数据库操作。

#### 场景: 使用 Model 层方法
- **当** Service 需要查询或修改数据
- **那么** 必须调用 Model 的类方法（如 `session.get()`、`Model.update_by_id()`）

## 修改需求

无

## 移除需求

无
