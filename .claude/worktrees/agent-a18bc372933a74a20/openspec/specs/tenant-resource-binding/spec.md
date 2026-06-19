# tenant-resource-binding Specification

## Purpose
TBD - created by syncing change tenant-admin-frontend. Update Purpose after archive.

## Requirements

### Requirement: 管理员可以查看租户资源绑定

系统 SHALL 允许管理员查看租户当前的资源配置绑定情况。

#### Scenario: 查询租户资源绑定
- **WHEN** 管理员请求 GET /admin/v1/tenants/{id}/resources
- **THEN** 系统返回租户的资源绑定情况（数据库/存储/缓存/队列/发布订阅）

#### Scenario: 未绑定资源显示
- **WHEN** 租户某项资源未绑定
- **THEN** 系统返回该项资源为 null

### Requirement: 管理员可以更新租户资源绑定

系统 SHALL 允许管理员为租户绑定或解绑资源配置。

#### Scenario: 绑定资源配置
- **WHEN** 管理员请求 PUT /admin/v1/tenants/{id}/resources 并提供配置 ID
- **THEN** 系统更新租户的资源绑定

#### Scenario: 解绑资源
- **WHEN** 管理员将某个配置设为 null
- **THEN** 系统解除该资源的绑定

#### Scenario: 绑定不存在的配置
- **WHEN** 管理员绑定的配置 ID 不存在
- **THEN** 系统返回 404 错误

### Requirement: 租户详情页提供资源绑定 Tab

系统 SHALL 在租户详情页提供资源绑定 Tab，展示租户的资源绑定情况。

#### Scenario: 显示资源绑定 Tab
- **WHEN** 管理员进入租户详情页并点击「资源绑定」Tab
- **THEN** 页面显示租户当前的资源绑定情况

#### Scenario: 选择资源配置
- **WHEN** 管理员点击资源配置下拉框
- **THEN** 系统显示可用的配置列表

#### Scenario: 测试资源配置连通性
- **WHEN** 管理员点击「测试连接」按钮
- **THEN** 系统调用对应的 test-connection API 并显示结果

#### Scenario: 保存资源绑定
- **WHEN** 管理员修改资源绑定并点击「保存」
- **THEN** 系统更新资源绑定并显示成功提示
