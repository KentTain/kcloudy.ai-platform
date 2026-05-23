# role-permission-management Specification

## Purpose
TBD - created by archiving change impl-iam-frontend-vue. Update Purpose after archive.
## Requirements
### Requirement: 角色列表查询
系统 SHALL 支持管理员查询角色列表。

#### Scenario: 查询角色列表
- **WHEN** 管理员访问角色列表页面
- **THEN** 系统返回当前租户的角色列表（包含系统内置角色）

### Requirement: 角色详情查看
系统 SHALL 支持查看角色的详细信息及关联权限。

#### Scenario: 查看角色详情
- **WHEN** 管理员点击角色列表中的某一行
- **THEN** 系统展示该角色的信息及关联的权限列表

### Requirement: 创建角色
系统 SHALL 支持管理员创建新角色。

#### Scenario: 创建新角色
- **WHEN** 管理员填写角色编码、名称、描述并提交
- **THEN** 系统创建新角色并返回成功提示

#### Scenario: 角色编码重复
- **WHEN** 管理员尝试创建已存在编码的角色
- **THEN** 系统返回错误提示"角色编码已存在"

### Requirement: 编辑角色
系统 SHALL 支持管理员编辑角色信息。

#### Scenario: 编辑角色信息
- **WHEN** 管理员修改角色名称、描述并提交
- **THEN** 系统更新角色信息并返回成功提示

### Requirement: 删除角色
系统 SHALL 支持管理员删除自定义角色。

#### Scenario: 删除角色
- **WHEN** 管理员点击删除按钮确认删除自定义角色
- **THEN** 系统删除角色及角色权限关联

#### Scenario: 删除系统内置角色
- **WHEN** 管理员尝试删除系统内置角色
- **THEN** 系统返回错误提示"系统内置角色无法删除"

### Requirement: 角色权限分配
系统 SHALL 支持为角色分配或取消权限。

#### Scenario: 为角色分配权限
- **WHEN** 管理员在角色详情页选择权限并保存
- **THEN** 系统更新角色的权限关联

#### Scenario: 批量分配权限
- **WHEN** 管理员选择多个权限并批量分配
- **THEN** 系统一次性更新角色权限关联

### Requirement: 权限列表查询
系统 SHALL 支持管理员查询所有可用权限。

#### Scenario: 查询权限列表
- **WHEN** 管理员访问权限列表页面
- **THEN** 系统返回所有权限列表

#### Scenario: 按资源筛选权限
- **WHEN** 管理员选择资源类型筛选
- **THEN** 系统返回对应资源的权限列表

### Requirement: 权限树展示
系统 SHALL 支持按资源分组展示权限。

#### Scenario: 查看权限树
- **WHEN** 管理员访问权限管理页面
- **THEN** 系统按资源（user, role, department 等）分组展示权限

### Requirement: 角色复制
系统 SHALL 支持复制现有角色创建新角色。

#### Scenario: 复制角色
- **WHEN** 管理员选择现有角色并点击复制，填写新角色信息
- **THEN** 系统创建新角色并复制原角色的权限

