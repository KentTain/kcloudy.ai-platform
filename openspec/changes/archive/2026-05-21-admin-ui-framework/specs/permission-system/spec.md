# Permission System 规格说明

## ADDED Requirements

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
