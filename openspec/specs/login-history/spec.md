# login-history Specification

## Purpose

定义用户登录历史查看功能，允许用户查看自己的登录记录，包括登录时间、IP 地址、设备信息等，帮助用户监控账户安全。

## Requirements

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
