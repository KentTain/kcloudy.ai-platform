# framework-iam-integration Specification

## Purpose

定义 Framework 与 IAM 模块的集成规范，包括侧边栏菜单集成、租户上下文管理、权限指令集成等功能。

## Requirements

### Requirement: IAM 菜单集成

系统 SHALL 在 Framework 侧边栏中展示 IAM 模块菜单。

#### Scenario: 展示 IAM 菜单

- **WHEN** 用户有 IAM 模块访问权限
- **THEN** 侧边栏展示 IAM 相关菜单项（用户管理、角色管理、部门管理等）

#### Scenario: 菜单权限过滤

- **WHEN** 用户无某个 IAM 子模块权限
- **THEN** 侧边栏不展示该子菜单

#### Scenario: 菜单折叠

- **WHEN** 侧边栏处于折叠状态
- **THEN** IAM 菜单仅展示图标，悬停显示子菜单

### Requirement: 租户上下文

系统 SHALL 在用户状态中管理租户上下文信息。

#### Scenario: 存储租户信息

- **WHEN** 用户登录成功
- **THEN** 系统存储当前租户信息（租户 ID、名称、编码）

#### Scenario: 获取当前租户

- **WHEN** 调用 useUserStore().currentTenant
- **THEN** 返回当前租户信息对象

#### Scenario: 租户列表

- **WHEN** 用户属于多个租户
- **THEN** 系统存储用户的租户列表，支持租户切换

### Requirement: 权限指令集成

系统 SHALL 在应用启动时注册权限指令。

#### Scenario: 指令注册

- **WHEN** 应用初始化
- **THEN** 系统注册 v-permission 指令

#### Scenario: 按钮权限控制

- **WHEN** 页面元素绑定 v-permission 指令
- **THEN** 根据用户权限决定是否显示该元素

#### Scenario: 权限检查

- **WHEN** 用户缺少所需权限
- **THEN** 元素从 DOM 中移除

### Requirement: 路由集成

系统 SHALL 将 IAM 路由集成到 Framework 路由配置。

#### Scenario: 路由注册

- **WHEN** 应用加载
- **THEN** IAM 模块路由被注册到 Vue Router

#### Scenario: 路由守卫

- **WHEN** 用户访问 IAM 模块路由
- **THEN** 路由守卫检查用户权限

### Requirement: 侧边栏菜单配置

系统 SHALL 支持配置式菜单管理。

#### Scenario: 菜单配置格式

- **WHEN** 定义菜单配置
- **THEN** 配置包含菜单名称、路径、图标、权限码

#### Scenario: 动态菜单生成

- **WHEN** 侧边栏组件加载
- **THEN** 根据配置和用户权限动态生成菜单
