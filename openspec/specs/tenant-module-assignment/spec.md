# tenant-module-assignment Specification

## Purpose
TBD - created by syncing change tenant-admin-frontend. Update Purpose after archive.

## Requirements

### Requirement: 管理员可以查看租户已分配模块

系统 SHALL 允许管理员查看租户已分配的模块列表。

#### Scenario: 查询租户模块列表
- **WHEN** 管理员请求 GET /admin/v1/tenants/{id}/modules
- **THEN** 系统返回租户已分配的模块列表

#### Scenario: 显示模块分配状态
- **WHEN** 系统返回模块列表
- **THEN** 每个模块包含分配时间、过期时间、启用状态

### Requirement: 管理员可以为租户分配模块

系统 SHALL 允许管理员为租户分配模块。

#### Scenario: 分配模块
- **WHEN** 管理员请求 POST /admin/v1/tenants/{id}/modules 并提供模块 ID
- **THEN** 系统为租户分配模块，创建租户实例层数据

#### Scenario: 分配已存在的模块
- **WHEN** 管理员尝试分配租户已拥有的模块
- **THEN** 系统返回错误（唯一约束冲突）

#### Scenario: 分配不存在的模块
- **WHEN** 管理员分配的模块 ID 不存在
- **THEN** 系统返回 404 错误

#### Scenario: 分配未启用的模块
- **WHEN** 管理员分配 is_active=false 的模块
- **THEN** 系统返回错误 "模块未启用"

#### Scenario: 必须模块设置过期时间
- **WHEN** 管理员为 is_need=true 的模块设置过期时间
- **THEN** 系统返回错误 "必须模块不可设置过期时间"

### Requirement: 管理员可以取消租户模块分配

系统 SHALL 允许管理员取消租户的模块分配。

#### Scenario: 取消模块分配
- **WHEN** 管理员请求 DELETE /admin/v1/tenants/{id}/modules/{moduleId}
- **THEN** 系统取消模块分配，删除租户实例层数据

#### Scenario: 取消必须模块分配
- **WHEN** 管理员尝试取消 is_need=true 的模块
- **THEN** 系统返回错误 "必须模块禁止取消"

#### Scenario: 取消有用户使用的模块
- **WHEN** 管理员取消有用户使用该模块角色的模块
- **THEN** 系统返回错误，提示先移除相关用户角色

### Requirement: 租户详情页提供模块分配 Tab

系统 SHALL 在租户详情页提供模块分配 Tab，展示租户已分配的模块列表。

#### Scenario: 显示模块分配 Tab
- **WHEN** 管理员进入租户详情页并点击「模块分配」Tab
- **THEN** 页面显示租户已分配的模块列表

#### Scenario: 分配模块弹窗
- **WHEN** 管理员点击「分配模块」按钮
- **THEN** 系统弹出模块分配表单，显示可分配的模块列表

#### Scenario: 取消分配确认
- **WHEN** 管理员点击「取消分配」按钮
- **THEN** 系统弹出确认对话框，提示取消分配的影响

#### Scenario: 查看模块详情
- **WHEN** 管理员点击模块名称
- **THEN** 系统跳转到模块详情页
