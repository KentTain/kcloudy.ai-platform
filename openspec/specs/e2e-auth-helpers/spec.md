## 新增需求

### 需求:管理员 API 辅助登录

系统必须提供通过后端 API 完成管理员认证的辅助函数，绕过 UI 登录流程，将 Token 直接注入浏览器存储。

#### 场景:管理员成功登录并注入 Token
- **当** 调用 `adminLoginViaAPI(page, request, 'admin', 'admin123')`
- **那么** 系统向 `/api/tenant/admin/v1/auth/login` 发送 POST 请求
- **那么** 系统从响应中获取 `token` 字段
- **那么** 系统调用 `/api/tenant/admin/v1/admin/me` 获取完整管理员信息
- **那么** 系统将 `admin_token`、`admin_info`、`admin_menus`、`admin_permissions`、`admin_role` 写入 localStorage
- **那么** 后续页面访问自动携带认证信息

#### 场景:登录失败时抛出明确错误
- **当** 调用 `adminLoginViaAPI` 使用错误的凭据
- **那么** 函数抛出包含 HTTP 状态码和错误消息的异常

### 需求:用户端 API 辅助登录

系统必须提供 IAM 用户端的 API 辅助登录函数，支持 `X-Tenant-Id` 请求头注入。

#### 场景:用户成功登录并注入 Token
- **当** 调用 `userLoginViaAPI(page, request, 'admin', 'admin123')`
- **那么** 系统向 `/api/iam/console/v1/auth/login` 发送 POST 请求（请求体使用 `account` 字段）
- **那么** 系统从响应中获取 `access_token` 和 `tenant_id`
- **那么** 系统调用 `/api/iam/console/v1/users/me`（携带 `Authorization` 和 `X-Tenant-Id` 请求头）
- **那么** 系统将 `token` 和 `tenant_id` 写入 localStorage

### 需求:Token 存储常量

系统必须定义与前端源码一致的 Token 存储键名常量。

#### 场景:常量与源码一致
- **当** 测试代码引用 `ADMIN_TOKEN_KEY` 常量
- **那么** 其值必须等于 `"admin_token"`
- **那么** 其他常量（`ADMIN_INFO_KEY`、`ADMIN_MENUS_KEY` 等）同理
