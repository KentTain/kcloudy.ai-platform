## MODIFIED Requirements

### Requirement: 租户列表查询

系统 SHALL 支持管理员查询租户列表，支持分页和关键字搜索，UI SHALL 使用 shadcn 组件。

#### Scenario: 分页查询租户列表
- **WHEN** 管理员访问租户列表页面，输入页码和每页数量
- **THEN** 系统返回对应页的租户数据，TenantList SHALL 使用 shadcn Table + Pagination 替代 el-table + el-pagination

#### Scenario: 按关键字搜索租户
- **WHEN** 管理员在搜索框输入租户名称或编码
- **THEN** 系统返回名称或编码包含关键字的租户列表，搜索框 SHALL 使用 shadcn Input 替代 el-input

#### Scenario: 按状态筛选租户
- **WHEN** 管理员选择筛选条件（全部/激活/停用）
- **THEN** 系统返回对应状态的租户列表，筛选 SHALL 使用 shadcn Select 替代 el-select

### Requirement: 租户详情查看

系统 SHALL 支持管理员查看租户的详细信息，UI SHALL 使用 shadcn 组件。

#### Scenario: 查看租户详情
- **WHEN** 管理员点击租户列表中的某一行
- **THEN** 系统展示该租户的完整信息，TenantDetail SHALL 使用 DescriptionList 替代 el-descriptions