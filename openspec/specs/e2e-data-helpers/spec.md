## 新增需求

### 需求:测试数据创建辅助函数

系统必须提供通过 API 创建测试数据的辅助函数，支持快速准备测试环境。

#### 场景:创建临时租户
- **当** 调用 `createTenantViaAPI(request, token, { name: 'e2e-test-xxx', code: 'e2e_xxx' })`
- **那么** 系统向 `/api/tenant/admin/v1/tenants` 发送 POST 请求
- **那么** 返回包含 `id`、`name`、`code` 的租户对象
- **那么** 租户名称自动添加 `e2e-` 前缀（如果未提供）

#### 场景:创建临时模块
- **当** 调用 `createModuleViaAPI(request, token, { name: 'Test Module', code: 'test_module' })`
- **那么** 系统向 `/api/tenant/admin/v1/modules` 发送 POST 请求
- **那么** 返回包含 `id` 的模块对象

#### 场景:创建临时用户
- **当** 调用 `createUserViaAPI(request, token, { username: 'e2e_user', ... })`
- **那么** 系统向 `/api/iam/console/v1/users` 发送 POST 请求
- **那么** 返回包含 `id` 的用户对象

### 需求:测试数据清理辅助函数

系统必须提供通过 API 删除测试数据的辅助函数，支持在测试完成后清理环境。

#### 场景:删除租户
- **当** 调用 `deleteTenantViaAPI(request, token, tenantId)`
- **那么** 系统向 `/api/tenant/admin/v1/tenants/{id}` 发送 DELETE 请求
- **那么** 不抛出异常（即使资源不存在）

#### 场景:删除模块
- **当** 调用 `deleteModuleViaAPI(request, token, moduleId)`
- **那么** 系统向 `/api/tenant/admin/v1/modules/{id}` 发送 DELETE 请求

#### 场景:删除用户
- **当** 调用 `deleteUserViaAPI(request, token, userId)`
- **那么** 系统向 `/api/iam/console/v1/users/{id}` 发送 DELETE 请求

### 需求:测试数据生命周期管理

系统必须支持测试数据的完整生命周期管理，确保清理代码始终执行。

#### 场景:使用 try-finally 保证清理
- **当** 测试代码使用 `try { ... } finally { await cleanup(); }` 模式
- **那么** 即使测试断言失败，清理代码也必须执行

#### 场景:批量清理残留数据
- **当** 调用 `cleanupAllE2EData(request, token)`
- **那么** 系统删除所有名称以 `e2e-` 或 `e2e_` 开头的测试数据
