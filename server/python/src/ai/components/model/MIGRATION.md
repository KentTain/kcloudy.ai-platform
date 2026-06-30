# Model 组件迁移日志

本文档记录 Model 组件从 Alon 平台迁移到 AI Platform 的过程和差异。

## 迁移来源

- **源项目**：Alon（`D:\Project\ai\Alon\packages\platform`）
- **源路径前缀**：`src/alon/components/model/`
- **目标路径前缀**：`src/ai/components/model/`
- **迁移时间**：2025 年

## 导入路径替换

迁移时批量替换了所有导入路径：

| Alon 导入路径 | 目标导入路径 |
|---------------|--------------|
| `from alon.components.model.` | `from ai.components.model.` |
| `from alon_plugin.sdk.entities.` | `from ai_plugin.sdk.entities.` |
| `from alon.configs.settings` | `from framework.configs.settings` |
| `from alon.common.ctx` | `from framework.common.ctx` |
| `from alon.common.exceptions` | `from framework.common.exceptions` |
| `from alon.models.core.engine` | `from framework.database.core.engine` |
| `from alon.components.plugin.client.model_client` | `from ai.components.plugin.client.model_client` |
| `from alon.extensions.ext_redis` | `from framework.cache.redis_util` |

## 与 Alon 的差异

### 1. 缓存适配

Alon 直接使用 `ext_redis.redis_client` 操作 Redis；本项目中改为使用 `framework/cache/` 提供的 `TenantCacheManager`。

```python
# Alon
from alon.extensions.ext_redis import redis_client
await redis_client.get(cache_key)

# AI Platform
from framework.cache.tenant_cache_manager import get_cache_manager
cache_manager = get_cache_manager()
await cache_manager.get(cache_key, tenant_id=tenant_id)
```

`ProviderManager.get_configurations()` 的缓存逻辑已适配 `TenantCacheManager` 接口，包含：

- 缓存键格式：`model_provider_configurations:{tenant_id}`
- 序列化：`ProviderConfigurations.to_dict()` -> dict
- 反序列化：`ProviderConfigurations.from_dict(data, provider_entities)` -> ProviderConfigurations
- TTL：3600 秒

### 2. 加密适配

Alon 使用 `alon.components.model.internal.helper.encrypter` 模块；本项目改为使用 `framework/utils/crypto/`。

```python
# Alon
from alon.components.model.internal.helper.encrypter import encrypt_token, decrypt_token

# AI Platform
from framework.utils.crypto import encrypt, decrypt
```

### 3. 上下文适配

Alon 使用 `alon.common.ctx` 中的上下文变量；本项目改为使用 `framework/common/ctx/` 提供的函数式接口。

```python
# Alon
from alon.common.ctx import CTX_TENANT_ID, CTX_USER_ID
tenant_id = CTX_TENANT_ID.get()

# AI Platform
from framework.common.ctx import get_tenant_id, get_user_id
tenant_id = get_tenant_id()
```

### 4. 新增的异常类

迁移过程中新增了以下 Alon 中没有的异常类（`errors/error.py`）：

| 异常类 | 说明 |
|--------|------|
| `ProviderNotFoundError` | Provider 不存在 |
| `UnsupportedProviderError` | 不支持的 Provider 类型 |
| `ModelInvocationError` | 模型调用错误（插件通信失败） |
| `ModelTimeoutError` | 模型调用超时 |
| `ModelCredentialError` | 模型凭证无效或缺失 |
| `ModelParameterError` | 无效的模型参数 |

Alon 原有的 `ProviderTokenNotInitError` 保持不变。

### 5. 缓存序列化实现

Alon 的 `ProviderConfigurations` 依赖 SQLAlchemy ORM 对象序列化，缓存的是完整 ORM 对象。本项目改为纯 dict 序列化/反序列化：

- `to_dict()`：将配置序列化为可 JSON 化的字典
- `from_dict(data, provider_entities)`：从字典 + ProviderEntity 字典重建配置对象

### 6. Provider ID 独立模块

Alon 中 Provider ID 相关类散布在 `plugin/entities/plugin.py`；本项目将其独立为 `schema/provider_id.py`，包含：

- `GenericProviderID`：通用 Provider ID（格式：`组织/插件名/提供者名`）
- `ModelProviderID`：模型 Provider ID（支持简化格式自动转换）
- `ToolProviderID`：工具 Provider ID（含工具提供者映射）
- `ProviderIDFormatError`：格式错误异常

### 7. entities 目录拆分

Alon 的 `entities/` 目录同时包含公共实体和内部实体。本项目拆分为：

- `schema/`：公共 Schema 定义（`model_entities.py`、`provider_id.py`）
- `internal/entities/`：内部实体定义（`provider_entities.py`）

### 8. 单例模式调整

`LLMService` 在 Alon 中使用模块级变量实现单例；本项目改为 `WeakValueDictionary`，避免内存泄漏：

