# Spec: 模块动态加载

## ADDED Requirements

### Requirement: 模块声明文件定义注册信息

系统 SHALL 通过模块根目录的 `module.py` 文件声明模块注册信息。

#### Scenario: 模块声明基本结构

- **GIVEN** `iam` 模块存在 `src/iam/module.py`
- **WHEN** 该文件定义 `IAMModule` 类实现 `ModuleDescriptor` 协议
- **THEN** 模块注册信息包括：
  - `name`: 模块名称 `"iam"`
  - `schema`: PostgreSQL schema `"iam"`
  - `get_base()`: 返回模块的 `DeclarativeBase`
  - `get_routers()`: 返回路由注册列表
  - `get_middlewares()`: 返回中间件列表
  - `get_lifespan_hooks()`: 返回生命周期钩子
  - `get_seeds()`: 返回 seed 注册表
  - `get_task_setup()`: 返回任务调度器配置
  - `get_listener_setup()`: 返回监听器配置

#### Scenario: 模块声明路由注册

- **WHEN** `IAMModule.get_routers()` 返回 `[(iam_router, "/api/v1", ["IAM"])]`
- **THEN** 应用启动时自动注册该路由
- **AND** 路由前缀为 `/api/v1`
- **AND** 标签为 `["IAM"]`

### Requirement: 模块动态扫描与发现

系统 SHALL 在启动时自动扫描 `src/` 目录下的模块声明文件。

#### Scenario: 自动发现所有模块

- **GIVEN** `src/` 目录下存在 `iam/module.py` 和 `demo/module.py`
- **WHEN** 执行 `python manage.py runserver` 无参数
- **THEN** 系统扫描并加载所有模块
- **AND** 所有模块的路由、中间件、生命周期钩子被注册

#### Scenario: 按需加载指定模块

- **GIVEN** 系统存在 `iam` 和 `demo` 两个模块
- **WHEN** 执行 `python manage.py runserver --module iam`
- **THEN** 仅加载 `iam` 模块
- **AND** `demo` 模块的路由和功能不可用

#### Scenario: 加载多个指定模块

- **WHEN** 执行 `python manage.py runserver --module iam,demo`
- **THEN** 仅加载 `iam` 和 `demo` 模块
- **AND** 其他模块（如有）不被加载

### Requirement: 模块 Base 创建工厂

系统 SHALL 提供 `create_module_base(schema)` 工厂函数，为模块创建带 schema 的 `DeclarativeBase`。

#### Scenario: 创建模块 Base

- **WHEN** 调用 `create_module_base("iam")`
- **THEN** 返回一个 `DeclarativeBase` 子类
- **AND** 该类的 `metadata.schema` 为 `"iam"`

#### Scenario: 创建模块 BaseModel

- **WHEN** 调用 `create_base_model(module_base)`
- **THEN** 返回一个包含 `id`、`created_at`、`updated_at` 字段的抽象基类
- **AND** 继承自模块的 `Base`
- **AND** 所有子类表自动归属模块 schema

### Requirement: 模块依赖声明

系统 SHALL 支持模块声明对其他模块的依赖关系。

#### Scenario: 声明模块依赖

- **GIVEN** `demo` 模块依赖 `iam` 模块的租户数据
- **WHEN** `DemoModule.dependencies = ["iam"]`
- **THEN** 系统确保 `iam` 模块先于 `demo` 模块加载
- **AND** seed 执行时 `iam` 的 seed 先于 `demo` 执行

#### Scenario: 循环依赖检测

- **GIVEN** 模块 A 声明依赖 B，模块 B 声明依赖 A
- **WHEN** 系统扫描模块
- **THEN** 抛出循环依赖异常
- **AND** 应用启动失败并提示错误信息

### Requirement: 模块注册中心

系统 SHALL 提供模块注册中心管理所有已加载模块。

#### Scenario: 获取已注册模块

- **GIVEN** 系统已加载 `iam` 和 `demo` 模块
- **WHEN** 调用 `ModuleRegistry.get_module("iam")`
- **THEN** 返回 `IAMModule` 实例

#### Scenario: 获取所有模块的 Base

- **WHEN** 调用 `ModuleRegistry.get_all_bases()`
- **THEN** 返回所有模块的 `DeclarativeBase` 列表
- **AND** 用于 Alembic 迁移时收集所有模块的 metadata
