# 模型 Provider 管理规范

## 新增需求

### 需求:系统支持 Provider ID 解析

系统必须支持 `<plugin_id>/<provider_type>` 格式的 Provider ID 解析。

#### 场景:解析标准格式 Provider ID

- **当** Provider ID 为 `plugin-001/openai`
- **那么** 系统必须解析为 `plugin_id="plugin-001"`, `provider_type="openai"`

#### 场景:解析无效格式 Provider ID

- **当** Provider ID 格式无效（如 `openai` 不含斜杠）
- **那么** 系统必须抛出 `ProviderIDFormatError` 异常

---

### 鈰求:系统支持 Provider 配置获取

系统必须支持根据 Provider ID 获取完整的 Provider 配置。

#### 场景:获取 Provider 配置成功

- **当** 调用 `get_provider_config(provider_id, tenant_id)`
- **那么** 系统必须返回 `ProviderConfiguration` 对象，包含凭证、模型列表、默认参数

#### 场景:Provider 不存在

- **当** 指定的 Provider ID 不存在
- **那么** 系统必须抛出 `ProviderNotFoundError` 异常

---

### 需求:系统支持凭证管理

系统必须支持模型凭证的存储、读取和缓存。

#### 场景:从数据库读取凭证

- **当** 缓存未命中
- **那么** 系统必须从数据库 `model_providers` 表读取凭证

#### 场景:凭证缓存存储

- **当** 从数据库获取凭证成功
- **那么** 系统必须将凭证存入 Redis 缓存，TTL 为 5 分钟

#### 场景:凭证更新清除缓存

- **当** Provider 凭证被更新
- **那么** 系统必须清除对应的缓存条目

---

### 需求:系统支持 Provider 工厂

系统必须提供 `ModelProviderFactory` 根据 Provider 类型创建对应的 Provider 实例。

#### 场景:创建 OpenAI Provider

- **当** Provider 类型为 `openai`
- **那么** 系统必须返回配置正确的 OpenAI Provider 实例

#### 场景:创建 Anthropic Provider

- **当** Provider 类型为 `anthropic`
- **那么** 系统必须返回配置正确的 Anthropic Provider 实例

#### 场景:不支持的 Provider 类型

- **当** Provider 类型不在支持列表中
- **那么** 系统必须抛出 `UnsupportedProviderError` 异常

---

### 需求:系统支持模型清单管理

系统必须支持查询租户可用的模型列表。

#### 场景:获取模型列表

- **当** 调用 `get_models(tenant_id)`
- **那么** 系统必须返回该租户所有可用模型的列表，包含模型名称、类型、参数限制

#### 场景:模型列表缓存

- **当** 5 分钟内重复查询模型列表
- **那么** 系统必须返回缓存的模型列表，不重复查询数据库
