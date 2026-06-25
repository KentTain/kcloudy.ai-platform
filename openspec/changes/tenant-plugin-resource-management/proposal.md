## 为什么

当前插件和模型资源的管理职责分散在 AI 模块，Tenant 模块对这些资源无感知，导致管理分散、职责模糊、配额不可控。Tenant 模块无法统一分配和限制 AI 资源，无法实现租户级的资源管控。

此变更将插件资源管理职责从 AI 模块迁移至 Tenant 模块，实现"有什么"（资源定义）与"用什么"（运行时配置）的职责分离，为后续的租户资源配额管理奠定基础。

## 变更内容

### 新增

- **Tenant Schema 新增表**：
  - `plugin_definitions`：全局插件注册表，合并原 `ai.plugins` + `ai.plugin_declarations`
  - `plugin_installations`：租户级安装记录，仅包含管理面字段

- **AI Schema 新增表**：
  - `plugin_configs`：插件配置，从 `plugin_installations` 剥离
  - `plugin_runtime_states`：运行时状态，从 `plugin_installations` 剥离

- **Inner API**：
  - `PluginInstallationProvider` 协议定义
  - `PluginInstallationProviderImpl` 实现
  - 全局注册机制

- **事件驱动一致性机制**：
  - `PluginInstallationFailed` 事件
  - `PluginUninstallFailed` 事件
  - Tenant 侧事件处理器

### 修改

- **PluginManager**：数据访问方式从 ORM 替换为 Provider + AI 侧查询
- **PluginManagementService**：数据访问方式同上

### 移除

- `ai.plugins` 表
- `ai.plugin_declarations` 表
- `ai.plugin_installations` 表

## 功能 (Capabilities)

### 新增功能

- `plugin-resource-management`：Tenant 模块统一管理插件资源定义和安装记录，提供 Inner API 供 AI 模块访问

### 修改功能

- `plugin-runtime`：AI 模块通过 Provider 访问 Tenant 侧安装记录，配置和运行时状态存储在 AI Schema

## 影响

### 代码模块

- `tenant/models/`：新增 `plugin_definition.py`, `plugin_installation.py`
- `tenant/services/`：新增 `plugin_provider.py`
- `framework/tenant/`：新增 `plugin_protocols.py`
- `framework/events/`：新增事件定义
- `tenant/listeners/`：新增事件处理器
- `ai/models/`：新增 `plugin_config.py`, `plugin_runtime_state.py`
- `ai/components/plugin/engine/core/plugin_manager.py`：数据访问方式替换
- `ai/services/plugin.py`：数据访问方式替换

### API 端点

- `/admin/v1/tenants/plugins`：Tenant Web 管理端查询插件定义列表
- `/inner/v1/plugins/*`：Inner API（Provider 协议实现）

### 数据库

- **新增表**：`tenant.plugin_definitions`, `tenant.plugin_installations`, `ai.plugin_configs`, `ai.plugin_runtime_states`
- **移除表**：`ai.plugins`, `ai.plugin_declarations`, `ai.plugin_installations`

### 迁移策略

无历史数据，直接创建新表结构，无需数据迁移。
