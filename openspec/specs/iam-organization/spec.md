# IAM Organization 规范

## Purpose

定义部门组织架构管理功能，支持树形部门结构、部门负责人设置和用户 - 部门关联。

## Requirements

### Requirement: 部门管理

系统 SHALL 支持部门的创建、查询、更新和删除，页面 UI SHALL 使用 shadcn 组件和 CheckboxTree。

#### Scenario: 创建顶级部门
- **WHEN** 系统管理员请求 `POST /api/v1/iam/departments` 并提供部门名称
- **THEN** 创建顶级部门并返回部门信息

#### Scenario: 创建子部门
- **WHEN** 系统管理员请求创建部门时指定 `parent_id`
- **THEN** 创建子部门，形成树形结构

#### Scenario: 查询部门树
- **WHEN** 系统管理员请求 `GET /api/v1/iam/departments`
- **THEN** 返回当前租户的部门树形结构，DepartmentPage SHALL 使用 CheckboxTree 替代 el-tree 展示

#### Scenario: 更新部门
- **WHEN** 系统管理员请求 `PUT /api/v1/iam/departments/{id}` 并提供更新数据
- **THEN** 更新部门信息

#### Scenario: 删除无用户的部门
- **WHEN** 系统管理员请求 `DELETE /api/v1/iam/departments/{id}` 且部门下无用户
- **THEN** 删除部门

#### Scenario: 删除有用户的部门
- **WHEN** 系统管理员尝试删除有用户的部门
- **THEN** 返回 HTTP 400，错误消息为"部门下存在用户，无法删除"

#### Scenario: 删除有子部门的部门
- **WHEN** 系统管理员尝试删除有子部门的部门
- **THEN** 返回 HTTP 400，错误消息为"存在子部门，无法删除"

#### Scenario: 部门详情展示
- **WHEN** DepartmentPage 渲染部门详情区域
- **THEN** SHALL 使用 DescriptionList 替代 el-descriptions 展示部门信息

### Requirement: 部门排序

系统 SHALL 支持部门排序。

#### Scenario: 设置部门排序
- **WHEN** 系统管理员创建或更新部门时指定 `sort_order`
- **THEN** 部门按 `sort_order` 升序排列

#### Scenario: 默认排序
- **WHEN** 创建部门时未指定 `sort_order`
- **THEN** 默认 `sort_order = 0`

### Requirement: 部门负责人

系统 SHALL 支持设置部门负责人。

#### Scenario: 设置部门负责人
- **WHEN** 系统管理员更新部门时指定 `leader_id`
- **THEN** 设置该用户为部门负责人

#### Scenario: 部门负责人自动关联
- **WHEN** 设置用户为部门负责人
- **THEN** 自动创建用户 - 部门关联记录，`is_leader = true`

### Requirement: 用户 - 部门关联

系统 SHALL 支持用户属于多个部门。

#### Scenario: 添加用户到部门
- **WHEN** 系统管理员请求 `POST /api/v1/iam/users/{id}/departments` 并提供部门 ID
- **THEN** 创建用户 - 部门关联

#### Scenario: 用户属于多个部门
- **WHEN** 用户被添加到多个部门
- **THEN** 用户可以查看所有所属部门的信息

#### Scenario: 移除用户部门关联
- **WHEN** 系统管理员请求 `DELETE /api/v1/iam/users/{id}/departments/{department_id}`
- **THEN** 删除用户 - 部门关联

#### Scenario: 查询部门用户列表
- **WHEN** 系统管理员请求 `GET /api/v1/iam/departments/{id}/users`
- **THEN** 返回该部门下的所有用户列表

### Requirement: 租户隔离

系统 SHALL 确保部门在租户内隔离。

#### Scenario: 查询部门仅返回本租户
- **WHEN** 系统管理员查询部门列表
- **THEN** 仅返回当前租户下的部门

#### Scenario: 跨租户部门不可见
- **WHEN** 系统管理员尝试查询其他租户的部门
- **THEN** 返回 HTTP 404

