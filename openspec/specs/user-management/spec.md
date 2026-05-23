# user-management Specification

## Purpose
TBD - created by archiving change impl-iam-frontend-vue. Update Purpose after archive.
## Requirements
### Requirement: 用户列表查询
系统 SHALL 支持管理员查询用户列表，支持分页和条件筛选。

#### Scenario: 分页查询用户列表
- **WHEN** 管理员访问用户列表页面，输入页码和每页数量
- **THEN** 系统返回对应页的用户数据，包含总数和当前页数据

#### Scenario: 按关键字搜索用户
- **WHEN** 管理员在搜索框输入用户名、邮箱或手机号
- **THEN** 系统返回匹配的用户列表

#### Scenario: 按状态筛选用户
- **WHEN** 管理员选择用户状态筛选（全部/激活/停用/锁定）
- **THEN** 系统返回对应状态的用户列表

### Requirement: 用户详情查看
系统 SHALL 支持查看用户的详细信息。

#### Scenario: 查看用户详情
- **WHEN** 管理员点击用户列表中的某一行
- **THEN** 系统展示该用户的完整信息（基本信息、角色、部门、状态等）

### Requirement: 创建用户
系统 SHALL 支持管理员创建新用户。

#### Scenario: 创建新用户
- **WHEN** 管理员填写用户名、密码、邮箱、手机号并提交
- **THEN** 系统创建新用户并返回成功提示

#### Scenario: 用户名重复
- **WHEN** 管理员尝试创建已存在用户名的用户
- **THEN** 系统返回错误提示"用户名已存在"

### Requirement: 编辑用户
系统 SHALL 支持管理员编辑用户信息。

#### Scenario: 编辑用户基本信息
- **WHEN** 管理员修改用户昵称、头像、邮箱、手机号并提交
- **THEN** 系统更新用户信息并返回成功提示

### Requirement: 删除用户（软删除）
系统 SHALL 支持管理员删除用户。

#### Scenario: 删除用户
- **WHEN** 管理员点击删除按钮确认删除
- **THEN** 系统将用户状态标记为已删除

### Requirement: 用户状态管理
系统 SHALL 支持管理员启用、停用、锁定用户。

#### Scenario: 停用用户
- **WHEN** 管理员点击停用按钮
- **THEN** 用户状态变为"停用"，无法登录

#### Scenario: 激活用户
- **WHEN** 管理员点击激活按钮
- **THEN** 用户状态变为"激活"

#### Scenario: 锁定用户
- **WHEN** 管理员点击锁定按钮
- **THEN** 用户状态变为"锁定"，无法登录

### Requirement: 用户角色分配
系统 SHALL 支持为用户分配角色。

#### Scenario: 为用户分配角色
- **WHEN** 管理员在用户详情页选择角色并保存
- **THEN** 系统更新用户的角色关联

### Requirement: 用户部门分配
系统 SHALL 支持为用户分配部门。

#### Scenario: 为用户分配部门
- **WHEN** 管理员在用户详情页选择部门并保存
- **THEN** 系统更新用户的部门关联

### Requirement: 用户密码重置
系统 SHALL 支持管理员重置用户密码。

#### Scenario: 重置用户密码
- **WHEN** 管理员点击重置密码按钮
- **THEN** 系统生成随机密码并返回给管理员

### Requirement: 修改密码
系统 SHALL 支持用户修改自己的登录密码。

#### Scenario: 修改密码
- **WHEN** 用户输入原密码和新密码，确认修改
- **THEN** 系统验证原密码正确后更新密码

### Requirement: 租户上下文存储

系统 SHALL 在用户状态中存储租户上下文信息。

#### Scenario: 存储当前租户

- **WHEN** 用户登录成功
- **THEN** 系统存储当前租户 ID、名称、编码到用户状态

#### Scenario: 存储租户列表

- **WHEN** 用户属于多个租户
- **THEN** 系统存储用户的租户列表信息

#### Scenario: 获取当前租户

- **WHEN** 调用 `useUserStore().currentTenant`
- **THEN** 返回当前租户信息对象

### Requirement: 租户切换

系统 SHALL 支持用户在不同租户间切换。

#### Scenario: 切换租户

- **WHEN** 用户选择切换到其他租户
- **THEN** 系统更新当前租户信息并刷新 Token

#### Scenario: 切换后刷新状态

- **WHEN** 租户切换成功
- **THEN** 系统清除旧租户相关的缓存数据

### Requirement: 租户信息展示

系统 SHALL 在界面上展示租户信息。

#### Scenario: 顶部导航展示

- **WHEN** 用户登录后
- **THEN** 顶部导航栏展示当前租户名称

#### Scenario: 租户选择器

- **WHEN** 用户属于多个租户
- **THEN** 提供租户选择下拉框，支持快速切换

### Requirement: UserInfo 类型扩展

系统 SHALL 扩展 UserInfo 类型以包含租户信息。

#### Scenario: 类型定义

- **WHEN** 定义 UserInfo 接口
- **THEN** 包含 tenantId、tenantName、tenantCode 字段

#### Scenario: 类型兼容

- **WHEN** 使用扩展后的 UserInfo
- **THEN** 与现有代码保持向后兼容

