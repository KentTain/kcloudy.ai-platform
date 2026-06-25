## 1. 数据模型与迁移

- [x] 1.1 新增 `tenant.plugin_definitions` 表字段：`is_recommended`（BOOLEAN, 默认 false）、`is_enabled`（BOOLEAN, 默认 true）
- [x] 1.2 创建 `ai.plugin_install_tasks` 表（任务 ID、租户 ID、插件 ID、状态、进度、步骤、错误信息、时间戳）
- [x] 1.3 创建数据库迁移脚本（Alembic migration）
- [x] 1.4 在 `iam` 模块种子数据中添加权限定义：`tenant:plugin:read`、`tenant:plugin:write`、`ai:plugin:read`、`ai:plugin:write`、`ai:plugin:delete`

## 2. Tenant 模块 - 插件定义注册

- [x] 2.1 创建 `PluginPackageService`：插件包解析服务（manifest 解析、校验和计算、格式验证）
- [x] 2.2 创建 `PluginStorageService`：MinIO 上传服务（bucket: plugins, key: {plugin_id}/{version}.zip）
- [x] 2.3 创建 `PluginDefinitionService`：插件定义注册业务逻辑（注：已有 PluginDefinitionService，已扩展注册方法）
- [x] 2.4 创建 `ScanDirectoryRequest`、`ScanDirectoryResponse` Schema
- [x] 2.5 实现 `POST /tenant/admin/v1/plugin-definitions/scan` API（扫描服务器目录注册）
- [x] 2.6 创建 `UploadPluginRequest`、`UploadPluginResponse` Schema
- [x] 2.7 实现 `POST /tenant/admin/v1/plugin-definitions/upload` API（上传插件包注册）

## 3. Tenant 模块 - 插件定义管理

- [x] 3.1 创建 `PluginDefinitionQuery`、`PluginDefinitionResponse`、`PluginDefinitionDetailResponse` Schema
- [x] 3.2 创建 `PluginDefinitionService.list_definitions()` 方法（分页查询、关键词搜索、类型筛选）
- [x] 3.3 实现 `GET /tenant/admin/v1/plugin-definitions` API（列表查询）
- [x] 3.4 实现 `GET /tenant/admin/v1/plugin-definitions/{plugin_id}` API（详情查看）
- [x] 3.5 创建 `UpdatePluginDefinitionRequest` Schema
- [x] 3.6 实现 `PATCH /tenant/admin/v1/plugin-definitions/{plugin_id}` API（标记推荐/禁用）
- [x] 3.7 实现 `DELETE /tenant/admin/v1/plugin-definitions/{plugin_id}` API（删除定义，检查 refers > 0）

## 4. Tenant 模块 - 统计仪表板

- [x] 4.1 创建 `PluginStatisticsResponse` Schema（定义统计、安装统计）
- [x] 4.2 创建 `PluginStatisticsService.get_statistics()` 方法
- [x] 4.3 实现 `GET /tenant/admin/v1/plugin-definitions/statistics` API

## 5. AI 模块 - 可用插件列表

- [x] 5.1 创建 `AvailablePluginQuery`、`AvailablePluginResponse` Schema
- [x] 5.2 扩展 `PluginManagementService.get_available_plugins()` 方法（从 Tenant Provider 获取定义，标记安装状态）
- [x] 5.3 实现 `GET /ai/console/v1/plugins/available` API

## 6. AI 模块 - 安装任务队列

