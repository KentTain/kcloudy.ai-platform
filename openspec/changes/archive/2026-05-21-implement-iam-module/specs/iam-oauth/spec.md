## ADDED Requirements

### Requirement: OAuth 授权链接获取

系统 SHALL 支持获取第三方 OAuth2 授权链接。

#### Scenario: 获取微信授权链接
- **WHEN** 用户请求 `GET /api/v1/iam/oauth/wechat`
- **THEN** 返回微信 OAuth2 授权链接

#### Scenario: 获取企微授权链接
- **WHEN** 用户请求 `GET /api/v1/iam/oauth/wework`
- **THEN** 返回企微 OAuth2 授权链接

#### Scenario: 不支持的 OAuth 提供商
- **WHEN** 用户请求不支持的 OAuth 提供商（如 `GET /api/v1/iam/oauth/google`）
- **THEN** 返回 HTTP 400，错误消息为"不支持的登录方式"

### Requirement: OAuth 回调处理

系统 SHALL 处理第三方 OAuth2 回调并完成登录。

#### Scenario: 微信登录成功-新用户
- **WHEN** 微信回调 `GET /api/v1/iam/oauth/wechat/callback?code=xxx`
- **THEN** 创建新用户并绑定微信 OpenID，返回 Token

#### Scenario: 微信登录成功-已有用户
- **WHEN** 已绑定微信的用户通过微信回调登录
- **THEN** 返回 Token，不重复创建用户

#### Scenario: 企微登录成功
- **WHEN** 企微回调 `GET /api/v1/iam/oauth/wework/callback?code=xxx`
- **THEN** 返回 Token

#### Scenario: 无效授权码
- **WHEN** OAuth 回调携带无效的 code 参数
- **THEN** 返回 HTTP 401，错误消息为"授权失败"

### Requirement: OAuth 用户信息补全

系统 SHALL 引导 OAuth 登录的新用户补全必要信息。

#### Scenario: 检测用户信息不完整
- **WHEN** OAuth 登录创建的用户缺少密码
- **THEN** 登录响应中包含 `need_complete_profile: true`

#### Scenario: 补全密码
- **WHEN** 用户请求 `POST /api/v1/iam/oauth/complete-profile` 并提供密码
- **THEN** 设置用户密码，标记 `profile_completed = true`

#### Scenario: 补全邮箱
- **WHEN** 用户请求补全信息时提供邮箱和验证码
- **THEN** 绑定邮箱并标记邮箱已验证

#### Scenario: 补全手机号
- **WHEN** 用户请求补全信息时提供手机号和验证码
- **THEN** 绑定手机号并标记手机已验证

#### Scenario: 已补全用户不提示
- **WHEN** 已完成信息补全的用户 OAuth 登录
- **THEN** 登录响应中不包含 `need_complete_profile` 字段

### Requirement: OAuth 账号绑定

系统 SHALL 支持一个用户绑定多个第三方账号。

#### Scenario: 绑定新 OAuth 账号
- **WHEN** 已登录用户请求绑定新的 OAuth 账号
- **THEN** 创建新的 OAuth 关联记录

#### Scenario: OAuth 账号已被绑定
- **WHEN** 用户尝试绑定已被其他用户绑定的 OAuth 账号
- **THEN** 返回 HTTP 400，错误消息为"该账号已被其他用户绑定"

### Requirement: OAuth Token 管理

系统 SHALL 管理 OAuth 获取的第三方 Token。

#### Scenario: 存储 OAuth Token
- **WHEN** 用户通过 OAuth 登录
- **THEN** 存储 access_token、refresh_token、expires_at 到 oauth_connections 表

#### Scenario: OAuth Token 过期处理
- **WHEN** OAuth access_token 过期
- **THEN** 使用 refresh_token 刷新获取新的 access_token
