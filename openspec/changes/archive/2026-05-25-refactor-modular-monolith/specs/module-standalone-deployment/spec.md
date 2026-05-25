# Spec: 模块独立部署

## ADDED Requirements

### Requirement: 模块独立应用工厂

系统 SHALL 为每个模块提供独立的 FastAPI 应用工厂文件 `app.py`。

#### Scenario: 模块独立应用入口

- **GIVEN** `iam` 模块存在 `src/iam/app.py`
- **WHEN** 该文件定义 `create_app()` 函数
- **THEN** 该函数返回完整的 FastAPI 应用实例
- **AND** 包含 IAM 模块的所有路由、中间件、生命周期钩子
- **AND** 可独立运行

#### Scenario: 独立应用包含完整依赖

- **WHEN** `iam/app.py` 的 `create_app()` 被调用
- **THEN** 应用包含：
  - 数据库引擎初始化
  - 租户 Provider 注册
  - IAM 相关路由
  - IAM 相关中间件
  - IAM 相关生命周期钩子

### Requirement: 单模块独立启动

系统 SHALL 支持通过 manage.py 启动单个模块的独立应用。

#### Scenario: 启动单模块服务

- **WHEN** 执行 `python manage.py runserver --module iam`
- **THEN** 系统加载 `iam/app.py` 的 `create_app()` 返回的应用
- **AND** 仅 IAM 模块的功能可用
- **AND** 其他模块的路由不存在

#### Scenario: 单模块独立数据库

- **GIVEN** `iam` 模块配置使用独立数据库连接
- **WHEN** 启动 `iam` 独立服务
- **THEN** 数据库引擎仅连接 IAM 配置的数据库
- **AND** 不加载其他模块的数据库配置

### Requirement: 模块间 HTTP 通信

当模块独立部署时，系统 SHALL 通过 HTTP API 实现跨模块调用。

#### Scenario: Demo 服务调用 IAM 租户接口

- **GIVEN** `demo` 服务独立部署
- **AND** `iam` 服务独立部署
- **WHEN** `demo` 服务需要获取租户信息
- **THEN** `demo` 服务通过 HTTP 调用 `iam` 服务的 `/api/v1/tenants/{id}` 接口
- **AND** 不直接访问 `iam` 数据库表

#### Scenario: 服务发现配置

- **GIVEN** 模块独立部署模式
- **WHEN** 配置环境变量 `IAM_SERVICE_URL=http://iam-service:8000`
- **THEN** 其他模块通过该 URL 调用 IAM 服务接口

### Requirement: 任务调度器独立部署

系统 SHALL 支持任务调度器按模块独立部署。

#### Scenario: 启动单模块任务调度器

- **WHEN** 执行 `python manage.py runtask --module demo`
- **THEN** 仅加载 `demo` 模块的任务定义
- **AND** 仅执行 `demo` 模块的定时任务

#### Scenario: 单模块任务隔离

- **GIVEN** `demo` 模块定义了 `cleanup_expired_datasets` 任务
- **WHEN** `demo` 任务调度器独立运行
- **THEN** 该任务正常执行
- **AND** 其他模块的任务不被加载

### Requirement: 消息监听器独立部署

系统 SHALL 支持消息监听器按模块独立部署。

#### Scenario: 启动单模块监听器

- **WHEN** 执行 `python manage.py runlistener --module demo`
- **THEN** 仅加载 `demo` 模块的监听器定义
- **AND** 仅处理 `demo` 模块订阅的消息

#### Scenario: 单模块监听器隔离

- **GIVEN** `demo` 模块定义了 `DatasetCreatedHandler`
- **WHEN** `demo` 监听器独立运行
- **THEN** 该处理器正常响应消息
- **AND** 其他模块的监听器不被加载

### Requirement: 模块部署模式配置

系统 SHALL 通过配置区分单体模式和微服务模式。

#### Scenario: 单体模式配置

- **GIVEN** 环境变量 `DEPLOY_MODE=monolith`
- **WHEN** 启动服务
- **THEN** 所有模块在同一进程内加载
- **AND** 模块间调用使用本地函数调用

#### Scenario: 微服务模式配置

- **GIVEN** 环境变量 `DEPLOY_MODE=microservice`
- **WHEN** 启动服务
- **THEN** 仅加载指定模块
- **AND** 跨模块调用通过 HTTP API

### Requirement: API 网关路由分发

在微服务模式下，系统 SHALL 通过 API 网关分发请求到对应模块服务。

#### Scenario: 网关路由规则

- **GIVEN** 部署了 API 网关
- **WHEN** 请求路径为 `/api/v1/auth/*`
- **THEN** 网关将请求转发到 IAM 服务
- **WHEN** 请求路径为 `/api/v1/datasets/*`
- **THEN** 网关将请求转发到 Demo 服务

#### Scenario: 网关健康检查聚合

- **GIVEN** IAM 服务和 Demo 服务独立部署
- **WHEN** 请求网关的 `/health` 端点
- **THEN** 网关聚合所有服务的健康状态
- **AND** 返回整体健康检查结果
