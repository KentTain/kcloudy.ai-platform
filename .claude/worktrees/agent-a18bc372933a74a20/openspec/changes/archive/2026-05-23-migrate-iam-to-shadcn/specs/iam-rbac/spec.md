## MODIFIED Requirements

### Requirement: 角色管理

系统 SHALL 支持角色的创建、查询、更新和删除，页面 UI SHALL 使用 shadcn 组件。

#### Scenario: 创建角色
- **WHEN** 系统管理员请求 `POST /api/v1/iam/roles` 并提供角色编码和名称
- **THEN** 创建角色并返回角色信息

#### Scenario: 查询角色列表
- **WHEN** 系统管理员请求 `GET /api/v1/iam/roles`
- **THEN** 返回当前租户下的角色列表，RoleList 页面 SHALL 使用 shadcn Table 展示

#### Scenario: 更新角色
- **WHEN** 系统管理员请求 `PUT /api/v1/iam/roles/{id}` 并提供更新数据
- **THEN** 更新角色信息

#### Scenario: 删除自定义角色
- **WHEN** 系统管理员请求 `DELETE /api/v1/iam/roles/{id}` 且角色非系统内置
- **THEN** 删除角色

#### Scenario: 删除系统内置角色
- **WHEN** 系统管理员尝试删除系统内置角色（`is_system = true`）
- **THEN** 返回 HTTP 400，错误消息为"系统内置角色不可删除"

#### Scenario: 角色列表状态 Badge 展示
- **WHEN** RoleList 表格渲染角色状态列
- **THEN** SHALL 使用 Badge 替代 el-tag 展示角色类型