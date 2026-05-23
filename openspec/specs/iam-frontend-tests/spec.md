# iam-frontend-tests Specification

## Purpose

定义 IAM 前端模块的测试规范，包括 API 测试、Store 测试、组件测试等，确保代码质量和功能正确性。

## Requirements

### Requirement: API 单元测试

系统 SHALL 为 IAM API 封装创建单元测试。

#### Scenario: 认证 API 测试

- **WHEN** 运行 auth API 测试
- **THEN** 验证 login、logout、refreshToken、getCurrentUser 等方法正确调用

#### Scenario: 用户 API 测试

- **WHEN** 运行 user API 测试
- **THEN** 验证 list、get、create、update、delete 等方法正确调用

#### Scenario: 角色 API 测试

- **WHEN** 运行 role API 测试
- **THEN** 验证 CRUD 和权限分配方法正确调用

#### Scenario: 部门 API 测试

- **WHEN** 运行 department API 测试
- **THEN** 验证树形结构获取和 CRUD 方法正确调用

#### Scenario: 租户 API 测试

- **WHEN** 运行 tenant API 测试
- **THEN** 验证管理端和用户端 API 方法正确调用

### Requirement: Store 单元测试

系统 SHALL 为 IAM Store 创建单元测试。

#### Scenario: Auth Store 测试

- **WHEN** 运行 auth store 测试
- **THEN** 验证登录状态管理、Token 处理、用户信息存储

#### Scenario: User Store 测试

- **WHEN** 运行 user store 测试
- **THEN** 验证用户列表管理、状态变更、角色分配

#### Scenario: Role Store 测试

- **WHEN** 运行 role store 测试
- **THEN** 验证角色列表管理、权限分配

#### Scenario: Department Store 测试

- **WHEN** 运行 department store 测试
- **THEN** 验证部门树管理、节点操作

#### Scenario: Tenant Store 测试

- **WHEN** 运行 tenant store 测试
- **THEN** 验证租户列表管理、租户切换

### Requirement: 组件测试

系统 SHALL 为关键组件创建测试。

#### Scenario: 权限树组件测试

- **WHEN** 运行 PermissionTree 组件测试
- **THEN** 验证树形渲染、选择功能、搜索过滤

#### Scenario: 部门树组件测试

- **WHEN** 运行 DepartmentTree 组件测试
- **THEN** 验证树形渲染、节点选择、展开折叠

#### Scenario: 用户表单组件测试

- **WHEN** 运行 UserForm 组件测试
- **THEN** 验证表单验证、数据提交

### Requirement: 测试覆盖率

系统 SHALL 保持测试覆盖率在合理水平。

#### Scenario: 覆盖率目标

- **WHEN** 运行测试覆盖率报告
- **THEN** API 和 Store 覆盖率达到 80% 以上

#### Scenario: 关键路径覆盖

- **WHEN** 检查测试用例
- **THEN** 覆盖登录、用户管理、角色管理等核心功能路径
