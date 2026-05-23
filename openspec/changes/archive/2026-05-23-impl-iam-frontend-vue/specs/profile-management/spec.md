# profile-management 个人中心功能规范

## ADDED Requirements

### Requirement: 查看个人资料
系统 SHALL 支持用户查看自己的个人资料。

#### Scenario: 查看个人资料
- **WHEN** 用户访问个人中心页面
- **THEN** 系统展示用户的个人信息（用户名、昵称、邮箱、手机号、头像等）

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
系统 SHALL 支持用户修改登录密码。

#### Scenario: 修改密码成功
- **WHEN** 用户输入正确的原密码和新密码，确认修改
- **THEN** 系统验证原密码正确后更新密码，返回成功提示

#### Scenario: 修改密码失败（原密码错误）
- **WHEN** 用户输入错误的原密码
- **THEN** 系统返回错误提示"原密码错误"

### Requirement: 查看登录历史
系统 SHALL 支持用户查看最近的登录记录。

#### Scenario: 查看登录历史
- **WHEN** 用户查看登录历史
- **THEN** 系统展示最近的登录记录（时间、IP、设备）

### Requirement: 多租户用户切换
系统 SHALL 支持多租户用户切换当前租户。

#### Scenario: 查看可切换租户列表
- **WHEN** 用户在个人中心查看可切换的租户
- **THEN** 系统展示用户有权限的租户列表

#### Scenario: 切换当前租户
- **WHEN** 用户选择切换到另一个租户
- **THEN** 系统更新当前租户上下文，刷新页面数据
