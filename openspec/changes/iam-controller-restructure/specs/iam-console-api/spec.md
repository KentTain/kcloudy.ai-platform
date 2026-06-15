## 新增需求

### 需求:用户端认证 API
系统必须在 `/console/v1/iam/auth` 路径下提供认证接口。

#### 场景:用户登录
- **当** 用户发送 POST /console/v1/iam/auth/login 包含账号和密码
- **那么** 系统验证凭据并返回 access_token 和 refresh_token

#### 场景:用户登出
- **当** 用户发送 POST /console/v1/iam/auth/logout 携带有效 Token
- **那么** 系统将 Token 加入黑名单

#### 场景:刷新 Token
- **当** 用户发送 POST /console/v1/iam/auth/token/refresh 包含 refresh_token
- **那么** 系统返回新的 access_token

### 需求:用户端 OAuth API
系统必须在 `/console/v1/iam/oauth` 路径下提供第三方 OAuth 登录接口。

#### 场景:获取 OAuth 授权链接
- **当** 用户发送 GET /console/v1/iam/oauth/{provider}
- **那么** 系统返回第三方 OAuth2 授权页面 URL

#### 场景:OAuth 回调处理
- **当** 第三方回调 GET /console/v1/iam/oauth/{provider}/callback 包含 code 和 state
- **那么** 系统完成 OAuth 登录并返回 Token

#### 场景:OAuth 用户补全信息
- **当** OAuth 用户发送 POST /console/v1/iam/oauth/complete-profile 包含补全信息
- **那么** 系统更新用户资料

### 需求:用户端个人信息 API
系统必须在 `/console/v1/iam/users` 路径下提供用户个人信息管理接口。

#### 场景:用户注册
- **当** 用户发送 POST /console/v1/iam/users/register 包含注册信息
- **那么** 系统创建账号并自动登录返回 Token

#### 场景:获取当前用户信息
- **当** 登录用户发送 GET /console/v1/iam/users/me
- **那么** 系统返回当前用户详情含角色和权限

#### 场景:修改当前用户信息
- **当** 登录用户发送 PUT /console/v1/iam/users/me 包含更新信息
- **那么** 系统更新用户资料

#### 场景:修改密码
- **当** 登录用户发送 PUT /console/v1/iam/users/password 包含旧密码和新密码
- **那么** 系统验证旧密码后更新密码

#### 场景:发送密码重置验证码
- **当** 用户发送 POST /console/v1/iam/users/password/reset-code 包含邮箱或手机号
- **那么** 系统发送 6 位验证码

#### 场景:重置密码
- **当** 用户发送 POST /console/v1/iam/users/password/reset 包含验证码和新密码
- **那么** 系统验证码后重置密码

### 需求:用户端菜单 API
系统必须在 `/console/v1/iam/users/menus` 路径下提供当前用户菜单查询接口。

#### 场景:获取当前用户菜单
- **当** 登录用户发送 GET /console/v1/iam/users/menus
- **那么** 系统返回该用户有权限访问的菜单树

#### 场景:用户无菜单权限
- **当** 登录用户没有任何菜单权限
- **那么** 系统返回空数组

#### 场景:未登录用户
- **当** 未登录用户请求菜单列表
- **那么** 系统返回 401 错误
