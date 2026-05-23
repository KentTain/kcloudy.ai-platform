# profile-management Specification

## Purpose
TBD - created by archiving change impl-iam-frontend-vue. Update Purpose after archive.
## Requirements
### Requirement: 查看个人资料

系统 SHALL 支持用户查看自己的个人资料，UI SHALL 使用 shadcn 组件。

#### Scenario: 查看个人资料
- **WHEN** 用户访问个人中心页面
- **THEN** 系统展示用户的个人信息，Profile SHALL 使用 AppPage 骨架 + shadcn Tabs 替代 el-tabs

#### Scenario: 头像展示
- **WHEN** Profile 页渲染用户头像
- **THEN** SHALL 使用 shadcn Avatar 替代 el-avatar

#### Scenario: 角色标签展示
- **WHEN** Profile 页渲染用户角色
- **THEN** SHALL 使用 Badge 替代 el-tag 展示角色名称

### Requirement: 修改个人资料
系统 SHALL 支持用户修改个人信息。

#### Scenario: 修改昵称
- **WHEN** 用户修改昵称并保存
- **THEN** 系统更新昵称并返回成功提示

#### Scenario: 修改头像
- **WHEN** 用户上传新头像并保存
- **THEN** 系统更新头像并展示新头像

#### Scenario: 修改邮箱
- **WHEN** 用户修改邮箱并提交
- **THEN** 系统发送验证邮件，返回成功提示

#### Scenario: 修改手机号
- **WHEN** 用户修改手机号并提交
- **WHEN** 系统发送验证码，返回成功提示

### Requirement: 修改密码

系统 SHALL 支持用户修改登录密码，表单 SHALL 使用 vee-validate + zod。

#### Scenario: 修改密码成功
- **WHEN** 用户输入正确的原密码和新密码，确认修改
- **THEN** 系统验证原密码正确后更新密码

#### Scenario: 修改密码失败（原密码错误）
- **WHEN** 用户输入错误的原密码
- **THEN** 系统返回错误提示"原密码错误"

#### Scenario: 表单校验
- **WHEN** 修改密码表单提交
- **THEN** vee-validate SHALL 根据 zod schema 校验原密码（必填）、新密码（必填 + 最少 8 位）、确认密码（必填 + 与新密码一致）

### Requirement: 查看登录历史

系统 SHALL 支持用户查看最近的登录记录，UI SHALL 使用 shadcn Table + Pagination。

#### Scenario: 查看登录历史
- **WHEN** 用户查看登录历史 tab
- **THEN** 系统展示最近的登录记录，SHALL 使用 shadcn Table 替代 el-table

### Requirement: 多租户用户切换
系统 SHALL 支持多租户用户切换当前租户。

#### Scenario: 查看可切换租户列表
- **WHEN** 用户在个人中心查看可切换的租户
- **THEN** 系统展示用户有权限的租户列表

#### Scenario: 切换当前租户
- **WHEN** 用户选择切换到另一个租户
- **THEN** 系统更新当前租户上下文，刷新页面数据

