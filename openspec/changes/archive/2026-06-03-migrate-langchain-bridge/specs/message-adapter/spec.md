# 消息适配器规范

## 新增需求

### 需求:系统支持消息类型双向转换

系统必须提供 `MessageAdapter` 类，实现 LangChain `BaseMessage` 与平台 `PromptMessage` 的双向转换。

#### 场景:创建 MessageAdapter 实例

- **当** 创建 `MessageAdapter` 实例
- **那么** 实例必须可用于双向消息转换

---

### 需求:系统支持 LangChain 到 Platform 的消息转换

系统必须实现 `to_platform_message()` 方法，将 LangChain 消息转换为平台消息。

#### 场景:转换 HumanMessage

- **当** 调用 `to_platform_message(HumanMessage(content="你好"))`
- **那么** 系统必须返回 `UserPromptMessage(content="你好")`

#### 场景:转换 AIMessage

- **当** 调用 `to_platform_message(AIMessage(content="你好！"))`
- **那么** 系统必须返回 `AssistantPromptMessage(content="你好！")`

#### 场景:转换 SystemMessage

- **当** 调用 `to_platform_message(SystemMessage(content="你是一个助手"))`
- **那么** 系统必须返回 `SystemPromptMessage(content="你是一个助手")`

#### 场景:转换消息列表

- **当** 调用 `to_platform_messages([HumanMessage(...), AIMessage(...)])`
- **那么** 系统必须返回对应的 `List[PromptMessage]`

---

### 需求:系统支持 Platform 到 LangChain 的消息转换

系统必须实现 `to_langchain_message()` 方法，将平台消息转换为 LangChain 消息。

#### 场景:转换 UserPromptMessage

- **当** 调用 `to_langchain_message(UserPromptMessage(content="你好"))`
- **那么** 系统必须返回 `HumanMessage(content="你好")`

#### 场景:转换 AssistantPromptMessage

- **当** 调用 `to_langchain_message(AssistantPromptMessage(content="你好！"))`
- **那么** 系统必须返回 `AIMessage(content="你好！")`

#### 场景:转换 SystemPromptMessage

- **当** 调用 `to_langchain_message(SystemPromptMessage(content="你是一个助手"))`
- **那么** 系统必须返回 `SystemMessage(content="你是一个助手")`

---

### 需求:系统处理不支持的消息类型

系统必须正确处理不支持的消息类型。

#### 场景:不支持的消息类型

- **当** 尝试转换不支持的消息类型（如 ToolMessage）
- **那么** 系统必须抛出 `UnsupportedMessageTypeError` 异常

#### 场景:错误消息包含类型信息

- **当** 抛出 `UnsupportedMessageTypeError`
- **那么** 异常消息必须包含不支持的消息类型名称
