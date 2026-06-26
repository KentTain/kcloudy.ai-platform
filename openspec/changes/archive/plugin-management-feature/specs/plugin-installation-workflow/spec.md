## 新增需求

### 需求:租户管理员可以浏览可用插件列表

系统必须支持租户管理员浏览 Tenant 模块已注册且启用的插件定义列表，并标记每个插件是否已安装。

#### 场景:成功获取可用插件列表
- **当** 租户管理员请求 `GET /ai/console/v1/plugins/available` 且提供分页参数
- **那么** 系统返回所有 `is_enabled=true` 的插件定义列表，每个插件包含 `is_installed` 和 `installation_status` 字段

#### 场景:按条件筛选可用插件列表
- **当** 租户管理员请求可用插件列表且提供 `keyword`、`type`、`is_recommended` 筛选参数
- **那么** 系统返回符合所有筛选条件的插件定义列表

### 需求:租户管理员可以异步安装插件

系统必须支持租户管理员异步安装插件。安装过程创建任务记录，通过 Redis Stream 队列执行，租户可以追踪任务进度。

#### 场景:成功发起安装请求
- **当** 租户管理员请求 `POST /ai/console/v1/plugins/installations` 且提供 `plugin_id`
- **那么** 系统创建 `plugin_install_tasks` 任务记录（状态 `pending`），创建 `plugin_installations` 记录（状态 `PENDING`），返回 `task_id`

#### 场景:安装任务消费者成功执行安装
- **当** 安装任务消费者从 Redis Stream 获取任务并成功执行安装
- **那么** 系统更新 `plugin_installations` 状态为 `ACTIVE`，更新 `plugin_install_tasks` 状态为 `completed`，初始化 `plugin_configs` 和 `plugin_runtime_states` 记录

#### 场景:安装任务消费者执行安装失败
- **当** 安装任务消费者执行安装失败
- **那么** 系统更新 `plugin_install_tasks` 状态为 `failed`，记录错误信息，发布 `PluginInstallationFailed` 事件

#### 场景:Tenant 监听器处理安装失败事件
- **当** Tenant 监听器收到 `PluginInstallationFailed` 事件
- **那么** 系统更新 `plugin_installations` 状态为 `FAILED` 或删除记录

#### 场景:安装插件时插件定义不存在
- **当** 租户管理员请求安装的 `plugin_id` 不存在于 `plugin_definitions` 表
- **那么** 系统返回 404 错误"插件定义不存在"

#### 场景:安装插件时插件定义已禁用
- **当** 租户管理员请求安装的插件定义 `is_enabled=false`
- **那么** 系统返回 400 错误"插件已禁用，无法安装"

#### 场景:重复安装同一插件
- **当** 租户管理员请求安装已安装的插件
- **那么** 系统返回 400 错误"插件已安装"

### 需求:租户管理员可以查看安装任务进度

系统必须支持租户管理员查看安装任务的详细进度，包括当前步骤、进度百分比、错误信息。

#### 场景:成功查询安装任务列表
- **当** 租户管理员请求 `GET /ai/console/v1/plugins/install-tasks`
- **那么** 系统返回当前租户的所有安装任务列表，包含任务 ID、插件 ID、状态、进度

#### 场景:成功查询安装任务详情
- **当** 租户管理员请求 `GET /ai/console/v1/plugins/install-tasks/{task_id}`
- **那么** 系统返回任务详情，包含步骤列表、日志、开始时间、完成时间

### 需求:租户管理员可以卸载插件

系统必须支持租户管理员卸载已安装的插件。卸载过程必须清理相关数据。

#### 场景:成功卸载插件
- **当** 租户管理员请求 `DELETE /ai/console/v1/plugins/installations/{plugin_id}` 且插件已安装
- **那么** 系统停止运行中的插件进程，删除 `plugin_configs`、`plugin_runtime_states`、`plugin_installations` 记录，递减 `plugin_definitions.refers`

#### 场景:卸载插件时插件未安装
- **当** 租户管理员请求卸载不存在的插件
- **那么** 系统返回 404 错误"插件未安装"

#### 场景:卸载失败时发布事件
- **当** 卸载过程失败
- **那么** 系统发布 `PluginUninstallFailed` 事件，Tenant 监听器记录失败日志

### 需求:安装任务必须有超时机制

系统必须对安装任务设置超时时间，超时后标记任务为失败。

#### 场景:安装任务超时
- **当** 安装任务执行时间超过 30 分钟
- **那么** 系统标记任务状态为 `failed`，错误信息为"安装任务超时"

### 需求:安装工作流必须有权限控制

系统必须对插件安装/卸载 API 进行权限校验，要求 `ai:plugin:read`、`ai:plugin:write` 或 `ai:plugin:delete` 权限。

#### 场景:无权限安装插件
- **当** 用户请求安装插件且没有 `ai:plugin:write` 权限
- **那么** 系统返回 403 错误"权限不足"

#### 场景:无权限卸载插件
- **当** 用户请求卸载插件且没有 `ai:plugin:delete` 权限
- **那么** 系统返回 403 错误"权限不足"

### 需求:安装任务表必须持久化任务状态

系统必须确保 `ai.plugin_install_tasks` 表正确记录任务状态和进度。

#### 场景:任务状态持久化
- **当** 安装任务状态变更（pending → running → completed/failed）
- **那么** 系统更新 `plugin_install_tasks` 表的 `status`、`progress`、`current_step`、`completed_at` 字段
