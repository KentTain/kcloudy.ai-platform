## MODIFIED Requirements

### Requirement: IAM 模块职责范围

系统 SHALL 将 IAM 模块职责限制在身份认证和访问控制领域，移除租户管理功能。

#### Scenario: 模块声明更新

- **WHEN** 查看 `iam/module.py`
- **THEN** `dependencies` 包含 `"tenant"`
- **AND** 不再注册 `/admin/v1/tenants` 和 `/console/v1/tenants` 路由

#### Scenario: 模型保留与移除

- **WHEN** 查看 `iam/models/` 目录
- **THEN** 保留 `user.py`、`role.py`、`permission.py`、`department.py`、`user_tenant.py`
- **AND** 不存在 `tenant.py`、`tenant_config.py`、`tenant_admin.py`

#### Scenario: UserTenant 模型保留

- **WHEN** 查看 `iam/models/user_tenant.py`
- **THEN** `UserTenant` 模型保留在 IAM 模块
- **AND** `tenant_id` 字段引用 `tenant.tenants`（跨 schema）

### Requirement: IAM 内部接口

系统 SHALL 在 IAM 模块新增内部接口层供其他模块调用。

#### Scenario: Inner 控制器目录

- **WHEN** 查看 `iam/controllers/` 目录
- **THEN** 存在 `inner/` 子目录
- **AND** 包含 `user_controller.py`、`department_controller.py`

#### Scenario: 用户内部接口

- **WHEN** 请求 `GET /inner/v1/users/{user_id}`
- **THEN** 返回用户详细信息
- **AND** 接口由 IAM 模块提供

## ADDED Requirements

### Requirement: IAM 模块依赖 Tenant 模块

系统 SHALL 在 IAM 模块声明对 Tenant 模块的依赖。

#### Scenario: 模块依赖声明

- **WHEN** 查看 `iam/module.py` 的 `dependencies`
- **THEN** 返回 `["tenant"]`

#### Scenario: 迁移顺序保证

- **WHEN** 执行 `python manage.py db migrate --all`
- **THEN** tenant 模块迁移先于 iam 模块执行
