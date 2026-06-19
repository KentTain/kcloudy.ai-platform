# resource-config-management Specification

## Purpose
TBD - created by syncing change tenant-admin-frontend. Update Purpose after archive.

## Requirements

### Requirement: 管理员可以管理数据库配置

系统 SHALL 允许管理员对数据库配置进行创建、查询、更新、删除操作，并支持连通性测试。

#### Scenario: 查询数据库配置列表
- **WHEN** 管理员请求 GET /admin/v1/resource-configs/databases
- **THEN** 系统返回数据库配置列表（分页）

#### Scenario: 创建数据库配置
- **WHEN** 管理员请求 POST /admin/v1/resource-configs/databases 并提供配置信息
- **THEN** 系统创建数据库配置并返回配置信息

#### Scenario: 更新数据库配置
- **WHEN** 管理员请求 PUT /admin/v1/resource-configs/databases/{id} 并提供更新数据
- **THEN** 系统更新配置并返回更新后的数据

#### Scenario: 删除数据库配置
- **WHEN** 管理员请求 DELETE /admin/v1/resource-configs/databases/{id}
- **THEN** 系统删除配置

#### Scenario: 删除已被引用的配置
- **WHEN** 管理员尝试删除已被租户引用的配置
- **THEN** 系统返回错误，禁止删除

#### Scenario: 测试数据库连通性
- **WHEN** 管理员请求 POST /admin/v1/resource-configs/databases/{id}/test-connection
- **THEN** 系统测试连接并返回测试结果（成功/失败/延迟）

### Requirement: 管理员可以管理存储配置

系统 SHALL 允许管理员对存储配置进行创建、查询、更新、删除操作，并支持连通性测试。

#### Scenario: 查询存储配置列表
- **WHEN** 管理员请求 GET /admin/v1/resource-configs/storages
- **THEN** 系统返回存储配置列表（分页）

#### Scenario: 创建存储配置
- **WHEN** 管理员请求 POST /admin/v1/resource-configs/storages 并提供配置信息
- **THEN** 系统创建存储配置并返回配置信息

#### Scenario: 测试存储连通性
- **WHEN** 管理员请求 POST /admin/v1/resource-configs/storages/{id}/test-connection
- **THEN** 系统检查 bucket 是否存在且可访问，返回测试结果

### Requirement: 管理员可以管理缓存配置

系统 SHALL 允许管理员对缓存配置进行创建、查询、更新、删除操作，并支持连通性测试。

#### Scenario: 查询缓存配置列表
- **WHEN** 管理员请求 GET /admin/v1/resource-configs/caches
- **THEN** 系统返回缓存配置列表（分页）

#### Scenario: 测试缓存连通性
- **WHEN** 管理员请求 POST /admin/v1/resource-configs/caches/{id}/test-connection
- **THEN** 系统执行 PING 命令并返回测试结果

### Requirement: 管理员可以管理队列配置

系统 SHALL 允许管理员对队列配置进行创建、查询、更新、删除操作，并支持连通性测试。

#### Scenario: 查询队列配置列表
- **WHEN** 管理员请求 GET /admin/v1/resource-configs/queues
- **THEN** 系统返回队列配置列表（分页）

#### Scenario: 测试队列连通性
- **WHEN** 管理员请求 POST /admin/v1/resource-configs/queues/{id}/test-connection
- **THEN** 系统根据队列类型执行连通性测试并返回结果

### Requirement: 管理员可以管理发布订阅配置

系统 SHALL 允许管理员对发布订阅配置进行创建、查询、更新、删除操作，并支持连通性测试。

#### Scenario: 查询发布订阅配置列表
- **WHEN** 管理员请求 GET /admin/v1/resource-configs/pubsubs
- **THEN** 系统返回发布订阅配置列表（分页）

#### Scenario: 测试发布订阅连通性
- **WHEN** 管理员请求 POST /admin/v1/resource-configs/pubsubs/{id}/test-connection
- **THEN** 系统根据类型执行连通性测试并返回结果

### Requirement: 资源配置页面提供统一界面

系统 SHALL 提供 Tab 切换的统一页面，支持在数据库、存储、缓存、队列、发布订阅五种类型间切换。

#### Scenario: 切换资源配置类型
- **WHEN** 管理员点击不同 Tab
- **THEN** 页面切换显示对应类型的配置列表

#### Scenario: 显示统计卡片
- **WHEN** 管理员进入资源配置页面
- **THEN** 页面顶部显示配置总数、已被引用数、未被使用数

### Requirement: 资源配置表单弹窗

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
