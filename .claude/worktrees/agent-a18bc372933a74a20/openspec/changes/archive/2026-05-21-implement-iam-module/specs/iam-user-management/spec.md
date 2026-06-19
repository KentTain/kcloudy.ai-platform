## ADDED Requirements

### Requirement: 用户注册

系统 SHALL 支持用户自主注册账号。

#### Scenario: 注册成功
- **WHEN** 用户请求 `POST /api/v1/iam/register` 并提供用户名、密码
- **THEN** 创建用户账号并返回 Access Token 和 Refresh Token

#### Scenario: 用户名已存在
- **WHEN** 用户使用已存在的用户名注册
- **THEN** 返回 HTTP 400，错误消息为"用户名已存在"

#### Scenario: 密码强度校验
- **WHEN** 用户注册时密码长度小于 8 位或不包含字母和数字
- **THEN** 返回 HTTP 400，错误消息为"密码长度需 8-32 位，且包含字母和数字"

#### Scenario: 邮箱格式校验
- **WHEN** 用户注册时提供无效邮箱格式
- **THEN** 返回 HTTP 400，错误消息为"邮箱格式无效"

#### Scenario: 手机号格式校验
- **WHEN** 用户注册时提供无效手机号格式
- **THEN** 返回 HTTP 400，错误消息为"手机号格式无效"

### Requirement: 获取当前用户信息

系统 SHALL 支持获取当前登录用户的详细信息。

#### Scenario: 获取用户信息成功
- **WHEN** 用户请求 `GET /api/v1/iam/user/me` 并携带有效 Token
- **THEN** 返回用户 ID、用户名、昵称、邮箱、手机号、头像等信息

#### Scenario: 未登录访问
- **WHEN** 未携带 Token 请求 `GET /api/v1/iam/user/me`
- **THEN** 返回 HTTP 401

### Requirement: 修改用户信息

系统 SHALL 支持用户修改自己的基本信息。

#### Scenario: 修改昵称成功
- **WHEN** 用户请求 `PUT /api/v1/iam/user/me` 并提供新昵称
- **THEN** 更新用户昵称并返回更新后的用户信息

#### Scenario: 修改邮箱成功
- **WHEN** 用户请求 `PUT /api/v1/iam/user/me` 并提供新邮箱和验证码
- **THEN** 更新用户邮箱并标记邮箱已验证

#### Scenario: 修改手机号成功
- **WHEN** 用户请求 `PUT /api/v1/iam/user/me` 并提供新手机号和验证码
- **THEN** 更新用户手机号并标记手机已验证

### Requirement: 修改密码

系统 SHALL 支持用户修改自己的密码。

#### Scenario: 修改密码成功
- **WHEN** 用户请求 `PUT /api/v1/iam/user/password` 并提供正确的旧密码和新密码
- **THEN** 更新密码哈希并返回成功

#### Scenario: 旧密码错误
- **WHEN** 用户请求修改密码时提供的旧密码不正确
- **THEN** 返回 HTTP 400，错误消息为"原密码错误"

#### Scenario: 修改密码后登出其他设备
- **WHEN** 用户成功修改密码
- **THEN** 其他设备的 Token 失效，仅当前会话有效

### Requirement: 重置密码

系统 SHALL 支持用户通过邮箱或手机号重置忘记的密码。

#### Scenario: 发送重置验证码
- **WHEN** 用户请求 `POST /api/v1/iam/password/reset-code` 并提供邮箱或手机号
- **THEN** 发送 6 位验证码，有效期 5 分钟

#### Scenario: 验证码发送限流
- **WHEN** 同一账号在 1 分钟内多次请求发送验证码
- **THEN** 返回 HTTP 429，错误消息为"发送过于频繁，请稍后再试"

#### Scenario: 重置密码成功
- **WHEN** 用户请求 `POST /api/v1/iam/password/reset` 并提供正确的验证码和新密码
- **THEN** 更新密码哈希并使所有设备登出

#### Scenario: 验证码错误
- **WHEN** 用户重置密码时提供的验证码不正确
- **THEN** 返回 HTTP 400，错误消息为"验证码错误"

#### Scenario: 验证码过期
- **WHEN** 用户使用已过期的验证码重置密码
- **THEN** 返回 HTTP 400，错误消息为"验证码已过期"

### Requirement: 用户账号状态

系统 SHALL 支持用户账号的激活、停用和锁定状态。

#### Scenario: 激活状态用户登录
- **WHEN** 状态为 `active` 的用户登录
- **THEN** 正常返回 Token

#### Scenario: 停用状态用户登录
- **WHEN** 状态为 `inactive` 的用户登录
- **THEN** 返回 HTTP 403，错误消息为"账号已停用"

#### Scenario: 锁定状态用户登录
- **WHEN** 状态为 `locked` 的用户登录
- **THEN** 返回 HTTP 403，错误消息为"账号已锁定"
