# 内部接口规范

## Purpose

提供 `/inner/v1/*` 路由前缀用于模块间内部通信，支持单体和微服务两种部署模式。

## Requirements

### Requirement: 内部接口路由前缀

系统 SHALL 提供 `/inner/v1/*` 路由前缀用于模块间内部通信。

#### Scenario: 路由注册

- **WHEN** 应用启动
- **THEN** 注册 `/inner/v1/*` 路由
- **AND** 路由不对外暴露（仅内部网络可访问）

#### Scenario: 路由隔离

- **WHEN** 配置网关或反向代理
- **THEN** 可配置禁止外网访问 `/inner/v1/*` 路由

### Requirement: 租户内部接口

系统 SHALL 在 Tenant 模块提供内部接口供其他模块调用。

#### Scenario: 获取单个租户

- **WHEN** 请求 `GET /inner/v1/tenants/{tenant_id}`
- **THEN** 返回指定租户的详细信息
- **AND** 不依赖 Token 认证
- **AND** tenant_id 由调用方显式传入

#### Scenario: 批量获取租户

- **WHEN** 请求 `POST /inner/v1/tenants/batch`
- **WITH** 请求体 `{"tenant_ids": ["id1", "id2"]}`
- **THEN** 返回多个租户的信息列表
- **AND** 返回顺序与请求顺序一致

#### Scenario: 验证租户访问权限

- **WHEN** 请求 `GET /inner/v1/tenants/{tenant_id}/validate?user_id={user_id}`
- **THEN** 返回布尔值表示用户是否有权访问该租户

#### Scenario: 租户不存在

- **WHEN** 请求 `GET /inner/v1/tenants/nonexistent`
- **THEN** 返回 HTTP 404
- **AND** 响应体包含错误信息

### Requirement: 用户内部接口

系统 SHALL 在 IAM 模块提供内部接口供其他模块调用。

#### Scenario: 获取单个用户

- **WHEN** 请求 `GET /inner/v1/users/{user_id}`
- **THEN** 返回指定用户的详细信息
- **AND** 不依赖 Token 认证
- **AND** user_id 由调用方显式传入

#### Scenario: 批量获取用户

- **WHEN** 请求 `POST /inner/v1/users/batch`
- **WITH** 请求体 `{"user_ids": ["id1", "id2"]}`
- **THEN** 返回多个用户的信息列表

#### Scenario: 获取用户部门

- **WHEN** 请求 `GET /inner/v1/users/{user_id}/departments`
- **THEN** 返回用户所属的部门列表

#### Scenario: 用户不存在

- **WHEN** 请求 `GET /inner/v1/users/nonexistent`
- **THEN** 返回 HTTP 404
- **AND** 响应体包含错误信息

### Requirement: 部门内部接口

系统 SHALL 在 IAM 模块提供部门内部接口供其他模块调用。

#### Scenario: 获取部门树

- **WHEN** 请求 `GET /inner/v1/departments/tree`
- **THEN** 返回完整的部门树结构

#### Scenario: 获取单个部门

- **WHEN** 请求 `GET /inner/v1/departments/{department_id}`
- **THEN** 返回指定部门的详细信息

### Requirement: 内部接口性能

系统 SHALL 保证内部接口的响应性能。

#### Scenario: 单次调用响应时间

- **WHEN** 调用内部接口
- **THEN** 响应时间 SHALL 不超过 100ms（单体模式）

#### Scenario: 批量调用效率

- **WHEN** 批量获取 100 个用户
- **THEN** 响应时间 SHALL 不超过 500ms
