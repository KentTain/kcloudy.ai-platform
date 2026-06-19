# Alon 项目源文件映射

本文档记录 migrate-model-component 变更对应的 Alon 项目源文件路径，供实现时参考。

## 源项目路径

```
ALON_ROOT=D:\Project\ai\Alon\packages\platform
```

## 文件映射表

### 1. entities 实体层迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/model/entities/__init__.py` | `{ALON_ROOT}/src/alon/components/model/entities/__init__.py` |
| `src/ai/components/model/entities/plugin_entities.py` | `{ALON_ROOT}/src/alon/components/model/entities/plugin_entities.py` |
| `src/ai/components/model/entities/provider_entities.py` | `{ALON_ROOT}/src/alon/components/model/entities/provider_entities.py` |

### 2. errors 异常层迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/model/errors/__init__.py` | `{ALON_ROOT}/src/alon/components/model/errors/__init__.py` |
| `src/ai/components/model/errors/error.py` | `{ALON_ROOT}/src/alon/components/model/errors/error.py` |

### 3. schema Schema 定义迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/model/schema/model_entities.py` | `{ALON_ROOT}/src/alon/components/model/schema/model_entities.py` |

### 4. internal 内部实现迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/model/internal/__init__.py` | `{ALON_ROOT}/src/alon/components/model/internal/__init__.py` |
| `src/ai/components/model/internal/configs/__init__.py` | `{ALON_ROOT}/src/alon/components/model/internal/configs/__init__.py` |
| `src/ai/components/model/internal/entities/parameter_entities.py` | `{ALON_ROOT}/src/alon/components/model/internal/entities/parameter_entities.py` |
| `src/ai/components/model/internal/entities/provider_entities.py` | `{ALON_ROOT}/src/alon/components/model/internal/entities/provider_entities.py` |
| `src/ai/components/model/internal/helper/encrypter.py` | `{ALON_ROOT}/src/alon/components/model/internal/helper/encrypter.py` |
| `src/ai/components/model/internal/helper/position_helper.py` | `{ALON_ROOT}/src/alon/components/model/internal/helper/position_helper.py` |
| `src/ai/components/model/internal/helper/ssrf_proxy.py` | `{ALON_ROOT}/src/alon/components/model/internal/helper/ssrf_proxy.py` |
| `src/ai/components/model/internal/helper/yaml_utils.py` | `{ALON_ROOT}/src/alon/components/model/internal/helper/yaml_utils.py` |
| `src/ai/components/model/internal/model_instance_factory.py` | `{ALON_ROOT}/src/alon/components/model/internal/model_instance_factory.py` |
| `src/ai/components/model/internal/model_provider_factory.py` | `{ALON_ROOT}/src/alon/components/model/internal/model_provider_factory.py` |
| `src/ai/components/model/internal/provider_configuration.py` | `{ALON_ROOT}/src/alon/components/model/internal/provider_configuration.py` |
| `src/ai/components/model/internal/provider_manager.py` | `{ALON_ROOT}/src/alon/components/model/internal/provider_manager.py` |

### 5. model_providers 模型提供者基类迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/model/model_providers/__init__.py` | `{ALON_ROOT}/src/alon/components/model/model_providers/__init__.py` |
| `src/ai/components/model/model_providers/__base__/__init__.py` | `{ALON_ROOT}/src/alon/components/model/model_providers/__base__/__init__.py` |
| `src/ai/components/model/model_providers/__base__/ai_model.py` | `{ALON_ROOT}/src/alon/components/model/model_providers/__base__/ai_model.py` |
| `src/ai/components/model/model_providers/__base__/large_language_model.py` | `{ALON_ROOT}/src/alon/components/model/model_providers/__base__/large_language_model.py` |
| `src/ai/components/model/model_providers/__base__/tokenizers/gpt2_tokenzier.py` | `{ALON_ROOT}/src/alon/components/model/model_providers/__base__/tokenizers/gpt2_tokenzier.py` |

> **注意**：`text_embedding_model.py` 和 `rerank_model.py` 本接口未使用，暂不迁移。

### 6. services 服务层迁移

| 目标路径 | Alon 源路径 | 备注 |
|----------|-------------|------|
| `src/ai/components/model/services/__init__.py` | `{ALON_ROOT}/src/alon/components/model/services/__init__.py` | |
| `src/ai/components/model/services/base_model_service.py` | `{ALON_ROOT}/src/alon/components/model/services/base_model_service.py` | |
| `src/ai/components/model/services/llm_service.py` | `{ALON_ROOT}/src/alon/components/model/services/llm_service.py` | **核心文件** |
| `src/ai/components/model/services/management_service.py` | `{ALON_ROOT}/src/alon/components/model/services/management_service.py` | |

