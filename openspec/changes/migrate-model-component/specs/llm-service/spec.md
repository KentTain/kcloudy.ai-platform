# LLM 服务规范

## 新增需求

### 需求:LLM 服务提供统一调用门面

系统必须提供 `LLMService` 类作为 LLM 调用的统一入口，支持租户隔离和流式响应。

#### 场景:创建 LLMService 实例

- **当** 使用 `tenant_id` 创建 `LLMService` 实例
- **那么** 实例必须绑定到指定租户，所有调用在该租户上下文中执行

#### 场景:获取单例实例

- **当** 多次调用 `LLMService(tenant_id)` 创建实例
- **那么** 相同 `tenant_id` 必须返回相同实例（单例模式）

---

### 需求:LLM 服务支持非流式调用

系统必须支持通过 `invoke` 方法进行非流式 LLM 调用。

#### 场景:非流式调用成功

- **当** 调用 `LLMService.invoke(prompt_messages, model, provider)`
- **那么** 系统必须返回完整的 `LLMResult` 对象，包含 `message.content` 和 `usage` 统计

#### 场景:非流式调用失败

- **当** 模型插件不可用或凭证无效
- **那么** 系统必须抛出 `ModelInvocationError` 异常，包含错误详情

---

### 需求:LLM 服务支持流式调用

系统必须支持通过 `stream` 方法进行流式 LLM 调用。

#### 场景:流式调用返回异步迭代器

- **当** 调用 `LLMService.stream(prompt_messages, model, provider)`
- **那么** 系统必须返回 `AsyncIterator[LLMResultChunk]`，逐块返回生成内容

#### 场景:流式调用包含 usage 统计

- **当** 流式调用完成
- **那么** 最后一个 chunk 必须包含完整的 `usage` 统计（prompt_tokens, completion_tokens, total_tokens）

#### 场景:流式调用可被中断

- **当** 消费者提前退出迭代
- **那么** 系统必须正确关闭底层连接，不残留资源

---

### 需求:LLM 服务支持模型参数配置

系统必须支持传递模型参数（temperature、max_tokens 等）到 LLM 调用。

#### 场景:传递模型参数

- **当** 调用时传入 `model_parameters={"temperature": 0.7, "max_tokens": 1000}`
- **那么** 系统必须将参数传递给模型插件

#### 场景:参数校验

- **当** 传入无效的模型参数
- **那么** 系统必须抛出 `ModelParameterError` 异常

---

### 需求:LLM 服务支持凭证缓存

系统必须缓存模型凭证以减少数据库查询。

#### 场景:凭证缓存命中

- **当** 5 分钟内重复调用相同 Provider
- **那么** 系统必须从缓存获取凭证，不查询数据库

#### 场景:凭证缓存失效

- **当** 缓存过期或调用失败
- **那么** 系统必须重新从数据库获取凭证并更新缓存

#### 场景:多租户凭证隔离

- **当** 不同租户调用相同 Provider
- **那么** 系统必须使用各自租户的凭证，禁止跨租户访问
