# AlonChatModel 规范

## 新增需求

### 需求:AlonChatModel 继承 BaseChatModel

系统必须提供 `AlonChatModel` 类，继承 `langchain_core.language_models.chat_models.BaseChatModel`，作为 LangChain 与平台 LLMService 的桥接层。

#### 场景:创建 AlonChatModel 实例

- **当** 使用 `model`、`provider`、`tenant_id` 参数创建 `AlonChatModel` 实例
- **那么** 实例必须正确初始化，绑定到指定租户和模型配置

#### 场景:获取模型标识

- **当** 调用 `model._llm_type` 属性
- **那么** 必须返回 `"alon-chat-model"` 字符串

---

### 需求:AlonChatModel 支持非流式调用

系统必须实现 `_agenerate()` 方法，支持非流式 LLM 调用。

#### 场景:非流式调用成功

- **当** 调用 `model._agenerate(messages)`
- **那么** 系统必须通过 `LLMService.invoke()` 发起调用并返回 `ChatResult`

#### 场景:非流式调用返回 ChatResult

- **当** 非流式调用成功
- **那么** 返回的 `ChatResult` 必须包含 `AIMessage` 和 `generation_info`（含 token 统计）

#### 场景:非流式调用失败

- **当** `LLMService.invoke()` 抛出异常
- **那么** 系统必须捕获并重新抛出为 LangChain 兼容的异常

---

### 需求:AlonChatModel 支持流式调用

系统必须实现 `_astream()` 方法，支持流式 LLM 调用。

#### 场景:流式调用返回异步迭代器

- **当** 调用 `model._astream(messages)`
- **那么** 系统必须返回 `AsyncIterator[ChatGenerationChunk]`

#### 场景:流式调用逐块返回内容

- **当** 迭代流式响应
- **那么** 每个 `ChatGenerationChunk` 必须包含 `AIMessageChunk` 内容

#### 场景:流式调用包含 token 统计

- **当** 流式调用完成
- **那么** 最后一个 chunk 的 `generation_info` 必须包含完整的 token 统计

---

### 需求:AlonChatModel 支持模型参数

系统必须支持传递模型参数到 LLMService。

#### 场景:传递 temperature 参数

- **当** 创建 `AlonChatModel(model_parameters={"temperature": 0.7})`
- **那么** 调用时必须将参数传递给 `LLMService`

#### 场景:传递 stop 序列

- **当** 调用时传入 `stop=["\n"]`
- **那么** 系统必须将 stop 参数传递给 LLMService

---

### 需求:AlonChatModel 支持租户隔离

系统必须确保不同租户的调用相互隔离。

#### 场景:绑定租户 ID

- **当** 创建 `AlonChatModel(tenant_id="tenant-001")`
- **那么** 所有调用必须在 `tenant-001` 上下文中执行

#### 场景:禁止跨租户调用

- **当** 尝试使用其他租户的凭证
- **那么** 系统必须抛出 `ModelCredentialError` 异常