```python
# Alon：模块级 dict，需手动清理
_instances: dict[str, LLMService] = {}

# AI Platform：WeakValueDictionary，自动清理无引用实例
_instances: WeakValueDictionary[str, LLMService] = WeakValueDictionary()
```

## 未迁移的功能

以下功能按原计划暂不迁移，待业务需求驱动时再实现：

| 功能 | Alon 路径 | 说明 |
|------|-----------|------|
| Schema 验证器 | schema_validators/ | Provider/Model 凭证 Schema 验证 |
| SSRF 代理 | internal/helper/ssrf_proxy.py | 深度依赖 alon_config，当前无 HTTP 出站场景 |
| Model Manager | model_manager.py | 旧版模型管理入口，已由 LLMService + ManagementService 替代 |

## 二次迁移差异（2026-06-03）

以下功能在二次迁移中完成，与 Alon 存在以下差异：

### 1. EmbeddingService 缓存配置

Alon 通过 KnowledgeEmbeddingSettings 从配置文件加载缓存参数；本项目改为构造参数默认值，避免引入 Alon 的业务配置依赖。

`python

# Alon

class EmbeddingService(BaseModelService):
    def **init**(self, tenant_id: str):
        embedding_settings = settings.knowledge.embedding
        self._cache_enabled = embedding_settings.cache_enabled
        self._max_cache_size = embedding_settings.cache_size

# AI Platform

class EmbeddingService(BaseModelService):
    def **init**(self, tenant_id: str, cache_enabled: bool = True,
                 cache_size: int = 2000, log_cache_details: bool = False):
        super().**init**(tenant_id)
        self._cache_enabled = cache_enabled
        self._max_cache_size = cache_size
`

### 2. RerankService 基类调用

Alon 的 RerankService.**init** 直接设置 self._factory 和 self._tenant_id；本项目改为调用 super().**init**(tenant_id)，遵循 BaseModelService 的初始化模式。

### 3. ModelInstance 方法补充

一次迁移时 ModelInstance 仅保留了 LLM 相关方法；二次迁移补回了 invoke_text_embedding、get_text_embedding_num_tokens、invoke_rerank 三个方法。

### 4. LoggingCallback 回调

Alon 的 LoggingCallback 使用模块级 logger 变量；本项目改为 logger.bind(name=**name**) 绑定日志名称。

### 5. parameter_entities.py 参数实体

直接迁移，导入路径替换为 i_plugin.sdk.entities.provider_config。该模块为 ModelProviderFactory 的凭证 Schema 验证提供类型支撑。

## 待完成项

当前代码中存在以下 `TODO` 标记，均与数据库模型支持相关：

- `ProviderManager` 中的 Provider 记录查询（`_get_all_providers`、`_get_all_provider_model_settings` 等）
- `ProviderConfiguration` 中的自定义配置持久化（`custom_configuration_save`、`model_settings_save` 等）
- `ModelProviderFactory` 中的凭证 Schema 验证（`get_provider_schema`、`get_model_schema`）

这些标记将在 AI 模块的数据库模型创建后逐步完成。

## 架构简化（2026-06-30）

### 删除的模型

以下模型已删除，模型定义现在完全来自插件 manifest：

| 模型 | 说明 | 替代方案 |
|------|------|---------|
| ModelProvider | 模型提供商配置 | 插件 manifest 的 models_configuration |
| ModelConfig | 具体模型配置 | 插件 manifest 的 models 列表 |

### 新增字段

| 表 | 字段 | 说明 |
|----|------|------|
| plugin_credentials | is_default | 标记是否为插件的默认凭证 |

### 凭证获取流程变更

**旧流程（Alon）：**
1. 从 model_providers 表查询提供商配置
2. 从 model_configs 表查询模型配置
3. 从配置中获取凭证

**新流程（AI Platform）：**
1. 从插件 manifest 获取模型定义
2. 从 plugin_credentials 表获取默认凭证（通过 is_default 字段）
3. 通过 plugin_id 关联插件和凭证
4. 凭证在 ProviderManager.get_configurations() 中自动注入到 CustomConfiguration

### Session 传递链路

凭证查询需要数据库 Session，通过以下链路传递：

```
ChatController (Depends(get_db_session))
  → AlonChatModel(db_session=session)
    → LLMService.invoke(..., db_session=db_session)
      → ModelInstanceFactory.get_model_instance(..., db_session=db_session)
        → ProviderManager.get_configurations(..., db_session=db_session)
          → _inject_plugin_credentials(session, ...)
```

### ProviderManager 改造

以下方法已废弃，保留仅为向后兼容：

- `_get_all_providers()` - 模型定义来自插件
- `_get_all_provider_model_settings()` - 模型设置由插件管理
- `_get_all_custom_models()` - 自定义模型通过插件扩展
- `get_default_model_record()` - 默认凭证通过 is_default 管理

新增方法：

- `_inject_plugin_credentials()` - 从 PluginCredential 表注入凭证
- `_extract_plugin_id_from_provider()` - 从 provider 名称提取 plugin_id
- `_extract_credentials_schema_from_provider()` - 提取凭证架构用于解密
