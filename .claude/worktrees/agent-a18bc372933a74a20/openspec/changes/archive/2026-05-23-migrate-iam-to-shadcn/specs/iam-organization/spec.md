## MODIFIED Requirements

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

#### Scenario: 部门详情展示
- **WHEN** DepartmentPage 渲染部门详情区域
- **THEN** SHALL 使用 DescriptionList 替代 el-descriptions 展示部门信息