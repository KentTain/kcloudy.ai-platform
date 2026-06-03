# Alon 项目源文件映射

本文档记录 migrate-plugin-system 变更对应的 Alon 项目源文件路径，供实现时参考。

## 源项目路径

```
ALON_ROOT=D:\Project\ai\Alon\packages\platform
```

## 文件映射表

### 1. ai_plugin SDK 迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai_plugin/sdk/entities/` | `{ALON_ROOT}/src/alon_plugin/sdk/entities/` |
| `src/ai_plugin/sdk/interfaces/` | `{ALON_ROOT}/src/alon_plugin/sdk/interfaces/` |
| `src/ai_plugin/sdk/errors/` | `{ALON_ROOT}/src/alon_plugin/sdk/errors/` |
| `src/ai_plugin/sdk/file/` | `{ALON_ROOT}/src/alon_plugin/sdk/file/` |
| `src/ai_plugin/sdk/schemas/` | `{ALON_ROOT}/src/alon_plugin/sdk/schemas/` |
| `src/ai_plugin/sdk/__init__.py` | `{ALON_ROOT}/src/alon_plugin/sdk/__init__.py` |

### 2. ai_plugin 服务端迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai_plugin/server/core/entities/` | `{ALON_ROOT}/src/alon_plugin/server/core/entities/` |
| `src/ai_plugin/server/core/server/` | `{ALON_ROOT}/src/alon_plugin/server/core/server/` |
| `src/ai_plugin/server/core/plugin_executor.py` | `{ALON_ROOT}/src/alon_plugin/server/core/plugin_executor.py` |
| `src/ai_plugin/server/core/plugin_registration.py` | `{ALON_ROOT}/src/alon_plugin/server/core/plugin_registration.py` |
| `src/ai_plugin/server/core/runtime.py` | `{ALON_ROOT}/src/alon_plugin/server/core/runtime.py` |
| `src/ai_plugin/server/core/utils/` | `{ALON_ROOT}/src/alon_plugin/server/core/utils/` |
| `src/ai_plugin/server/config/` | `{ALON_ROOT}/src/alon_plugin/server/config/` |
| `src/ai_plugin/server/invocations/` | `{ALON_ROOT}/src/alon_plugin/server/invocations/` |
| `src/ai_plugin/cli/` | `{ALON_ROOT}/src/alon_plugin/cli/` |
| `src/ai_plugin/plugin.py` | `{ALON_ROOT}/src/alon_plugin/plugin.py` |

### 3. ai/components/plugin 引擎迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/components/plugin/engine/config/` | `{ALON_ROOT}/src/alon/components/plugin/engine/config/` |
| `src/ai/components/plugin/engine/models/` | `{ALON_ROOT}/src/alon/components/plugin/engine/models/` |
| `src/ai/components/plugin/engine/utils/` | `{ALON_ROOT}/src/alon/components/plugin/engine/utils/` |
| `src/ai/components/plugin/engine/core/helper/` | `{ALON_ROOT}/src/alon/components/plugin/engine/core/helper/` |
| `src/ai/components/plugin/engine/core/session/` | `{ALON_ROOT}/src/alon/components/plugin/engine/core/session/` |
| `src/ai/components/plugin/engine/core/security/` | `{ALON_ROOT}/src/alon/components/plugin/engine/core/security/` |
| `src/ai/components/plugin/engine/core/communication/` | `{ALON_ROOT}/src/alon/components/plugin/engine/core/communication/` |
| `src/ai/components/plugin/engine/core/monitoring/` | `{ALON_ROOT}/src/alon/components/plugin/engine/core/monitoring/` |
| `src/ai/components/plugin/engine/core/warmup/` | `{ALON_ROOT}/src/alon/components/plugin/engine/core/warmup/` |
| `src/ai/components/plugin/engine/core/runtime/` | `{ALON_ROOT}/src/alon/components/plugin/engine/core/runtime/` |
| `src/ai/components/plugin/engine/core/plugin_manager.py` | `{ALON_ROOT}/src/alon/components/plugin/engine/core/plugin_manager.py` |
| `src/ai/components/plugin/engine/core/install_task_manager.py` | `{ALON_ROOT}/src/alon/components/plugin/engine/core/install_task_manager.py` |
| `src/ai/components/plugin/engine/api/routes/` | `{ALON_ROOT}/src/alon/components/plugin/engine/api/routes/` |
| `src/ai/components/plugin/engine/api/middleware.py` | `{ALON_ROOT}/src/alon/components/plugin/engine/api/middleware.py` |
| `src/ai/components/plugin/client/` | `{ALON_ROOT}/src/alon/components/plugin/client/` |
| `src/ai/components/plugin/commands/` | `{ALON_ROOT}/src/alon/components/plugin/commands/` |
| `src/ai/components/plugin/remotable.py` | `{ALON_ROOT}/src/alon/components/plugin/remotable.py` |
| `src/ai/components/plugin/setup.py` | `{ALON_ROOT}/src/alon/components/plugin/setup.py` |

### 4. 数据层迁移

| 目标文件 | Alon 源文件 |
|----------|-------------|
| `src/ai/models/plugin.py` | `{ALON_ROOT}/src/alon/models/plugin.py` |
| `src/ai/schemas/plugin.py` | `{ALON_ROOT}/src/alon/schemas/plugin.py` |

### 5. 服务层迁移

| 目标文件 | Alon 源文件 | 备注 |
|----------|-------------|------|
| `src/ai/services/plugin.py` | `{ALON_ROOT}/src/alon/services/plugin.py` | 需适配 framework 基础设施 |
| `src/ai/services/credential_service.py` | 新建 | 使用 `framework/utils/crypto.py` |

### 6. 控制器层迁移

| 目标文件 | Alon 源文件 |
|----------|-------------|
| `src/ai/controllers/admin/v1/plugin.py` | `{ALON_ROOT}/src/alon/controllers/admin/v1/plugin.py` |
| `src/ai/controllers/console/v1/plugin.py` | `{ALON_ROOT}/src/alon/controllers/console/v1/plugin/plugin.py` |
| `src/ai/controllers/inner/v1/plugin.py` | `{ALON_ROOT}/src/alon/controllers/inner_api/v1/plugin.py` |

## 导入路径替换规则

迁移时需要批量替换导入路径：

| Alon 导入路径 | 目标导入路径 |
|---------------|--------------|
| `from alon_plugin.` | `from ai_plugin.` |
| `from alon.components.plugin.` | `from ai.components.plugin.` |
| `from alon.models.plugin` | `from ai.models.plugin` |
| `from alon.schemas.plugin` | `from ai.schemas.plugin` |
| `from alon.services.plugin` | `from ai.services.plugin` |
| `from alon.configs.settings` | `from framework.configs.settings` |
| `from alon.common.ctx` | `from framework.common.ctx` |
| `from alon.common.exceptions` | `from framework.common.exceptions` |
| `from alon.models.core.engine` | `from framework.database.core.engine` |
| `from alon.components.oss.base` | `from framework.storage` |

## 关键依赖适配

### 凭证加密

```python
# Alon 使用
from alon.components.model.internal.helper.encrypter import encrypt_token, decrypt_token

# 改为使用 framework
from framework.utils.crypto import encrypt, decrypt
```

### 对象存储

```python
# Alon 使用
from alon.components.oss.base import oss_provider

# 改为使用 framework
from framework.storage import get_storage_provider
```

### 上下文

```python
# Alon 使用
from alon.common.ctx import CTX_TENANT_ID, CTX_USER_ID

# 改为使用 framework
from framework.common.ctx import get_tenant_id, get_user_id
```
