## ADDED Requirements

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
