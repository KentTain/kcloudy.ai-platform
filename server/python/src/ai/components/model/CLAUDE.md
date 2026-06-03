# Model 组件开发指南

本文件为 Claude Code 在 `ai/components/model/` 目录中工作时提供指导。

## 模块定位

Model 组件是模型调用的统一门面。它封装了 Provider 管理、模型实例创建、凭证验证等底层细节，对外提供 LLM、Embedding、Rerank 调用和管理接口。

**核心职责：**

- 统一的 LLM / Embedding / Rerank 调用入口
- Provider 配置管理与缓存
- 模型实例的创建与生命周期管理
- 供应商凭证验证
- 默认模型管理

## 目录结构

```text
model/
├── __init__.py                  # 公共导出：ModelInstanceFactory、各 Service
├── constants.py                 # 常量定义：HIDDEN_VALUE、DEFAULT_MODEL_STATUS
├── CLAUDE.md                    # 本文件
├── MIGRATION.md                 # 迁移日志
│
├── callbacks/                   # LLM 调用回调机制
│   ├── __init__.py
│   ├── base_callback.py         # 回调基类（on_before_invoke / on_new_chunk / on_after_invoke / on_invoke_error）
│   └── logging_callback.py      # 日志回调（记录请求参数、响应结果、错误信息）
│
├── errors/                      # 异常定义
│   ├── __init__.py
│   └── error.py                 # ProviderTokenNotInitError、ProviderNotFoundError、ModelInvocationError 等
│
├── internal/                    # 内部实现，不直接被外部模块导入
│   ├── __init__.py              # 导出 ModelInstance、ModelInstanceFactory、实体类
│   ├── model_instance_factory.py  # ModelInstance + ModelInstanceFactory
│   ├── model_provider_factory.py  # ModelProviderFactory（插件 Provider 加载与实例化）
│   ├── provider_configuration.py  # ProviderConfiguration、ProviderConfigurations、ProviderModelBundle
│   └── provider_manager.py        # ProviderManager（配置加载、缓存、默认模型管理）
│
├── model_providers/             # 模型提供者基类
│   ├── __init__.py
│   └── __base__/
│       ├── __init__.py
│       ├── ai_model.py            # AIModelImpl 基类
│       ├── large_language_model.py # LargeLanguageModelImpl（LLM 调用实现）
│       ├── text_embedding_model.py # TextEmbeddingModelImpl（Embedding 调用实现）
│       ├── rerank_model.py        # RerankModelImpl（Rerank 调用实现）
│       └── tokenizers/            # Token 计数器
│           ├── __init__.py
│           └── gpt2_tokenizer.py
│
├── schema/                      # Schema 定义（Pydantic 模型与 Provider ID）
│   ├── __init__.py
│   ├── model_entities.py        # ModelStatus、SimpleModelProviderEntity、ModelWithProviderEntity 等
│   └── provider_id.py           # GenericProviderID、ModelProviderID、ToolProviderID
│
├── services/                    # 对外服务层
│   ├── __init__.py
│   ├── base_model_service.py     # BaseModelService（默认模型解析）
│   ├── llm_service.py            # LLMService（核心：invoke / stream / tokens）
│   ├── embedding_service.py      # EmbeddingService（embed / batch_embed / tokens）
│   ├── rerank_service.py         # RerankService（rerank / score）
│   └── management_service.py     # ManagementService、ModelService、ProviderService、DefaultModelService
│
└── utils/                       # 工具函数
    ├── __init__.py
    └── helper.py                 # dump_model（Pydantic 模型序列化兼容）
```

## 核心类说明

### LLMService

LLM 调用的统一入口。使用单例模式（基于 `WeakValueDictionary`），相同 `tenant_id` 返回相同实例。

| 方法 | 说明 |
|------|------|
| `invoke(prompt_messages, ...)` | 非流式 LLM 调用，返回 `LLMResult` |
| `stream(prompt_messages, ...)` | 流式 LLM 调用，异步生成器返回 `LLMResultChunk` |
| `tokens(prompt_messages, ...)` | 计算 token 数量 |
| `clear_instance(tenant_id)` | 清除指定租户的单例 |
| `clear_all_instances()` | 清除所有单例 |

### EmbeddingService

文本嵌入服务。提供 LRU 缓存（类级共享），支持单条和批量嵌入。

| 方法 | 说明 |
|------|------|
| embed(text, ...) | 单文本嵌入，返回向量 |
| atch_embed(texts, ...) | 批量文本嵌入，返回 TextEmbeddingResult |
| 	okens(texts, ...) | 计算 token 数量 |

