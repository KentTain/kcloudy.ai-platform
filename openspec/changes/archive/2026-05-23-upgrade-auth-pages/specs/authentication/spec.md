## MODIFIED Requirements

### Requirement: 用户登录
系统 SHALL 支持用户使用账号密码登录，表单 SHALL 使用 vee-validate + zod schema 校验。

#### Scenario: 登录成功
- **WHEN** 用户输入正确的用户名和密码点击登录
- **THEN** 系统验证成功后返回 Token，跳转至首页

#### Scenario: 登录失败（密码错误）
- **WHEN** 用户输入正确的用户名但错误的密码
- **THEN** 系统返回错误提示"用户名或密码错误"

#### Scenario: 登录失败（用户不存在）
- **WHEN** 用户输入不存在的用户名
- **THEN** 系统返回错误提示"用户名或密码错误"

#### Scenario: 登录失败（用户被停用）
- **WHEN** 用户使用已被停用的账号登录
- **THEN** 系统返回错误提示"账号已被停用"

#### Scenario: 登录失败（用户被锁定）
- **WHEN** 用户使用已被锁定的账号登录
- **THEN** 系统返回错误提示"账号已被锁定"

#### Scenario: 表单校验失败（空用户名）
- **WHEN** 用户未输入用户名即点击登录
- **THEN** vee-validate SHALL 在用户名 FormMessage 中显示"请输入用户名"错误提示

#### Scenario: 表单校验失败（空密码）
- **WHEN** 用户未输入密码即点击登录
- **THEN** vee-validate SHALL 在密码 FormMessage 中显示"请输入密码"错误提示