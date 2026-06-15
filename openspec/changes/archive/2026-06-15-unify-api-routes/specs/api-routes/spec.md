## 新增需求

### 需求:模块优先路由规则

所有 API 路由必须遵循模块优先的路由规则：`/{模块}/{类型}/v1/{功能}/{其他}`

- **模块**：`tenant`、`iam`、`ai`
- **类型**：`admin`（管理端）、`console`（用户端）、`inner`（内部接口）
- **v1**：API 版本号
- **功能**：资源名称，如 `users`、`tenants`、`chat-messages`

#### 场景:Tenant 模块路由

- **当** 访问 Tenant 模块的管理端租户管理功能
- **那么** 路由必须为 `/tenant/admin/v1/tenants`

#### 场景:IAM 模块路由

- **当** 访问 IAM 模块的用户端认证功能
- **那么** 路由必须为 `/iam/console/v1/auth/login`

#### 场景:AI 模块路由

- **当** 访问 AI 模块的用户端对话功能
- **那么** 路由必须为 `/ai/console/v1/chat-messages`

### 需求:路由路径必须包含模块名

所有 API 路由路径必须以模块名开头，禁止出现不包含模块名的路由。

#### 场景:禁止无模块名的路由

- **当** 定义一个 API 路由
- **那么** 路由路径必须以 `/tenant/`、`/iam/` 或 `/ai/` 开头
- **禁止** 使用 `/admin/v1/`、`/console/v1/`、`/api/v1/` 等无模块名的路径

### 需求:移除特殊路由前缀

禁止使用 `/api/v1/*` 路由前缀，所有路由必须统一到模块优先结构。

#### 场景:AI 对话路由迁移

- **当** 访问 AI 对话功能
- **那么** 路由必须为 `/ai/console/v1/chat-messages`
- **禁止** 使用 `/api/v1/chat-messages` 路径

### 需求:路由注册使用模块声明

所有模块的路由必须通过 `module.py` 的 `get_routers()` 方法注册，禁止在 `application_web.py` 中硬编码路由。

#### 场景:模块路由注册

- **当** 一个模块需要注册 API 路由
- **那么** 必须在模块的 `module.py` 文件中实现 `get_routers()` 方法
- **那么** 方法返回格式必须为 `[(router, prefix, tags), ...]`
- **那么** prefix 必须包含完整的模块前缀，如 `/tenant/admin/v1`

### 需求:前端 API 路径同步

前端 API 调用路径必须与后端路由规则保持一致。

#### 场景:前端 API 路径格式

- **当** 前端调用后端 API
- **那么** 请求路径必须为 `/api/{模块}/{类型}/v1/{功能}`
- **那么** `baseURL` 必须保持为 `/api`

#### 场景:前端 Token 选择

- **当** 前端调用 `/tenant/admin/*` 路由
- **那么** 必须使用租户管理员 Token（`rawGet`、`rawPost` 等）

- **当** 前端调用 `/iam/*`、`/ai/*`、`/tenant/console/*` 路由
- **那么** 必须使用 JWT Token（`get`、`post` 等）
