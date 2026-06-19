## ADDED Requirements

### Requirement: 用户登录

系统 SHALL 支持用户通过用户名、邮箱或手机号进行密码登录。

#### Scenario: 用户名密码登录成功
- **WHEN** 用户使用正确的用户名和密码请求 `POST /api/v1/iam/login`
- **THEN** 返回 HTTP 200，包含 Access Token 和 Refresh Token

#### Scenario: 邮箱密码登录成功
- **WHEN** 用户使用正确的邮箱和密码请求 `POST /api/v1/iam/login`
- **THEN** 返回 HTTP 200，包含 Access Token 和 Refresh Token

#### Scenario: 手机号密码登录成功
- **WHEN** 用户使用正确的手机号和密码请求 `POST /api/v1/iam/login`
- **THEN** 返回 HTTP 200，包含 Access Token 和 Refresh Token

#### Scenario: 登录失败模糊提示
- **WHEN** 用户使用错误的用户名或密码登录
- **THEN** 返回 HTTP 401，错误消息为"用户名或密码错误"

#### Scenario: 用户不存在模糊提示
- **WHEN** 用户使用不存在的用户名登录
- **THEN** 返回 HTTP 401，错误消息为"用户名或密码错误"

#### Scenario: 登录限流
- **WHEN** 同一 IP 在 1 分钟内登录失败超过 5 次
- **THEN** 返回 HTTP 429，错误消息为"登录次数过多，请稍后再试"

### Requirement: 用户登出

系统 SHALL 支持用户主动登出，使当前 Token 失效。

#### Scenario: 登出成功
- **WHEN** 用户请求 `POST /api/v1/iam/logout` 并携带有效 Token
- **THEN** Token 加入黑名单，返回 HTTP 200

#### Scenario: 已登出 Token 不可用
- **WHEN** 用户使用已登出的 Token 访问受保护资源
- **THEN** 返回 HTTP 401

### Requirement: Token 刷新

系统 SHALL 支持 Refresh Token 刷新 Access Token。

#### Scenario: 刷新 Token 成功
- **WHEN** 用户使用有效的 Refresh Token 请求 `POST /api/v1/iam/token/refresh`
- **THEN** 返回新的 Access Token 和 Refresh Token

#### Scenario: Refresh Token 过期
- **WHEN** 用户使用已过期的 Refresh Token 请求刷新
- **THEN** 返回 HTTP 401，错误消息为"登录已过期，请重新登录"

#### Scenario: Refresh Token 已撤销
- **WHEN** 用户使用已撤销的 Refresh Token 请求刷新
- **THEN** 返回 HTTP 401

### Requirement: JWT Token 结构

系统 SHALL 使用 JWT 格式的 Access Token，包含用户基本权限信息。

#### Scenario: Token 包含必要信息
- **WHEN** 生成 Access Token
- **THEN** Token payload 包含 user_id、session_id、version、roles、permissions、exp

#### Scenario: Token 有效期内可用
- **WHEN** 用户在 Access Token 有效期（2 小时）内访问受保护资源
- **THEN** 系统正常处理请求

### Requirement: Redis 会话管理

系统 SHALL 使用 Redis 存储用户会话状态。

#### Scenario: 会话创建
- **WHEN** 用户登录成功
- **THEN** 在 Redis 创建会话记录，Key 为 `session:{session_id}`，TTL 为 7 天

#### Scenario: 会话验证
- **WHEN** 验证 Token 时 version 不匹配
- **THEN** 从 Redis 读取最新权限信息并更新 Token

#### Scenario: 会话销毁
- **WHEN** 用户登出
- **THEN** 删除 Redis 中的会话记录并将 Token 加入黑名单

### Requirement: 密码安全存储

系统 SHALL 使用 BCrypt 算法存储密码哈希。

#### Scenario: 密码哈希存储
- **WHEN** 用户设置或修改密码
- **THEN** 使用 BCrypt（cost factor = 12）计算哈希值并存储

#### Scenario: 密码验证
- **WHEN** 用户登录时验证密码
- **THEN** 使用 BCrypt 比对输入密码与存储的哈希值
