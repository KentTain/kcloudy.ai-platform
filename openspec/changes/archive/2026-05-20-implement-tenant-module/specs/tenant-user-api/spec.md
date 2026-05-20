## ADDED Requirements

### Requirement: 获取可用租户列表

系统 SHALL 提供获取当前用户可用租户列表的 API。

#### Scenario: 获取用户可用租户列表
- **WHEN** 用户请求 `GET /console/v1/tenants`
- **THEN** 返回用户所属的所有租户列表

#### Scenario: 用户不属于任何租户
- **WHEN** 用户不属于任何租户时请求 `GET /console/v1/tenants`
- **THEN** 返回空列表

### Requirement: 获取当前租户信息

系统 SHALL 提供获取当前租户信息的 API。

#### Scenario: 获取当前租户信息
- **WHEN** 用户请求 `GET /console/v1/tenants/current`
- **THEN** 返回当前租户的详细信息

#### Scenario: 未设置租户上下文
- **WHEN** 用户未设置租户上下文时请求 `GET /console/v1/tenants/current`
- **THEN** 返回 HTTP 400 错误

### Requirement: 切换租户

系统 SHALL 提供租户切换 API。

#### Scenario: 切换到有权限的租户
- **WHEN** 用户请求 `POST /console/v1/tenants/{id}/switch` 且用户属于该租户
- **THEN** 返回包含新租户信息的 Token
- **AND** 后续请求使用新租户上下文

#### Scenario: 切换到无权限的租户
- **WHEN** 用户请求 `POST /console/v1/tenants/{id}/switch` 且用户不属于该租户
- **THEN** 返回 HTTP 403 错误，消息为 "无权访问该租户"

#### Scenario: 切换到不存在的租户
- **WHEN** 用户请求 `POST /console/v1/tenants/nonexistent/switch`
- **THEN** 返回 HTTP 404 错误

#### Scenario: 切换到已停用的租户
- **WHEN** 用户请求切换到状态为 `inactive` 的租户
- **THEN** 返回 HTTP 403 错误，消息为 "租户已停用"

### Requirement: 用户-租户关联模型

系统 SHALL 支持用户属于多个租户。

#### Scenario: 用户属于多个租户
- **WHEN** 用户被添加到多个租户
- **THEN** 用户可以切换到任意一个租户

#### Scenario: 设置默认租户
- **WHEN** 用户有多个租户时
- **THEN** 用户可以设置其中一个为默认租户
