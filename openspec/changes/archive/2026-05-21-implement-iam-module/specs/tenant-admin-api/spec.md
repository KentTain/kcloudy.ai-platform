## ADDED Requirements

### Requirement: 管理员密码安全存储

系统 SHALL 使用 BCrypt 算法存储租户管理员密码哈希。

#### Scenario: 密码哈希存储
- **WHEN** 创建或修改租户管理员密码
- **THEN** 使用 BCrypt（cost factor = 12）计算哈希值并存储

#### Scenario: 密码验证
- **WHEN** 租户管理员登录时验证密码
- **THEN** 使用 BCrypt 比对输入密码与存储的哈希值