- [x] 6.1 创建 `PluginInstallTask` 模型（对应 `ai.plugin_install_tasks` 表）
- [x] 6.2 创建 `InstallPluginRequest`、`InstallPluginResponse` Schema
- [x] 6.3 创建 `InstallTaskService`：任务创建、状态更新、进度追踪
- [x] 6.4 创建 Redis Stream 任务队列消费者（`InstallTaskConsumer`）
- [x] 6.5 实现安装任务执行逻辑（下载插件包、初始化配置、更新状态）
- [x] 6.6 实现 `POST /ai/console/v1/plugins/installations` API（创建安装任务）
- [x] 6.7 创建 `InstallTaskQuery`、`InstallTaskResponse`、`InstallTaskDetailResponse` Schema
- [x] 6.8 实现 `GET /ai/console/v1/plugins/install-tasks` API（任务列表）
- [x] 6.9 实现 `GET /ai/console/v1/plugins/install-tasks/{task_id}` API（任务详情）
- [x] 6.10 配置任务超时机制（30 分钟）和超时处理

## 7. AI 模块 - 卸载插件

- [x] 7.1 扩展 `PluginManagementService.uninstall_plugin()` 方法（停止进程、清理数据、递减引用计数）
- [x] 7.2 实现 `DELETE /ai/console/v1/plugins/installations/{plugin_id}` API

## 8. AI 模块 - 运行时管理

- [x] 8.1 创建 `StartPluginResponse`、`StopPluginResponse` Schema
- [x] 8.2 实现 `POST /ai/console/v1/plugins/installations/{plugin_id}/start` API
- [x] 8.3 实现 `POST /ai/console/v1/plugins/installations/{plugin_id}/stop` API
- [x] 8.4 创建 `PluginConfigResponse`、`UpdatePluginConfigRequest` Schema
- [x] 8.5 实现 `GET /ai/console/v1/plugins/installations/{plugin_id}/config` API
- [x] 8.6 实现 `PATCH /ai/console/v1/plugins/installations/{plugin_id}/config` API
- [x] 8.7 创建 `RuntimeStateResponse`、`RuntimeStateListResponse` Schema
- [x] 8.8 实现 `GET /ai/console/v1/plugins/installations/{plugin_id}/runtime-state` API
- [x] 8.9 实现 `GET /ai/console/v1/plugins/runtime-states` API（批量状态）

## 9. AI 模块 - 统计仪表板

- [x] 9.1 创建 `PluginUsageStatisticsResponse` Schema（状态统计、使用统计、运行时统计）
- [x] 9.2 创建 `PluginUsageStatisticsService.get_statistics()` 方法
- [x] 9.3 实现 `GET /ai/console/v1/plugins/statistics` API

## 10. 权限控制集成

- [ ] 10.1 创建权限校验装饰器或中间件函数
- [ ] 10.2 在 Tenant 插件定义管理 API 中添加权限校验（`tenant:plugin:read`、`tenant:plugin:write`）
- [ ] 10.3 在 AI 插件安装使用 API 中添加权限校验（`ai:plugin:read`、`ai:plugin:write`、`ai:plugin:delete`）

## 11. 事件处理与定时任务

- [ ] 11.1 更新 `PluginInstallationFailedHandler`：删除或更新 `plugin_installations` 记录
- [ ] 11.2 创建 `CleanupPendingInstallationsTask`：清理超过 24 小时的 PENDING 状态记录
- [ ] 11.3 配置定时任务调度

## 12. 测试

- [ ] 12.1 编写 `PluginPackageService` 单元测试（manifest 解析、校验和计算）
- [ ] 12.2 编写 `PluginDefinitionService` 单元测试（注册、查询、标记、删除）
- [ ] 12.3 编写 Tenant 插件定义管理 API 集成测试
- [ ] 12.4 编写 `InstallTaskService` 单元测试（任务创建、状态更新）
- [ ] 12.5 编写安装任务消费者集成测试
- [ ] 12.6 编写 AI 插件安装/卸载 API 集成测试
- [ ] 12.7 编写 AI 运行时管理 API 集成测试
- [ ] 12.8 编写权限校验测试

## 13. 文档与配置

- [x] 13.1 更新 `tenant/CLAUDE.md` 文档（新增 API 端点说明）
- [x] 13.2 更新 `ai/CLAUDE.md` 文档（新增 API 端点说明）
- [x] 13.3 添加配置项：MinIO bucket 名称、任务超时时间、缓存 TTL
