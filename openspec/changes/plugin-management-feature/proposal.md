## 为什么

当前插件管理的职责分散在 AI 模块，Tenant 模块对插件资源无感知，导致：
- 管理分散：插件定义和安装记录混在同一张表
- 职责模糊："有什么"（资源定义）和"用什么"（运行时配置）未分离
- 配额不可控：Tenant 模块无法统一分配和限制 AI 资源

此变更将插件管理职责明确划分：Tenant 负责"有什么"（插件定义），AI 负责"用什么"（安装使用）。

## 变更内容

### 新增功能

**Tenant 模块**：
- 插件定义注册（服务器目录扫描、本地上传 zip 包、远程 URL 拉取）
- 插件定义管理（列表查询、详情查看、标记推荐/禁用）
- 插件定义统计（定义侧、安装侧各 3 个指标）

**AI 模块**：
- 可用插件浏览（从 Tenant 获取已注册的插件定义）
- 插件安装/卸载（事件驱动流程）
- 插件配置管理（plugin_config、runtime_config）
- 运行时状态监控（进程、内存、CPU、调用统计）
- 安装任务追踪
- 插件使用统计（状态、使用、运行时各 3 个指标）

### 修改功能

- 重构 AI 模块插件列表 API，从 Tenant Provider 获取插件定义
- 重构插件安装/卸载流程，使用事件驱动保证数据一致性

## 功能 (Capabilities)

### 新增功能

- `plugin-definition-management`: 插件定义管理功能，包括插件定义的注册（扫描/上传/远程拉取）、查询、标记推荐/禁用、统计
- `plugin-installation-management`: 插件安装使用功能，包括可用插件浏览、安装/卸载、启动/停止、配置管理、运行时监控、安装任务追踪、统计

### 修改功能

- `plugin-management`: 重构现有插件管理功能，将数据访问从 ORM 改为 Provider 模式，使用事件驱动保证一致性

## 影响

### 受影响模块

| 模块 | 影响 |
|------|------|
| tenant | 新增插件定义管理功能，新增 `plugin_definitions` 表，新增 Provider 实现 |
| ai | 重构插件管理功能，新增 `plugin_configs`、`plugin_runtime_states` 表，使用 Provider 访问 Tenant 数据 |

### 受影响 API

**Tenant 模块新增 API**：
- `POST /tenant/admin/v1/plugin-definitions/scan` - 扫描服务器目录注册
- `POST /tenant/admin/v1/plugin-definitions/upload` - 上传插件包注册
- `POST /tenant/admin/v1/plugin-definitions/fetch` - 远程 URL 拉取注册
- `GET /tenant/admin/v1/plugin-definitions` - 插件定义列表
- `GET /tenant/admin/v1/plugin-definitions/{plugin_id}` - 插件定义详情
- `PATCH /tenant/admin/v1/plugin-definitions/{plugin_id}` - 更新插件定义
- `DELETE /tenant/admin/v1/plugin-definitions/{plugin_id}` - 删除插件定义
- `GET /tenant/admin/v1/plugin-definitions/statistics` - 统计数据

**AI 模块新增 API**：
- `GET /ai/console/v1/plugins/available` - 可用插件列表
- `GET /ai/console/v1/plugins/installations/{plugin_id}/config` - 获取配置
- `PATCH /ai/console/v1/plugins/installations/{plugin_id}/config` - 更新配置
- `GET /ai/console/v1/plugins/installations/{plugin_id}/runtime-state` - 运行时状态
- `GET /ai/console/v1/plugins/runtime-states` - 批量运行时状态
- `GET /ai/console/v1/plugins/install-tasks` - 安装任务列表
- `GET /ai/console/v1/plugins/install-tasks/{task_id}` - 安装任务详情
- `GET /ai/console/v1/plugins/statistics` - 统计数据

**AI 模块修改 API**：
- `GET /ai/console/v1/plugins` - 重构为已安装插件列表
- `POST /ai/console/v1/plugins/installations` - 重构安装流程

### 数据库变更

**新增表**：
- `tenant.plugin_definitions` - 全局插件注册表
- `ai.plugin_configs` - 插件配置
- `ai.plugin_runtime_states` - 运行时状态

**迁移策略**：
- 阶段 P0：新增表和 Provider 实现，不影响现有功能
- 阶段 P1：重构 AI 模块代码使用 Provider，迁移数据
- 阶段 P2：删除旧表（`ai.plugins`、`ai.plugin_declarations`、`ai.plugin_installations`）

### 依赖关系

- AI 模块依赖 Tenant 模块的 `PluginInstallationProvider`
- 通过事件驱动保证跨模块数据一致性
