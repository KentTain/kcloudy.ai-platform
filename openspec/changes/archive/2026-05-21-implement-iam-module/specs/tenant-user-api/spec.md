## ADDED Requirements

### Requirement: 用户信息与 IAM 模块同步

系统 SHALL 确保租户用户信息与 IAM 模块的用户表保持一致。

#### Scenario: 用户 ID 关联
- **WHEN** 用户-租户关联记录中的 user_id
- **THEN** 对应 IAM 模块 users 表中的用户 ID

### Requirement: 租户管理员角色

系统 SHALL 支持在租户内为用户分配系统管理员角色。

#### Scenario: 创建租户时创建系统管理员角色
- **WHEN** 租户管理员创建新租户
- **THEN** 自动创建该租户的"系统管理员"和"普通用户"角色
