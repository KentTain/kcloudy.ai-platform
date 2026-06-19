# Permission System 规范

## Purpose

定义前后端权限控制系统，包括前端动态路由、权限指令和接口拦截，以及后端权限检查中间件，实现完整的 RBAC 权限模型。

## Requirements

### Requirement: 动态路由注册

系统 SHALL 支持根据用户权限动态注册路由。

#### Scenario: 获取用户菜单

- **WHEN** 用户登录成功
- **THEN** 系统 SHALL 请求 `/admin/v1/menus` 获取用户菜单权限

#### Scenario: 动态添加路由

- **WHEN** 获取到菜单数据
- **THEN** 系统 SHALL 通过 `router.addRoute()` 动态添加路由

#### Scenario: 无权限访问拦截

- **WHEN** 用户访问未授权路由
- **THEN** 系统 SHALL 跳转至 403 页面

### Requirement: 权限指令

系统 SHALL 提供 `v-permission` 指令控制元素显示。

#### Scenario: 单权限校验

- **WHEN** 元素绑定 `v-permission="['user:add']"`
- **THEN** 系统 SHALL 检查用户是否拥有 `user:add` 权限码

#### Scenario: 多权限校验

- **WHEN** 元素绑定 `v-permission="['user:add', 'user:edit']"`
- **THEN** 系统 SHALL 检查用户是否拥有任一权限码

#### Scenario: 无权限处理

- **WHEN** 用户不具备所需权限
- **THEN** 系统 SHALL 从 DOM 中移除该元素

### Requirement: 接口权限拦截

系统 SHALL 在 Axios 响应拦截器中处理权限错误。

#### Scenario: 401 未登录处理

- **WHEN** 接口返回 401 状态码
- **THEN** 系统 SHALL 跳转至登录页面

#### Scenario: 403 无权限处理

- **WHEN** 接口返回 403 状态码
- **THEN** 系统 SHALL 显示权限不足提示并跳转至 403 页面

### Requirement: Permission Store

系统 SHALL 提供 Pinia Store 管理权限状态。

#### Scenario: 存储权限码

- **WHEN** 获取到用户权限码列表
- **THEN** 系统 SHALL 存储至 permission store

#### Scenario: 检查权限

- **WHEN** 调用 `hasPermission('user:add')`
- **THEN** 系统 SHALL 返回布尔值表示是否拥有该权限

### Requirement: 路由守卫

系统 SHALL 提供路由守卫进行权限校验。

#### Scenario: 白名单路由

- **WHEN** 访问登录页、404 页等白名单路由
- **THEN** 系统 SHALL 直接放行

#### Scenario: 已登录访问登录页

- **WHEN** 已登录用户访问登录页
- **THEN** 系统 SHALL 重定向至首页

#### Scenario: 未登录访问受保护路由

- **WHEN** 未登录用户访问受保护路由
- **THEN** 系统 SHALL 重定向至登录页

### Requirement: 后端权限检查中间件

系统 SHALL 提供后端权限检查中间件。

#### Scenario: 接口权限拦截
- **WHEN** 用户访问需要特定权限的 API 接口
- **THEN** 中间件检查用户是否拥有所需权限

#### Scenario: 权限不足返回 403
- **WHEN** 用户缺少访问接口所需的权限
- **THEN** 返回 HTTP 403，错误消息为"权限不足"

#### Scenario: Token 解析获取权限
- **WHEN** 请求携带有效 Token
- **THEN** 从 Token 中提取用户权限列表

### Requirement: 权限缓存

系统 SHALL 缓存用户权限信息以提高性能。

#### Scenario: 权限缓存到 Redis
- **WHEN** 用户登录成功
- **THEN** 将用户权限列表缓存到 Redis，TTL 为 5 分钟

#### Scenario: 权限变更清除缓存
- **WHEN** 用户角色或权限发生变更
- **THEN** 清除该用户的权限缓存

#### Scenario: 权限缓存命中
- **WHEN** 检查用户权限时缓存存在
- **THEN** 直接从缓存读取权限列表

### Requirement: 权限装饰器

系统 SHALL 提供权限检查装饰器。

#### Scenario: 使用装饰器保护接口
- **WHEN** 控制器方法使用 `@require_permission("user:read")` 装饰器
- **THEN** 访问该方法前检查用户是否拥有 `user:read` 权限

#### Scenario: 多权限任一满足
- **WHEN** 装饰器指定多个权限 `@require_permission(["user:read", "user:write"])`
- **THEN** 用户拥有任一权限即可访问

### Requirement: 权限指令注册

系统 SHALL 在应用启动时自动注册权限指令。

#### Scenario: 应用初始化注册

- **WHEN** Vue 应用初始化
- **THEN** 系统自动注册 v-permission 指令

#### Scenario: 全局可用

- **WHEN** 组件中使用 v-permission 指令
- **THEN** 无需额外导入，指令全局可用

### Requirement: 权限指令增强

系统 SHALL 支持权限指令的多种用法。

#### Scenario: 字符串权限

- **WHEN** 元素绑定 `v-permission="'user:add'"`
- **THEN** 系统检查用户是否拥有 user:add 权限

#### Scenario: 数组权限

- **WHEN** 元素绑定 `v-permission="['user:add', 'user:edit']"`
- **THEN** 系统检查用户是否拥有任一权限

#### Scenario: 权限缺失提示

- **WHEN** 用户缺少所需权限
- **THEN** 元素从 DOM 中移除，可选显示 tooltip 提示

### Requirement: 权限检查函数

系统 SHALL 提供编程式权限检查函数。

#### Scenario: 检查单个权限

- **WHEN** 调用 `hasPermission('user:add')`
- **THEN** 返回布尔值表示是否拥有该权限

#### Scenario: 检查多个权限

- **WHEN** 调用 `hasAnyPermission(['user:add', 'user:edit'])`
- **THEN** 返回布尔值表示是否拥有任一权限

#### Scenario: 检查全部权限

- **WHEN** 调用 `hasAllPermissions(['user:add', 'user:edit'])`
- **THEN** 返回布尔值表示是否拥有全部权限
