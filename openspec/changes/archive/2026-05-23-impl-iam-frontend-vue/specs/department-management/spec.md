# department-management 部门管理功能规范

## ADDED Requirements

### Requirement: 部门树形结构展示
系统 SHALL 支持以树形结构展示部门组织。

#### Scenario: 查看部门树
- **WHEN** 管理员访问部门管理页面
- **THEN** 系统以树形结构展示部门，支持展开/折叠

#### Scenario: 部门层级展示
- **WHEN** 部门有子部门时
- **THEN** 显示下级部门数量，点击可展开查看

### Requirement: 创建部门
系统 SHALL 支持管理员创建新部门。

#### Scenario: 创建根部门
- **WHEN** 管理员在根级别创建部门，填写名称和编码
- **THEN** 系统创建新部门

#### Scenario: 创建子部门
- **WHEN** 管理员在某个部门下创建子部门
- **THEN** 系统创建子部门并关联父部门

### Requirement: 编辑部门
系统 SHALL 支持管理员编辑部门信息。

#### Scenario: 编辑部门信息
- **WHEN** 管理员修改部门名称、编码、排序号并提交
- **THEN** 系统更新部门信息

### Requirement: 删除部门
系统 SHALL 支持管理员删除部门。

#### Scenario: 删除部门（无子部门无用户）
- **WHEN** 管理员删除无子部门且无用户关联的部门
- **THEN** 系统删除部门

#### Scenario: 删除有子部门的部门
- **WHEN** 管理员尝试删除有子部门的部门
- **THEN** 系统返回错误提示"请先删除子部门"

#### Scenario: 删除有用户的部门
- **WHEN** 管理员尝试删除有用户关联的部门
- **THEN** 系统返回错误提示"部门下存在用户，无法删除"

### Requirement: 设置部门负责人
系统 SHALL 支持为部门设置负责人。

#### Scenario: 设置部门负责人
- **WHEN** 管理员选择用户作为部门负责人并保存
- **THEN** 系统更新部门的负责人信息

### Requirement: 部门用户管理
系统 SHALL 支持查看和 管理部门下的用户。

#### Scenario: 查看部门用户
- **WHEN** 管理员点击某个部门，查看其下用户列表
- **THEN** 系统展示该部门的用户列表

#### Scenario: 从部门移除用户
- **WHEN** 管理员从部门用户列表中移除某个用户
- **THEN** 系统删除用户与部门的关联关系

### Requirement: 部门移动
系统 SHALL 支持将部门移动到其他父部门下。

#### Scenario: 移动部门
- **WHEN** 管理员拖拽或选择目标父部门移动部门
- **THEN** 系统更新部门的父部门关联

### Requirement: 部门排序
系统 SHALL 支持调整部门显示顺序。

#### Scenario: 部门排序
- **WHEN** 管理员调整部门的 sort_order 值
- **THEN** 系统按排序号显示部门
