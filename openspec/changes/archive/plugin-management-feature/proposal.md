## 为什么

当前 AI Platform 缺乏统一的插件管理功能。平台管理员无法注册和管理插件定义，租户管理员无法自主安装、配置和监控插件运行状态。现有的插件能力分散在代码中，缺乏可视化管理界面和标准化的生命周期管理流程。

本变更将建立完整的插件管理功能，实现：
- **平台管理员**：注册插件定义、标记推荐/禁用、查看全局统计
- **租户管理员**：浏览可用插件、安装/卸载、启动/停止、配置管理、运行时监控

## 变更内容

### 新增功能

1. **Tenant 模块 - 插件定义管理**
   - 插件定义注册（服务器目录扫描、本地上传）
   - 插件定义列表、详情、标记推荐/禁用、删除
   - 统计仪表板

2. **AI 模块 - 插件安装使用**
   - 可用插件列表浏览
   - 异步安装/卸载插件（事件驱动）
   - 启动/停止插件
   - 配置管理
   - 运行时状态监控
   - 安装任务追踪
   - 统计仪表板

3. **权限控制**
   - Tenant: `tenant:plugin:read`、`tenant:plugin:write`
   - AI: `ai:plugin:read`、`ai:plugin:write`、`ai:plugin:delete`

### 数据模型变更

- `tenant.plugin_definitions`：新增 `is_recommended`、`is_enabled` 字段
- `ai.plugin_install_tasks`：新增安装任务表

### 存储策略

- 所有插件包统一上传到 MinIO（bucket: `plugins`）
- Object Key 格式：`{plugin_id}/{version}.zip`

### 后续迭代（不在本次范围）

- 远程 URL 拉取注册
- Docker/.venv 隔离策略
- 配额管理、插件市场、审批流程

## 功能 (Capabilities)

### 新增功能

- `plugin-definition-management`: 平台管理员注册、查询、管理插件定义的全生命周期
- `plugin-installation-workflow`: 租户管理员安装、卸载插件的异步工作流，包含任务追踪
- `plugin-runtime-management`: 插件运行时管理，包括启动、停止、配置、监控
- `plugin-statistics-dashboard`: 插件统计数据展示，包含定义侧和安装侧统计

## 影响

### 受影响模块

| 模块 | 影响范围 |
|------|----------|
| tenant | 新增插件定义管理功能、数据模型变更、新增 API 端点 |
| ai | 新增插件安装使用功能、新增数据模型、新增 API 端点 |
| iam | 新增权限定义（tenant:plugin:*、ai:plugin:*） |

### API 端点变更

**Tenant 管理侧（新增）**：
- `POST /tenant/admin/v1/plugin-definitions/scan` - 扫描服务器目录
- `POST /tenant/admin/v1/plugin-definitions/upload` - 上传插件包
- `GET /tenant/admin/v1/plugin-definitions` - 插件定义列表
- `GET /tenant/admin/v1/plugin-definitions/{id}` - 插件定义详情
- `PATCH /tenant/admin/v1/plugin-definitions/{id}` - 标记推荐/禁用
- `DELETE /tenant/admin/v1/plugin-definitions/{id}` - 删除插件定义
- `GET /tenant/admin/v1/plugin-definitions/statistics` - 统计数据

**AI 使用侧（新增）**：
- `GET /ai/console/v1/plugins/available` - 可用插件列表
- `POST /ai/console/v1/plugins/installations` - 安装插件
- `GET /ai/console/v1/plugins/installations` - 已安装列表
- `GET /ai/console/v1/plugins/installations/{id}` - 插件详情
- `DELETE /ai/console/v1/plugins/installations/{id}` - 卸载插件
- `POST /ai/console/v1/plugins/installations/{id}/start` - 启动插件
- `POST /ai/console/v1/plugins/installations/{id}/stop` - 停止插件
- `GET /ai/console/v1/plugins/installations/{id}/config` - 获取配置
- `PATCH /ai/console/v1/plugins/installations/{id}/config` - 更新配置
- `GET /ai/console/v1/plugins/installations/{id}/runtime-state` - 运行时状态
- `GET /ai/console/v1/plugins/runtime-states` - 批量运行时状态
- `GET /ai/console/v1/plugins/install-tasks` - 安装任务列表
- `GET /ai/console/v1/plugins/install-tasks/{id}` - 安装任务详情
- `GET /ai/console/v1/plugins/statistics` - 统计数据

### 数据库迁移

- `tenant.plugin_definitions`：新增字段 `is_recommended`、`is_enabled`
- `ai.plugin_install_tasks`：新建表

### 依赖项

- MinIO：插件包存储
- Redis Stream：安装任务队列
- 现有 `PluginInstallationProvider` 协议将继续使用

### 兼容性考虑

- 现有 `TenantPluginDefinition` 和 `TenantPluginInstallation` 数据模型将新增字段，需数据库迁移
- 新增权限定义需在 `iam` 模块注册
- 插件安装流程改为异步，API 响应结构变化（返回 task_id）