### RerankService

重排序服务。对文档列表按与查询的相关度排序。

| 方法 | 说明 |
|------|------|
| 
erank(query, docs, ...) | 文档重排序，返回 RerankResult |
| score(query, doc, ...) | 单文档相似度打分 |

### ProviderManager

供应商配置的统一管理器。负责从数据库加载配置并缓存到 Redis。

| 方法 | 说明 |
|------|------|
| `get_configurations(tenant_id)` | 获取供应商配置集合（优先从 Redis 缓存读取） |
| `clear_cache(tenant_id)` | 清除配置缓存 |
| `_get_provider_model_bundle(tenant_id, provider, model_type)` | 获取供应商模型束 |

### ModelInstanceFactory

模型实例创建工厂。内部持有 `ProviderManager`，根据 tenant/provider/model_type/model 创建 `ModelInstance`。

| 方法 | 说明 |
|------|------|
| `get_model_instance(tenant_id, provider, model_type, model)` | 获取模型实例 |
| `get_default_provider_model_name(tenant_id, model_type)` | 获取默认供应商和模型名称 |
| `get_default_model_instance(tenant_id, model_type)` | 获取默认模型实例 |

### ModelProviderFactory

Provider 工厂。从插件系统加载 Provider 实体，创建模型类型实例。

| 方法 | 说明 |
|------|------|
| `get_providers()` | 获取所有模型供应商实体 |
| `get_model_type_instance(provider, model_type)` | 获取指定类型的模型实现实例 |

### ManagementService

管理操作的门面类。通过 `.models()`、`.providers()`、`.default_models()` 获取子管理器。

## 依赖组件

| 依赖 | 路径 | 用途 |
|------|------|------|
| ai_plugin/sdk | `src/ai_plugin/sdk/` | 模型实体定义（ModelType、LLMResult、PromptMessage 等） |
| framework/cache | `src/framework/cache/` | Redis 缓存（TenantCacheManager） |
| framework/utils/crypto | `src/framework/utils/crypto.py` | 凭证加解密 |
| framework/common/ctx | `src/framework/common/ctx/` | 租户上下文 |
| framework/database | `src/framework/database/` | 数据库会话 |
| ai/components/plugin | `src/ai/components/plugin/` | 插件系统 ModelClient |

## 使用示例

### LLM 调用（非流式）

```python
from ai.components.model import LLMService
from ai_plugin.sdk.entities.model.message import HumanMessagePromptMessage

service = LLMService(tenant_id="tenant-123")
result = await service.invoke(
    prompt_messages=[HumanMessagePromptMessage(content="你好")],
    model="gpt-4o",
    provider="openai",
)
print(result.message.content)
```

### LLM 调用（流式）

```python
service = LLMService(tenant_id="tenant-123")
async for chunk in service.stream(
    prompt_messages=[HumanMessagePromptMessage(content="你好")],
):
    print(chunk.message.content, end="")
```

### 使用默认模型

```python
# 不指定 provider 和 model，自动使用租户配置的默认 LLM
result = await service.invoke(
    prompt_messages=[HumanMessagePromptMessage(content="你好")],
)
```

### 模型管理

```python
from ai.components.model import ManagementService

mgmt = ManagementService(tenant_id="tenant-123")

# 启用/禁用模型
await mgmt.models().enable_model(provider="openai", model="gpt-4o", model_type=ModelType.LLM)
await mgmt.models().disable_model(provider="openai", model="gpt-4o", model_type=ModelType.LLM)

# 获取供应商配置
configurations = await mgmt.providers().get_configurations()

# 获取/更新默认模型
default_model = await mgmt.default_models().get_default_model(ModelType.LLM)
await mgmt.default_models().update_default_model(ModelType.LLM, provider="openai", model="gpt-4o")
```

## 注意事项

- `internal/` 下的模块为内部实现，不应被 `model/` 外部直接导入。外部统一通过 `services/` 或 `__init__.py` 导出使用。
- `ProviderManager.get_configurations()` 使用 Redis 缓存，缓存键格式为 `model_provider_configurations:{tenant_id}`，TTL 为 3600 秒。
- `LLMService` 使用 `WeakValueDictionary` 实现单例，当外部不再持有引用时缓存会自动清理。
- 数据库相关的 Provider 配置加载方法中存在 `# TODO: 需要数据库模型支持` 标记，当前返回空数据。
