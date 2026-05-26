## ADDED Requirements

### Requirement: 模块客户端封装

系统 SHALL 提供模块间调用的客户端封装，统一调用入口。

#### Scenario: TenantClient 封装

- **WHEN** 查看 `framework/clients/tenant_client.py`
- **THEN** 存在 `TenantClient` 类
- **AND** 提供 `get_tenant()`、`get_tenants_batch()`、`validate_access()` 方法

#### Scenario: IamClient 封装

- **WHEN** 查看 `framework/clients/iam_client.py`
- **THEN** 存在 `IamClient` 类
- **AND** 提供 `get_user()`、`get_users_batch()`、`get_user_departments()` 方法

### Requirement: 混合调用模式支持

系统 SHALL 支持单体模式和微服务模式的调用切换。

#### Scenario: 单体模式调用

- **WHEN** 配置文件中未设置 `IAM_INNER_URL`
- **THEN** IamClient 直接调用 `iam.services.UserService`
- **AND** 不产生网络请求

#### Scenario: 微服务模式调用

- **WHEN** 配置文件中设置 `IAM_INNER_URL=http://iam-service:8001`
- **THEN** IamClient 发起 HTTP 请求到指定地址
- **AND** 请求路径为 `/inner/v1/users/{id}`

#### Scenario: 模式配置热切换

- **WHEN** 修改配置文件中的 `IAM_INNER_URL`
- **THEN** 重启服务后调用模式切换
- **AND** 无需修改代码

### Requirement: 配置管理

系统 SHALL 提供模块间调用的配置项。

#### Scenario: 配置项定义

- **WHEN** 查看 `config/application.yml`
- **THEN** 存在 `iam.inner_url` 和 `iam.inner_timeout` 配置项
- **AND** 存在 `tenant.inner_url` 和 `tenant.inner_timeout` 配置项

#### Scenario: 默认配置

- **WHEN** 未配置 `inner_url`
- **THEN** 默认使用单体模式（本地 Service 调用）

#### Scenario: 超时配置

- **WHEN** 配置 `iam.inner_timeout=30`
- **THEN** HTTP 调用超时时间为 30 秒

### Requirement: 错误处理

系统 SHALL 提供统一的错误处理机制。

#### Scenario: 服务不可用

- **WHEN** 微服务模式下目标服务不可用
- **THEN** 抛出 `InnerServiceUnavailableError` 异常
- **AND** 包含服务名称和错误详情

#### Scenario: 调用超时

- **WHEN** HTTP 调用超时
- **THEN** 抛出 `InnerServiceTimeoutError` 异常
- **AND** 包含超时时间信息

#### Scenario: 资源不存在

- **WHEN** 内部接口返回 404
- **THEN** 返回 `None` 或抛出 `NotFoundError`（根据方法语义）

### Requirement: 健康检查

系统 SHALL 提供内部接口健康检查。

#### Scenario: 健康检查端点

- **WHEN** 请求 `GET /inner/v1/health`
- **THEN** 返回 `{"status": "healthy"}`
- **AND** 不依赖外部服务

#### Scenario: 客户端健康检查

- **WHEN** 调用 `IamClient.health_check()`
- **THEN** 返回布尔值表示服务是否可用
