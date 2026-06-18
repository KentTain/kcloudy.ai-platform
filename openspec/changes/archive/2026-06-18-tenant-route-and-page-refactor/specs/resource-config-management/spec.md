# resource-config-management Specification (增量规范)

## 修改需求

### 需求: 管理员可以管理数据库配置

系统 SHALL 允许管理员对数据库配置进行创建、查询、更新、删除操作，并支持连通性测试。

**变更说明**：API 路由从 `/admin/v1/resource-configs/databases` 变更为 `/admin/v1/resources/databases`

#### Scenario: 查询数据库配置列表
- **WHEN** 管理员请求 GET /admin/v1/resources/databases
- **THEN** 系统返回数据库配置列表（分页）

#### Scenario: 创建数据库配置
- **WHEN** 管理员请求 POST /admin/v1/resources/databases 并提供配置信息
- **THEN** 系统创建数据库配置并返回配置信息

#### Scenario: 更新数据库配置
- **WHEN** 管理员请求 PUT /admin/v1/resources/databases/{id} 并提供更新数据
- **THEN** 系统更新配置并返回更新后的数据

#### Scenario: 删除数据库配置
- **WHEN** 管理员请求 DELETE /admin/v1/resources/databases/{id}
- **THEN** 系统删除配置

#### Scenario: 删除已被引用的配置
- **WHEN** 管理员尝试删除已被租户引用的配置
- **THEN** 系统返回错误，禁止删除

#### Scenario: 测试数据库连通性
- **WHEN** 管理员请求 POST /admin/v1/resources/databases/{id}/test-connection
- **THEN** 系统测试连接并返回测试结果（成功/失败/延迟）

### 需求: 管理员可以管理存储配置

系统 SHALL 允许管理员对存储配置进行创建、查询、更新、删除操作，并支持连通性测试。

**变更说明**：API 路由从 `/admin/v1/resource-configs/storages` 变更为 `/admin/v1/resources/storages`

#### Scenario: 查询存储配置列表
- **WHEN** 管理员请求 GET /admin/v1/resources/storages
- **THEN** 系统返回存储配置列表（分页）

#### Scenario: 创建存储配置
- **WHEN** 管理员请求 POST /admin/v1/resources/storages 并提供配置信息
- **THEN** 系统创建存储配置并返回配置信息

#### Scenario: 测试存储连通性
- **WHEN** 管理员请求 POST /admin/v1/resources/storages/{id}/test-connection
- **THEN** 系统检查 bucket 是否存在且可访问，返回测试结果

### 需求: 管理员可以管理缓存配置

系统 SHALL 允许管理员对缓存配置进行创建、查询、更新、删除操作，并支持连通性测试。

**变更说明**：API 路由从 `/admin/v1/resource-configs/caches` 变更为 `/admin/v1/resources/caches`

#### Scenario: 查询缓存配置列表
- **WHEN** 管理员请求 GET /admin/v1/resources/caches
- **THEN** 系统返回缓存配置列表（分页）

#### Scenario: 测试缓存连通性
- **WHEN** 管理员请求 POST /admin/v1/resources/caches/{id}/test-connection
- **THEN** 系统执行 PING 命令并返回测试结果

### 需求: 管理员可以管理队列配置

系统 SHALL 允许管理员对队列配置进行创建、查询、更新、删除操作，并支持连通性测试。

**变更说明**：API 路由从 `/admin/v1/resource-configs/queues` 变更为 `/admin/v1/resources/queues`

#### Scenario: 查询队列配置列表
- **WHEN** 管理员请求 GET /admin/v1/resources/queues
- **THEN** 系统返回队列配置列表（分页）

#### Scenario: 测试队列连通性
- **WHEN** 管理员请求 POST /admin/v1/resources/queues/{id}/test-connection
- **THEN** 系统根据队列类型执行连通性测试并返回结果

### 需求: 管理员可以管理发布订阅配置

系统 SHALL 允许管理员对发布订阅配置进行创建、查询、更新、删除操作，并支持连通性测试。

**变更说明**：API 路由从 `/admin/v1/resource-configs/pubsubs` 变更为 `/admin/v1/resources/pubsubs`

#### Scenario: 查询发布订阅配置列表
- **WHEN** 管理员请求 GET /admin/v1/resources/pubsubs
- **THEN** 系统返回发布订阅配置列表（分页）

#### Scenario: 测试发布订阅连通性
- **WHEN** 管理员请求 POST /admin/v1/resources/pubsubs/{id}/test-connection
- **THEN** 系统根据类型执行连通性测试并返回结果

### 需求: 资源配置页面提供统一界面

系统 SHALL 提供 Tab 切换的统一页面，支持在数据库、存储、缓存、队列、发布订阅五种类型间切换。

**变更说明**：前端路由从 `/admin/resource-configs` 变更为 `/admin/resources`

#### Scenario: 切换资源配置类型
- **WHEN** 管理员点击不同 Tab
- **THEN** 页面切换显示对应类型的配置列表

#### Scenario: 显示统计卡片
- **WHEN** 管理员进入资源配置页面
- **THEN** 页面顶部显示配置总数、已被引用数、未被使用数

### 需求: 资源配置表单弹窗

系统 SHALL 提供表单弹窗用于创建和编辑资源配置。

#### Scenario: 打开创建表单
- **WHEN** 管理员点击「新增配置」按钮
- **THEN** 系统弹出表单弹窗

#### Scenario: 提交表单验证失败
- **WHEN** 管理员提交表单但必填字段未填写
- **THEN** 系统显示验证错误提示

#### Scenario: 提交表单成功
- **WHEN** 管理员提交有效表单数据
- **THEN** 系统创建/更新配置，关闭弹窗，刷新列表

## 新增需求

### 需求: 资源配置菜单路径必须更新

系统必须更新资源配置菜单的前端路由路径，确保菜单导航正确。

#### Scenario: 菜单路径更新
- **当** 数据库迁移脚本执行
- **那么** `tenant.module_menus` 表中 `tenant.resources` 菜单的 `path` 字段更新为 `/admin/resources`
- **且** `iam.menus` 表中 `tenant.resources` 菜单的 `path` 字段更新为 `/admin/resources`

#### Scenario: 前端菜单导航
- **当** 用户点击"资源配置"菜单
- **那么** 页面跳转到 `/admin/resources`
- **且** 正确显示资源配置管理页面

### 需求: API 路由变更必须同步前后端

系统必须确保前后端 API 路由路径保持一致，避免接口调用失败。

#### Scenario: 前端 API 调用更新
- **当** 前端调用资源配置 API
- **那么** 所有 API 请求路径使用新的 `/admin/v1/resources` 前缀
- **且** 后端正确处理请求

#### Scenario: API 文档更新
- **当** API 路由变更完成
- **那么** API 文档同步更新路由路径
- **且** 所有示例使用新路径
