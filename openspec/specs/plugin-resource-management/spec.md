## 目的

定义租户模块对插件资源的管理能力，包括全局插件注册表和租户级安装记录的管理，
实现"有什么"（资源定义）与"用什么"（运行时配置）的职责分离。

## 新增需求

### 需求:Tenant 模块管理插件定义

Tenant 模块必须维护全局插件注册表（`plugin_definitions`），存储所有已安装插件的定义信息，包括插件 ID、唯一标识符、声明内容、引用计数和安装类型。

#### 场景:创建新插件定义

- **当** 租户首次安装某个插件
- **那么** Tenant 模块必须在 `plugin_definitions` 表中创建新记录，`refers` 初始化为 1

#### 场景:增加插件引用计数

- **当** 其他租户安装已存在的插件
- **那么** Tenant 模块必须递增该插件的 `refers` 字段

### 需求:Tenant 模块管理安装记录

Tenant 模块必须维护租户级插件安装记录（`plugin_installations`），仅包含管理面字段，包括租户 ID、插件 ID、状态、自动启动配置和冻结阈值。

#### 场景:创建安装记录

- **当** 租户安装插件
- **那么** Tenant 模块必须在 `plugin_installations` 表中创建记录，初始状态为 `PENDING`

#### 场景:更新安装状态为激活

- **当** AI 模块成功完成插件配置
- **那么** Tenant 模块必须将安装记录状态更新为 `ACTIVE`

#### 场景:更新安装状态为失败

- **当** AI 模块插件配置失败
- **那么** Tenant 模块必须将安装记录状态更新为 `FAILED`

#### 场景:禁用已激活的插件

- **当** 管理员通过 Web API 禁用插件
- **那么** Tenant 模块必须将安装记录状态从 `ACTIVE` 更新为 `INACTIVE`

#### 场景:启用已禁用的插件

- **当** 管理员通过 Web API 启用插件
- **那么** Tenant 模块必须将安装记录状态从 `INACTIVE` 更新为 `ACTIVE`

### 需求:提供 Inner API 访问安装记录

Tenant 模块必须实现 `PluginInstallationProvider` 协议，提供 CRUD 操作供 AI 模块访问安装记录，使用独立事务，不依赖 AI 模块的 Session。

#### 场景:查询租户所有安装记录

- **当** AI 模块调用 `get_tenant_installations(tenant_id)`
- **那么** Tenant 模块必须返回该租户所有安装记录的 DTO 列表

#### 场景:查询单个安装记录

- **当** AI 模块调用 `get_installation(tenant_id, plugin_id)`
- **那么** Tenant 模块必须返回对应的安装记录 DTO，如不存在则返回 `None`

#### 场景:创建安装记录

- **当** AI 模块调用 `create_installation(tenant_id, data)`
- **那么** Tenant 模块必须使用独立事务创建记录并返回 DTO

#### 场景:更新安装记录

- **当** AI 模块调用 `update_installation(tenant_id, plugin_id, data)`
- **那么** Tenant 模块必须使用独立事务更新记录并返回 DTO

#### 场景:删除安装记录

- **当** AI 模块调用 `delete_installation(tenant_id, plugin_id)`
- **那么** Tenant 模块必须使用独立事务删除记录

### 需求:多租户数据隔离

不同租户的安装记录必须严格隔离，一个租户无法访问或操作其他租户的安装记录。

#### 场景:租户 A 无法访问租户 B 的安装记录

- **当** AI 模块代表租户 A 调用 `get_installation(tenant_id_A, plugin_id)`
- **那么** 系统必须仅返回租户 A 的安装记录，不返回租户 B 的任何数据

#### 场景:租户 ID 唯一约束

- **当** 同一租户尝试安装同一插件两次
- **那么** 系统必须拒绝第二次安装（UNIQUE 约束冲突）

### 需求:清理失败的安装记录

系统必须定期清理处于 `FAILED` 状态超过 24 小时的安装记录，避免孤儿记录累积。

#### 场景:定时清理失败记录

- **当** 定时任务执行
- **那么** 系统必须删除所有 `status = 'FAILED'` 且 `created_at < NOW() - 24h` 的记录

### 需求:Web 管理端展示插件定义列表

Tenant 模块的 Web 管理端必须提供 API 端点展示所有已注册的插件定义，包括插件 ID、版本、引用租户数和安装类型。

#### 场景:查询插件定义列表

- **当** 管理员访问 `/admin/v1/tenants/plugins` 端点
- **那么** 系统必须返回所有插件定义列表，按引用数降序排列
