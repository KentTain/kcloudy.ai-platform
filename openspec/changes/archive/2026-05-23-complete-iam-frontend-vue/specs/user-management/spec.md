## ADDED Requirements

### Requirement: 租户上下文存储

系统 SHALL 在用户状态中存储租户上下文信息。

#### Scenario: 存储当前租户

- **WHEN** 用户登录成功
- **THEN** 系统存储当前租户 ID、名称、编码到用户状态

#### Scenario: 存储租户列表

- **WHEN** 用户属于多个租户
- **THEN** 系统存储用户的租户列表信息

#### Scenario: 获取当前租户

- **WHEN** 调用 `useUserStore().currentTenant`
- **THEN** 返回当前租户信息对象

### Requirement: 租户切换

系统 SHALL 支持用户在不同租户间切换。

#### Scenario: 切换租户

- **WHEN** 用户选择切换到其他租户
- **THEN** 系统更新当前租户信息并刷新 Token

#### Scenario: 切换后刷新状态

- **WHEN** 租户切换成功
- **THEN** 系统清除旧租户相关的缓存数据

### Requirement: 租户信息展示

系统 SHALL 在界面上展示租户信息。

#### Scenario: 顶部导航展示

- **WHEN** 用户登录后
- **THEN** 顶部导航栏展示当前租户名称

#### Scenario: 租户选择器

- **WHEN** 用户属于多个租户
- **THEN** 提供租户选择下拉框，支持快速切换

### Requirement: UserInfo 类型扩展

系统 SHALL 扩展 UserInfo 类型以包含租户信息。

#### Scenario: 类型定义

- **WHEN** 定义 UserInfo 接口
- **THEN** 包含 tenantId、tenantName、tenantCode 字段

#### Scenario: 类型兼容

- **WHEN** 使用扩展后的 UserInfo
- **THEN** 与现有代码保持向后兼容
