## MODIFIED Requirements

### Requirement: 用户账号状态

系统 SHALL 支持用户账号的激活、停用和锁定状态，UI SHALL 使用 Badge 展示状态。

#### Scenario: 激活状态用户登录
- **WHEN** 状态为 `active` 的用户登录
- **THEN** 正常返回 Token

#### Scenario: 停用状态用户登录
- **WHEN** 状态为 `inactive` 的用户登录
- **THEN** 返回 HTTP 403，错误消息为"账号已停用"

#### Scenario: 锁定状态用户登录
- **WHEN** 状态为 `locked` 的用户登录
- **THEN** 返回 HTTP 403，错误消息为"账号已锁定"

#### Scenario: 用户列表状态 Badge 展示
- **WHEN** UserList 表格渲染用户状态列
- **THEN** SHALL 使用 Badge 替代 el-tag（active → variant="success", inactive → variant="destructive", locked → variant="warning"）