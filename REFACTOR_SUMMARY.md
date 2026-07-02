# Tenant-AI 模块依赖重构总结

## 重构目标

消除 Tenant 模块对 AI 模块的直接依赖，改为通过 Inner API 进行模块间通信。

## 完成的工作

### 第一阶段：AI 模块新增 Inner API

1. **新建 Schema 定义** (`ai/schemas/plugin_management.py`)
   - `InstallationItem` - 单个安装项数据模型
   - `BatchInstallRequest` - 批量安装请求
   - `BatchInstallResponse` - 批量安装响应
   - `StartPluginResponse` - 启动插件响应
   - `StopPluginResponse` - 停止插件响应

2. **新建 Inner API 控制器** (`ai/controllers/inner/plugin_management.py`)
   - `POST /ai/inner/v1/plugins/install-batch` - 批量安装插件
   - `POST /ai/inner/v1/plugins/{plugin_id}/start` - 启动插件
   - `POST /ai/inner/v1/plugins/{plugin_id}/stop` - 停止插件

3. **注册路由** (`ai/module.py`)
   - 添加 `inner_plugin_management_router` 到路由列表

### 第二阶段：Framework 层新增客户端

4. **新建 AI 客户端** (`framework/clients/ai_client.py`)
   - `AIClient` 类，支持单体模式和微服务模式
   - `start_plugin()` - 启动插件
   - `stop_plugin()` - 停止插件
   - `batch_install_plugins()` - 批量安装插件
   - `get_ai_client()` - 单例工厂函数

### 第三阶段：Tenant 模块改造

5. **改造 plugin_provider.py**
   - `start_installation()` - 改为调用 `ai_client.start_plugin()`
   - `stop_installation()` - 改为调用 `ai_client.stop_plugin()`
   - 移除对 `ai.services.plugin.plugin_management_service` 的直接导入

6. **改造 plugin_definition_service.py**
   - `install_to_tenants()` - 改为调用 `ai_client.batch_install_plugins()`
   - 移除对 `ai.models.plugin_config.PluginConfig` 的直接导入
   - 移除对 `ai.models.plugin_runtime_state.PluginRuntimeState` 的直接导入
   - 移除直接创建 AI 侧 Model 的代码

## 架构改进

### 改造前
```
Tenant 模块
├── plugin_provider.py
│   ├── 直接调用 ai.services.plugin.plugin_management_service
│   └── 直接操作 ai.models.plugin_config
└── plugin_definition_service.py
    └── 直接创建 ai.models.plugin_runtime_state
```

### 改造后
```
Tenant 模块
├── plugin_provider.py
│   └── 调用 framework.clients.ai_client
└── plugin_definition_service.py
    └── 调用 framework.clients.ai_client

Framework 层
└── clients/ai_client.py
    ├── 单体模式：直接调用 ai.services
    └── 微服务模式：HTTP 调用 ai/inner/v1

AI 模块
└── controllers/inner/plugin_management.py
    └── Inner API 接口（无认证）
```

## 依赖关系改进

### 改造前
```python
# tenant/services/plugin_provider.py
from ai.services.plugin import plugin_management_service  # ❌ 直接依赖
result = await plugin_management_service.start_plugin_with_response(...)

# tenant/services/plugin_definition_service.py
from ai.models.plugin_config import PluginConfig  # ❌ 直接依赖
from ai.models.plugin_runtime_state import PluginRuntimeState  # ❌ 直接依赖
```

### 改造后
```python
# tenant/services/plugin_provider.py
from framework.clients.ai_client import get_ai_client  # ✅ 通过框架客户端
ai_client = get_ai_client()
result = await ai_client.start_plugin(...)

# tenant/services/plugin_definition_service.py
from framework.clients.ai_client import get_ai_client  # ✅ 通过框架客户端
ai_client = get_ai_client()
result = await ai_client.batch_install_plugins(...)
```

## 新增文件清单

| 文件路径 | 说明 |
|---------|------|
| `ai/schemas/plugin_management.py` | Inner API Schema 定义 |
| `ai/controllers/inner/plugin_management.py` | Inner API 控制器 |
| `framework/clients/ai_client.py` | AI 客户端（双模式） |

## 修改文件清单

| 文件路径 | 修改内容 |
|---------|---------|
| `ai/module.py` | 注册新的 Inner API 路由 |
| `tenant/services/plugin_provider.py` | start/stop_installation 改用客户端 |
| `tenant/services/plugin_definition_service.py` | install_to_tenants 改用客户端 |

## 验证方法

### 代码检查
```bash
# 检查 tenant 模块不再直接导入 ai 模块的 Service 和 Model
grep -r "from ai\." server/python/src/tenant/ --exclude-dir=__pycache__
# 应该只剩下导入 ai_client 的地方
```

### 运行测试
```bash
# 运行单元测试
pytest tests/ai/unit/controllers/test_inner_plugin_management.py -v
pytest tests/framework/unit/test_ai_client.py -v
pytest tests/tenant/unit/services/ -v

# 运行集成测试
pytest tests/integration/test_plugin_management.py -v
```

## 向后兼容性

- ✅ Provider 协议接口签名不变
- ✅ 保留现有的 Admin API 和 Console API
- ✅ Inner API 作为新增实现，不影响现有功能
- ✅ 单体模式和微服务模式均支持

## 性能影响

- **单体模式**：Inner API 仍是本地函数调用，性能影响极小
- **微服务模式**：HTTP 调用，批量接口减少网络往返

## 下一步工作

- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 更新 API 文档
- [ ] 更新架构设计文档
- [ ] 配置文件添加 `ai_inner_url` 配置项（可选，用于微服务模式）
