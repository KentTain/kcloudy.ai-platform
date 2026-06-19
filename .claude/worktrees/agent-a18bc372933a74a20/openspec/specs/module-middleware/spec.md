# module-middleware 规范

## 目的
待定 - 由归档变更 unify-api-routes 创建。归档后请更新目的。
## 需求
### 需求:中间件按模块前缀加载

中间件必须根据请求路径的模块前缀自动选择认证方式，禁止硬编码路径判断。

#### 场景:Tenant 管理端认证

- **当** 请求路径以 `/tenant/admin/` 开头
- **那么** 必须使用 `AdminAuthMiddleware` 进行认证
- **那么** 必须验证租户管理员 Token

#### 场景:Tenant 用户端认证

- **当** 请求路径以 `/tenant/console/` 开头
- **那么** 必须使用 `IAMAuthMiddleware` 进行认证
- **那么** 必须验证 JWT Token

#### 场景:IAM 模块认证

- **当** 请求路径以 `/iam/` 开头
- **那么** 必须使用 `IAMAuthMiddleware` 进行认证
- **那么** 必须验证 JWT Token

#### 场景:AI 模块认证

- **当** 请求路径以 `/ai/` 开头
- **那么** 必须使用 `IAMAuthMiddleware` 进行认证
- **那么** 必须验证 JWT Token（复用 IAM 用户体系）

#### 场景:内部接口无认证

- **当** 请求路径以 `/tenant/inner/`、`/iam/inner/` 或 `/ai/inner/` 开头
- **那么** 必须跳过认证
- **那么** 允许模块间内部调用

### 需求:豁免路径声明

中间件必须在代码中声明豁免路径，禁止硬编码完整的请求路径。

#### 场景:登录接口豁免

- **当** 请求路径为 `/tenant/admin/v1/auth/login`
- **那么** `AdminAuthMiddleware` 必须跳过认证
- **那么** 允许未认证用户访问

- **当** 请求路径为 `/iam/console/v1/auth/login`
- **那么** `IAMAuthMiddleware` 必须跳过认证
- **那么** 允许未认证用户访问

#### 场景:Token 刷新豁免

- **当** 请求路径为 `/iam/console/v1/auth/token/refresh`
- **那么** `IAMAuthMiddleware` 必须跳过认证
- **那么** 允许使用 Refresh Token 刷新

### 需求:中间件执行顺序

中间件必须按照正确的顺序执行：`TenantMiddleware` → `模块认证中间件` → `业务处理`。

#### 场景:中间件执行顺序

- **当** 一个请求进入系统
- **那么** `TenantMiddleware` 必须首先执行，解析租户 ID
- **那么** 模块认证中间件必须根据路径前缀选择执行
- **那么** 业务处理器最后执行

#### 场景:已认证请求跳过

- **当** 请求已被前序中间件标记为已认证（`request.state.authenticated = True`）
- **那么** 后续认证中间件必须跳过认证逻辑
- **那么** 直接执行业务处理

### 需求:AdminAuthMiddleware 路径匹配

`AdminAuthMiddleware` 必须只处理 `/tenant/admin/*` 路径，其他路径必须跳过。

#### 场景:只处理 Tenant 管理端

- **当** 请求路径为 `/tenant/admin/v1/tenants`
- **那么** `AdminAuthMiddleware` 必须验证租户管理员 Token

- **当** 请求路径为 `/iam/admin/v1/users`
- **那么** `AdminAuthMiddleware` 必须跳过，由 `IAMAuthMiddleware` 处理

### 需求:IAMAuthMiddleware 路径匹配

`IAMAuthMiddleware` 必须处理 `/iam/*`、`/ai/*`、`/tenant/console/*` 路径。

#### 场景:处理 IAM 模块

- **当** 请求路径以 `/iam/` 开头
- **那么** `IAMAuthMiddleware` 必须验证 JWT Token

#### 场景:处理 AI 模块

- **当** 请求路径以 `/ai/` 开头
- **那么** `IAMAuthMiddleware` 必须验证 JWT Token

#### 场景:处理 Tenant 用户端

- **当** 请求路径以 `/tenant/console/` 开头
- **那么** `IAMAuthMiddleware` 必须验证 JWT Token

