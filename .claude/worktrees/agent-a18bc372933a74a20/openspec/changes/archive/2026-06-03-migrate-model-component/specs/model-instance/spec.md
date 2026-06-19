# 模型实例管理规范

## 新增需求

### 需求:系统支持创建模型实例

系统必须提供 `ModelInstanceFactory` 根据模型配置创建模型实例。

#### 场景:创建模型实例

- **当** 调用 `get_model_instance(model_config, provider_config)`
- **那么** 系统必须返回配置正确的 `LargeLanguageModel` 实例

#### 场景:模型实例绑定插件

- **当** 创建模型实例时
- **那么** 实例必须绑定到指定的插件 ID，通过 `ModelClient` 通信

---

### 需求:模型实例支持 LLM 调用

`LargeLanguageModel` 实例必须支持 invoke 和 stream 两种调用模式。

#### 场景:实例调用 invoke

- **当** 调用 `model_instance.invoke(prompt_messages)`
- **那么** 实例必须通过 `ModelClient.invoke_llm()` 发起调用并返回 `LLMResult`

#### 场景:实例调用 stream

- **当** 调用 `model_instance.stream(prompt_messages)`
- **那么** 实例必须通过 `ModelClient.invoke_llm()` 发起流式调用并返回 `AsyncIterator[LLMResultChunk]`

---

### 需求:模型实例支持参数传递

模型实例必须支持传递调用参数。

#### 场景:传递调用参数

- **当** 调用时传入 `model_parameters` 和 `user_id`
- **那么** 实例必须将参数正确传递给 `ModelClient`

---

### 需求:系统支持大语言模型基类

系统必须提供 `LargeLanguageModel` 基类作为所有 LLM Provider 的统一抽象。

#### 场景:基类定义接口

- **当** 继承 `LargeLanguageModel` 基类
- **那么** 子类必须实现 `invoke` 和 `stream` 方法

#### 场景:基类提供通用逻辑

- **当** 使用基类方法
- **那么** 基类必须提供凭证处理、错误转换、日志记录等通用逻辑

---

### 需求:模型实例支持错误处理

模型实例必须正确处理和转换底层错误。

#### 场景:插件通信错误

- **当** `ModelClient` 抛出 `PluginError`
- **那么** 模型实例必须转换为 `ModelInvocationError`

#### 场景:超时错误

- **当** 调用超过配置的超时时间
- **那么** 模型实例必须抛出 `ModelTimeoutError`

#### 场景:凭证错误

- **当** 凭证无效或过期
- **那么** 模型实例必须抛出 `ModelCredentialError`
