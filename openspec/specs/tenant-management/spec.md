# tenant-management Specification

## Purpose
TBD - created by archiving change impl-iam-frontend-vue. Update Purpose after archive.
## Requirements
### Requirement: 租户列表查询
系统 SHALL 支持管理员查询租户列表，支持分页和关键字搜索。

#### Scenario: 分页查询租户列表
- **WHEN** 管理员访问租户列表页面，输入页码和每页数量
- **THEN** 系统返回对应页的租户数据，包含总数和当前页数据

#### Scenario: 按关键字搜索租户
- **WHEN** 管理员在搜索框输入租户名称或编码
- **THEN** 系统返回名称或编码包含关键字的租户列表

#### Scenario: 按状态筛选租户
- **WHEN** 管理员选择筛选条件（全部/激活/停用）
- **THEN** 系统返回对应状态的租户列表

### Requirement: 租户详情查看
系统 SHALL 支持管理员查看租户的详细信息，包括配置信息。

#### Scenario: 查看租户详情
- **WHEN** 管理员点击租户列表中的某一行
- **THEN** 系统展示该租户的完整信息（名称、编码、状态、联系人、配置等）

### Requirement: 创建租户
系统 SHALL 支持管理员创建新租户。

#### Scenario: 创建新租户
- **WHEN** 管理员填写租户名称、编码、联系人信息并提交
- **THEN** 系统创建新租户并返回成功提示

#### Scenario: 创建重复编码租户
- **WHEN** 管理员尝试创建已存在编码的租户
- **THEN** 系统返回错误提示"租户编码已存在"

### Requirement: 编辑租户
系统 SHALL 支持管理员编辑租户信息。

#### Scenario: 编辑租户信息
- **WHEN** 管理员修改租户信息并提交
- **THEN** 系统更新租户信息并返回成功提示

### Requirement: 删除租户（软删除）
系统 SHALL 支持管理员删除租户。

#### Scenario: 删除租户
- **WHEN** 管理员点击删除按钮确认删除
- **THEN** 系统将租户状态标记为已删除

#### Scenario: 删除有关联用户的租户
- **WHEN** 管理员尝试删除仍有用户关联的租户
- **THEN** 系统返回错误提示"租户下存在用户，无法删除"

### Requirement: 租户激活/停用
系统 SHALL 支持管理员激活或停用租户。

#### Scenario: 激活租户
- **WHEN** 管理员点击激活按钮
- **THEN** 租户状态变为"激活"

#### Scenario: 停用租户
- **WHEN** 管理员点击停用按钮
- **THEN** 租户状态变为"停用"

### Requirement: 租户资源配置
系统 SHALL 支持配置租户的数据库、存储、缓存资源。

#### Scenario: 配置租户独立数据库
- **WHEN** 管理员填写数据库配置（类型、主机、端口、名称、用户名）
- **THEN** 系统验证配置格式并保存

#### Scenario: 配置租户独立存储
- **WHEN** 管理员填写存储配置（类型、桶名称）
- **THEN** 系统验证配置格式并保存

#### Scenario: 配置租户独立缓存
- **WHEN** 管理员填写 Redis DB 编号
- **THEN** 系统验证编号范围（0-15）并检查是否已被占用

### Requirement: 租户切换
系统 SHALL 支持用户在不同租户间切换。

#### Scenario: 用户切换默认租户
- **WHEN** 用户在顶部导航点击租户切换，选择其他有权限的租户
- **THEN** 系统更新当前租户上下文，刷新页面数据

#### Scenario: 无权限访问租户
- **WHEN** 用户尝试访问无权限的租户数据
- **THEN** 系统返回 403 无权限错误

