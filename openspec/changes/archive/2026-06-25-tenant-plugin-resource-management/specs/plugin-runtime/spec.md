## 新增需求

### 需求:AI 模块管理插件配置

AI 模块必须在 AI Schema 中维护插件配置表（`plugin_configs`），存储插件能力定义和持久化运行时配置。

#### 场景:创建插件配置

- **当** 插件安装成功
- **那么** AI 模块必须在 `plugin_configs` 表中创建记录，包含 `plugin_config` 和 `runtime_config` 字段

#### 场景:更新插件配置

- **当** 插件配置发生变化
- **那么** AI 模块必须更新 `plugin_configs` 表中对应的 `plugin_config` 或 `runtime_config` 字段

#### 场景:删除插件配置

- **当** 插件卸载
- **那么** AI 模块必须删除 `plugin_configs` 表中对应的记录

### 需求:AI 模块管理运行时状态

AI 模块必须在 AI Schema 中维护运行时状态表（`plugin_runtime_states`），存储进程信息、调用统计和冻结状态。

#### 场景:创建运行时状态

- **当** 插件安装成功
- **那么** AI 模块必须在 `plugin_runtime_states` 表中创建初始记录

#### 场景:更新进程信息

- **当** 插件启动或停止
- **那么** AI 模块必须更新 `process_id`、`port`、`last_started_at` 或 `last_stopped_at` 字段

#### 场景:更新调用统计

- **当** 插件被调用
- **那么** AI 模块必须递增 `call_count` 字段，更新 `last_accessed_at` 时间戳

#### 场景:记录错误信息

- **当** 插件调用失败
- **那么** AI 模块必须递增 `error_count` 字段，记录 `last_error` 信息

#### 场景:更新冻结状态

- **当** 插件被冻结或解冻
- **那么** AI 模块必须更新 `frozen_at` 字段

### 需求:通过 Provider 访问安装记录

AI 模块必须通过 `PluginInstallationProvider` 协议访问 Tenant 侧的安装记录，不得直接访问 Tenant Schema 的数据表。

#### 场景:加载插件元数据

- **当** PluginManager 启动时加载插件
- **那么** AI 模块必须调用 `Provider.get_tenant_installations()` 获取安装记录列表

#### 场景:保存安装记录

- **当** PluginManager 安装插件
- **那么** AI 模块必须调用 `Provider.create_installation()` 创建 Tenant 侧记录

#### 场景:更新安装状态

- **当** 安装流程完成或失败
- **那么** AI 模块必须调用 `Provider.update_installation()` 更新状态

### 需求:事件驱动一致性

AI 模块必须在安装或卸载失败时发布事件，触发 Tenant 侧的补偿操作。

#### 场景:安装失败发布事件

- **当** AI 侧配置创建失败，但 Tenant 侧安装记录已存在
- **那么** AI 模块必须发布 `PluginInstallationFailed` 事件，包含租户 ID、插件 ID 和错误信息

#### 场景:卸载失败发布事件

- **当** AI 侧数据删除失败，但 Tenant 侧记录已删除
- **那么** AI 模块必须发布 `PluginUninstallFailed` 事件

## 修改需求

### 需求:PluginManager 数据访问方式

**原需求：** PluginManager 直接通过 ORM 查询 `ai.plugin_installations` 表获取插件信息。

**新需求：** PluginManager 必须通过 `PluginInstallationProvider` 获取 Tenant 侧安装记录，并查询 AI 侧 `plugin_configs` 和 `plugin_runtime_states` 表组装完整的插件信息。

#### 场景:加载插件元数据（修改后）

- **当** PluginManager 执行 `_load_plugins_metadata_from_database()`
- **那么** 系统必须：
  1. 调用 `Provider.get_tenant_installations()` 获取安装记录
  2. 查询 `ai.plugin_configs` 获取配置
  3. 查询 `ai.plugin_runtime_states` 获取运行时状态
  4. 组装 `PluginInfo` 对象

#### 场景:保存安装记录（修改后）

- **当** PluginManager 执行 `_save_plugin_installation_to_database()`
- **那么** 系统必须：
  1. 调用 `Provider.create_installation()` 创建 Tenant 侧记录
  2. 在当前事务中创建 `ai.plugin_configs` 和 `ai.plugin_runtime_states` 记录
