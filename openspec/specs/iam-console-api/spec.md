# IAM Console API 规范

## Purpose

定义 IAM 用户端 API，提供认证、OAuth 登录、个人信息管理、菜单查询接口，供普通用户进行身份认证和个人信息管理。

## Requirements

### Requirement: 用户端认证 API

系统 SHALL 在 `/console/v1/iam/auth` 路径下提供认证接口。

#### Scenario: 用户登录
- **WHEN** 用户发送 POST /console/v1/iam/auth/login 包含账号和密码
- **THEN** 系统验证凭据并返回 access_token 和 refresh_token

#### Scenario: 用户登出
- **WHEN** 用户发送 POST /console/v1/iam/auth/logout 携带有效 Token
- **THEN** 系统将 Token 加入黑名单

#### Scenario: 刷新 Token
- **WHEN** 用户发送 POST /console/v1/iam/auth/token/refresh 包含 refresh_token
- **THEN** 系统返回新的 access_token

### Requirement: 用户端 OAuth API

系统 SHALL 在 `/console/v1/iam/oauth` 路径下提供第三方 OAuth 登录接口。

#### Scenario: 获取 OAuth 授权链接
- **WHEN** 用户发送 GET /console/v1/iam/oauth/{provider}
- **THEN** 系统返回第三方 OAuth2 授权页面 URL

#### Scenario: OAuth 回调处理
- **WHEN** 第三方回调 GET /console/v1/iam/oauth/{provider}/callback 包含 code 和 state
- **THEN** 系统完成 OAuth 登录并返回 Token

#### Scenario: OAuth 用户补全信息
- **WHEN** OAuth 用户发送 POST /console/v1/iam/oauth/complete-profile 包含补全信息
- **THEN** 系统更新用户资料

### Requirement: 用户端个人信息 API

系统 SHALL 在 `/console/v1/iam/users` 路径下提供用户个人信息管理接口。

#### Scenario: 用户注册
- **WHEN** 用户发送 POST /console/v1/iam/users/register 包含注册信息
- **THEN** 系统创建账号并自动登录返回 Token

#### Scenario: 获取当前用户信息
- **WHEN** 登录用户发送 GET /console/v1/iam/users/me
- **THEN** 系统返回当前用户详情含角色和权限

#### Scenario: 修改当前用户信息
- **WHEN** 登录用户发送 PUT /console/v1/iam/users/me 包含更新信息
- **THEN** 系统更新用户资料

#### Scenario: 修改密码
- **WHEN** 登录用户发送 PUT /console/v1/iam/users/password 包含旧密码和新密码
- **THEN** 系统验证旧密码后更新密码

#### Scenario: 发送密码重置验证码
- **WHEN** 用户发送 POST /console/v1/iam/users/password/reset-code 包含邮箱或手机号
- **THEN** 系统发送 6 位验证码

#### Scenario: 重置密码
- **WHEN** 用户发送 POST /console/v1/iam/users/password/reset 包含验证码和新密码
- **THEN** 系统验证码后重置密码

### Requirement: 用户端菜单 API

系统 SHALL 在 `/console/v1/iam/users/menus` 路径下提供当前用户菜单查询接口。

#### Scenario: 获取当前用户菜单
- **WHEN** 登录用户发送 GET /console/v1/iam/users/menus
- **THEN** 系统返回该用户有权限访问的菜单树

#### Scenario: 用户无菜单权限
- **WHEN** 登录用户没有任何菜单权限
- **THEN** 系统返回空数组

#### Scenario: 未登录用户
- **WHEN** 未登录用户请求菜单列表
- **THEN** 系统返回 401 错误
