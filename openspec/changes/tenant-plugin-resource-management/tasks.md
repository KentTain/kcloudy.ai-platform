## 1. 基础设施 - Tenant 模块

- [ ] 1.1 创建 `framework/tenant/plugin_protocols.py`，定义 `PluginInstallationDTO`、`PluginRuntimeStateDTO`、`PluginConfigDTO` 和 `PluginInstallationProvider` 协议
- [ ] 1.2 在 `framework/tenant/plugin_protocols.py` 中实现全局注册函数 `register_plugin_installation_provider()` 和 `get_plugin_installation_provider()`
- [ ] 1.3 创建 `tenant/models/plugin_definition.py`，定义 `TenantPluginDefinition` ORM 模型
- [ ] 1.4 创建 `tenant/models/plugin_installation.py`，定义 `TenantPluginInstallation` ORM 模型
- [ ] 1.5 创建 `tenant/services/plugin_provider.py`，实现 `PluginInstallationProviderImpl` 类

## 2. 基础设施 - AI 模块

- [ ] 2.1 创建 `ai/models/plugin_config.py`，定义 `PluginConfig` ORM 模型
- [ ] 2.2 创建 `ai/models/plugin_runtime_state.py`，定义 `PluginRuntimeState` ORM 模型
- [ ] 2.3 更新 `ai/models/__init__.py`，导出新模型

## 3. 事件驱动机制

- [ ] 3.1 在 `framework/events/domain_events.py` 中定义 `PluginInstallationFailed` 事件
- [ ] 3.2 在 `framework/events/domain_events.py` 中定义 `PluginUninstallFailed` 事件
- [ ] 3.3 创建 `tenant/listeners/handlers/plugin_handler.py`，实现插件安装失败事件处理器
- [ ] 3.4 创建 `tenant/listeners/handlers/plugin_handler.py`，实现插件卸载失败事件处理器

## 4. 数据库迁移

- [ ] 4.1 创建数据库迁移脚本，新增 `tenant.plugin_definitions` 表
- [ ] 4.2 创建数据库迁移脚本，新增 `tenant.plugin_installations` 表
- [ ] 4.3 创建数据库迁移脚本，新增 `ai.plugin_configs` 表
- [ ] 4.4 创建数据库迁移脚本，新增 `ai.plugin_runtime_states` 表

## 5. PluginManager 数据访问替换

- [ ] 5.1 修改 `plugin_manager.py` 的 `_load_plugins_metadata_from_database()` 方法，使用 Provider + AI 侧查询
- [ ] 5.2 修改 `plugin_manager.py` 的 `_load_plugin_info_from_installation()` 方法，适配 DTO + AI 侧模型
- [ ] 5.3 修改 `plugin_manager.py` 的 `_save_plugin_installation_to_database()` 方法，使用 Provider + AI 侧写入
- [ ] 5.4 修改 `plugin_manager.py` 的 `_check_duplicate_installation()` 方法，使用 Provider 查询
- [ ] 5.5 修改 `plugin_manager.py` 的 `_ensure_plugin_ready()` 方法，使用 Provider 查询
- [ ] 5.6 修改 `plugin_manager.py` 的 `start_plugin()` 方法，写入 `plugin_runtime_states` 表
- [ ] 5.7 修改 `plugin_manager.py` 的 `stop_plugin()` 方法，更新 `plugin_runtime_states` 表和 Provider 状态
- [ ] 5.8 修改 `plugin_manager.py` 的 `install_plugin()` 方法，实现事件驱动的安装流程
- [ ] 5.9 修改 `plugin_manager.py` 的 `uninstall_plugin()` 方法，实现事件驱动的卸载流程

## 6. PluginManagementService 数据访问替换

- [ ] 6.1 修改 `ai/services/plugin.py` 的 `get_plugin_list()` 方法，使用 Provider + AI 侧查询
- [ ] 6.2 修改 `ai/services/plugin.py` 的 `get_plugin_info()` 方法，使用 Provider + AI 侧查询
- [ ] 6.3 修改 `ai/services/plugin.py` 的 `get_plugin_credentials_schema()` 方法，查询 `ai.plugin_configs`
- [ ] 6.4 修改 `ai/services/plugin.py` 的 `create_credential()` 方法，查询 `ai.plugin_configs`
- [ ] 6.5 修改 `ai/services/plugin.py` 的 `uninstall_plugin()` 方法，使用 Provider 删除 + AI 侧删除

## 7. Tenant Web 管理端 API

- [ ] 7.1 创建 `tenant/api/plugin.py`，定义插件定义列表查询端点 `/admin/v1/tenants/plugins`
- [ ] 7.2 创建 `tenant/schemas/plugin.py`，定义 `PluginDefinitionResponse` 响应模型

## 8. 定时清理任务

- [ ] 8.1 创建定时任务，清理超过 24 小时的 `FAILED` 状态安装记录

## 9. 应用启动注册

- [ ] 9.1 在应用启动入口注册 `PluginInstallationProviderImpl` 实例

## 10. 测试验证

- [ ] 10.1 编写 `PluginInstallationProviderImpl` 单元测试
- [ ] 10.2 编写 PluginManager 数据访问替换的集成测试
- [ ] 10.3 编写事件驱动一致性的集成测试
- [ ] 10.4 编写多租户数据隔离的集成测试
- [ ] 10.5 手动验证插件安装、启动、停止、卸载完整流程