> **注意**：`embedding_service.py` 和 `rerank_service.py` 本接口未使用，暂不迁移。

### 7. callbacks 回调机制迁移（可选）

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/model/callbacks/__init__.py` | `{ALON_ROOT}/src/alon/components/model/callbacks/__init__.py` |
| `src/ai/components/model/callbacks/base_callback.py` | `{ALON_ROOT}/src/alon/components/model/callbacks/base_callback.py` |
| `src/ai/components/model/callbacks/logging_callback.py` | `{ALON_ROOT}/src/alon/components/model/callbacks/logging_callback.py` |

### 8. utils 工具函数迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/model/utils/__init__.py` | `{ALON_ROOT}/src/alon/components/model/utils/__init__.py` |
| `src/ai/components/model/utils/helper.py` | `{ALON_ROOT}/src/alon/components/model/utils/helper.py` |

### 9. schema_validators 校验器迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/model/schema_validators/__init__.py` | `{ALON_ROOT}/src/alon/components/model/schema_validators/__init__.py` |
| `src/ai/components/model/schema_validators/common_validator.py` | `{ALON_ROOT}/src/alon/components/model/schema_validators/common_validator.py` |
| `src/ai/components/model/schema_validators/model_credential_schema_validator.py` | `{ALON_ROOT}/src/alon/components/model/schema_validators/model_credential_schema_validator.py` |
| `src/ai/components/model/schema_validators/provider_credential_schema_validator.py` | `{ALON_ROOT}/src/alon/components/model/schema_validators/provider_credential_schema_validator.py` |

### 10. 常量与入口文件

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/model/constants.py` | `{ALON_ROOT}/src/alon/components/model/constants.py` |
| `src/ai/components/model/model_manager.py` | `{ALON_ROOT}/src/alon/components/model/model_manager.py` |
| `src/ai/components/model/__init__.py` | `{ALON_ROOT}/src/alon/components/model/__init__.py` |

## 导入路径替换规则

迁移时需要批量替换导入路径：

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

## 关键依赖适配

### 凭证加密

```python
# Alon 使用
from alon.components.model.internal.helper.encrypter import encrypt_token, decrypt_token

# 改为使用 framework
from framework.utils.crypto import encrypt, decrypt
```

### 缓存

```python
# Alon 使用
from alon.extensions.ext_redis import redis_client

# 改为使用 framework
from framework.cache.tenant_cache_manager import TenantCacheManager
# 或
from framework.cache.redis_util import RedisUtil
```

### 上下文

```python
# Alon 使用
from alon.common.ctx import CTX_TENANT_ID, CTX_USER_ID

# 改为使用 framework
from framework.common.ctx import get_tenant_id, get_user_id
```

### 数据库会话

```python
# Alon 使用
from alon.models.core.engine import async_session

# 改为使用 framework
from framework.database.core.engine import get_async_session
```

### Plugin 客户端

```python
# Alon 使用
from alon.components.plugin.client.model_client import ModelClient

# 改为使用新路径
from ai.components.plugin.client.model_client import ModelClient
```

## 迁移优先级

### 第一优先级（核心功能，必须迁移）

1. `errors/error.py` - 异常定义
2. `entities/` - 实体定义
3. `schema/model_entities.py` - Schema 定义
4. `internal/provider_configuration.py` - Provider 配置
5. `internal/provider_manager.py` - Provider 管理
6. `internal/model_provider_factory.py` - Provider 工厂
7. `internal/model_instance_factory.py` - 实例工厂
8. `model_providers/__base__/large_language_model.py` - LLM 基类
9. `services/llm_service.py` - **核心服务**
10. `services/management_service.py` - 模型管理

### 第二优先级（辅助功能，按需迁移）

1. `internal/helper/` - 辅助工具
2. `utils/helper.py` - 工具函数
3. `schema_validators/` - 参数校验器
4. `callbacks/` - 回调机制

### 第三优先级（暂不迁移）

1. `services/embedding_service.py` - Embedding 服务
2. `services/rerank_service.py` - Rerank 服务
3. `model_providers/__base__/text_embedding_model.py` - Embedding 基类
4. `model_providers/__base__/rerank_model.py` - Rerank 基类

## 文件数量统计

| 类别 | 文件数 |
|------|--------|
| 必须迁移 | 15 |
| 按需迁移 | 10 |
| 暂不迁移 | 4 |
| **总计** | **29** |
