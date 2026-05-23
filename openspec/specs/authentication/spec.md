# authentication Specification

## Purpose
TBD - created by archiving change impl-iam-frontend-vue. Update Purpose after archive.
## Requirements
### Requirement: 用户登录
系统 SHALL 支持用户使用账号密码登录。

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

### Requirement: 记住登录状态
系统 SHALL 支持记住登录状态。

#### Scenario: 记住登录
- **WHEN** 用户勾选"记住我"后登录
- **THEN** 系统延长 Token 有效期

### Requirement: Token 刷新
系统 SHALL 支持自动刷新过期 Token。

#### Scenario: Token 即将过期
- **WHEN** 用户操作的 Token 即将过期（如剩余 5 分钟）
- **THEN** 系统自动使用刷新 Token 获取新 Token

#### Scenario: Token 已过期
- **WHEN** 用户操作的 Token 已过期
- **THEN** 系统跳转至登录页面

### Requirement: 用户登出
系统 SHALL 支持用户登出系统。

#### Scenario: 正常登出
- **WHEN** 用户点击登出按钮
- **THEN** 系统清除 Token 并跳转至登录页

### Requirement: 登录页面记住账号
系统 SHALL 支持在登录页面记住上次输入的账号。

#### Scenario: 记住账号
- **WHEN** 用户首次登录成功
- **THEN** 系统记录账号到本地存储

#### Scenario: 回显账号
- **WHEN** 用户再次访问登录页面
- **THEN** 系统自动填充上次登录的账号

### Requirement: 查看登录历史

系统 SHALL 支持用户查看自己的登录历史记录。

#### Scenario: 查看登录历史列表

- **WHEN** 用户进入个人中心登录历史页面
- **THEN** 系统展示该用户的登录历史记录列表

#### Scenario: 分页展示

- **WHEN** 登录历史记录超过 20 条
- **THEN** 系统分页展示记录，每页 20 条

#### Scenario: 按时间范围筛选

- **WHEN** 用户选择时间范围筛选条件
- **THEN** 系统仅展示该时间范围内的登录记录

### Requirement: 登录记录详情

系统 SHALL 在登录历史中展示详细的登录信息。

#### Scenario: 显示基本信息

- **WHEN** 用户查看登录历史
- **THEN** 每条记录展示登录时间、IP 地址、登录状态

#### Scenario: 显示设备信息

- **WHEN** 用户查看登录历史
- **THEN** 每条记录展示设备类型、浏览器、操作系统信息

### Requirement: 登录历史 API

系统 SHALL 提供登录历史 API 接口。

#### Scenario: API 请求

- **WHEN** 前端请求 `/api/v1/auth/login-history`
- **THEN** 系统返回当前用户的登录历史记录

#### Scenario: API 分页参数

- **WHEN** 前端请求登录历史并携带 page 和 page_size 参数
- **THEN** 系统返回对应页的数据和总数

