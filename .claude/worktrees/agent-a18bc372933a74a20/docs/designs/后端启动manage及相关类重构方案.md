/opsx:explore 重构server\python\manage.py和server\python\src\application_*：1.后端每一个模块的数据模型按scheme进行分配，这样都有自己的version表；2.server
\python\src\application_*可以动态扫描src下的模块文件，动态加载，而不是用import的方式，或者每个模块都有一个application_*.py文件独立（同时manage.py根据参数动
态启动）；3.考虑下每个模块分别部署的情况；4.通过脚本删除所有的表，重建migration，完成重构；

# 现状诊断

  当前架构（单进程、单 schema、硬编码装配）
  ┌─────────────────────────────────────────────────────┐
  │  manage.py                                          │
  │  ├── runserver → uvicorn("application_web:app")    │
  │  ├── runtask → import application_task              │  ← 硬编码
  │  ├── runlistener → import application_listener      │  ← 硬编码
  │  └── db makemigrations/migrate → 单 alembic.ini     │
  │      version_locations: demo + iam (共享 1 个       │
  │      alembic_version 表)                            │
  │                                                     │
  │  application_web.py                                 │
  │  ├── from demo.controllers import dataset           │  ← 硬编码 import
  │  ├── from iam.controllers import router             │  ← 硬编码 import
  │  ├── from iam.controllers.admin.xxx import ...      │  ← 硬编码 import
  │  └── lifespan: setup_engine() + register_tenant...  │
  │                                                     │
  │  application_task.py → from demo.tasks.setup        │  ← 硬编码
  │  application_listener.py → from demo.listeners.setup│  ← 硸编码
  │                                                     │
  │  数据库: public schema (所有表在同一 schema)         │
  │  ├── tenants                                        │
  │  ├── users                                          │
  │  ├── datasets                                       │
  │  └── alembic_version (1 个全局版本表)               │
  │                                                     │
  │  Base → DeclarativeBase (无 schema 配置)            │
  │  BaseModel → Base (abstract=True, 所有模块共享)     │
  └─────────────────────────────────────────────────────┘

## 核心问题

  1. 所有表在 public schema，模块之间没有物理隔离
  2. 迁移共享 1 个 alembic_version，模块无法独立迁移/独立版本控制
  3. 3 个 application_*.py 硬编码 import，新模块必须手动修改这些文件
  4. manage.py 紧耦合模块名（import_all_models 只扫描 demo/models，get_alembic_config 硬编码路径）

  ---

# 你提出的 4 点，我看到的深层张力

  你同时提出了 动态扫描加载（倾向模块化单体）和 模块分别部署（倾向微服务）。这两者看似矛盾，但其实可以统一为一个经典模式——模块化单体（Modular Monolith）：

  同一个代码库，两种运行模式：

  ┌─────────────────── 模块化单体 ───────────────────┐
  │                                                   │
  │  开发/小规模：                                     │
  │  python manage.py runserver                       │
  │  → 动态扫描 src/ 下所有模块                        │
  │  → 一个进程加载 iam + demo + ...                  │
  │  → 一个数据库，多 schema                           │
  │                                                   │
  │  生产/大规模：                                     │
  │  python manage.py runserver --module iam          │
  │  → 只加载 IAM 模块                                │
  │  → 独立进程、独立部署                              │
  │  → 独立数据库 或 共享数据库的 iam schema           │
  │                                                   │
  └───────────────────────────────────────────────────┘

  关键是：每个模块都是自包含的——有自己的模型、路由、迁移、seed、生命周期钩子。装配方式（全部加载 vs 单模块加载）只是启动参数的差异。

  ---

# 每个模块的数据模型按 schema 分配

  PostgreSQL schema 是天然的模块隔离边界：

  数据库: demo_db
  ├── schema: iam
  │   ├── tenants
  │   ├── users
  │   ├── roles
  │   ├── permissions
  │   ├── departments
  │   ├── alembic_version          ← IAM 专属版本表
  │   └── ...
  ├── schema: demo
  │   ├── datasets
  │   ├── alembic_version          ← Demo 专属版本表
  │   └── ...
  └── schema: public
  │   └── alembic_version          ← framework/全局（如果需要）

  SQLAlchemy 实现

  两种方式：

  ┌────────────────────────┬─────────────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────┐
  │          方案          │                                      做法                                       │                  优缺点                  │
  ├────────────────────────┼─────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────┤
  │ A: 模块级              │ 每个模块有自己的 Base（iam.models.Base =                                        │ 干净隔离，但 framework BaseModel         │
  │ DeclarativeBase        │ DeclarativeBase(metadata=MetaData(schema='iam'))）                              │ 需要适配                                 │
  ├────────────────────────┼─────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────┤
  │ B: 表级 __table_args__ │ 每个 Model 加 __table_args__ = {'schema': 'iam'}                                │ 改动小，但每个表都要手动声明，容易遗漏   │
  └────────────────────────┴─────────────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────┘

  方案 A 更好——模块级 Base 让 schema 声明一次，所有模型自动继承。但这意味着 framework.database.BaseModel 的角色需要重新思考：

  当前:
    framework.database.Base → DeclarativeBase (全局, 无 schema)
    framework.database.BaseModel → Base (abstract=True)

  重构后:
    framework.database.Base → DeclarativeBase (全局, 不设 schema)

    每个模块:
    iam.models.Base → DeclarativeBase(metadata=MetaData(schema='iam'))
    iam.models.BaseModel → iam.Base + framework字段(id, created_at, updated_at)

    demo.models.Base → DeclarativeBase(metadata=MetaData(schema='demo'))
    demo.models.BaseModel → demo.Base + framework字段

  framework 不再提供 BaseModel 实体类，而是提供 Mixin 或工厂函数 让模块自己创建带 schema 的 Base + BaseModel。

  Alembic 多 schema 迁移

  每个模块需要独立的 Alembic 环境：

  每个模块的 env.py:
    target_metadata = iam.models.BaseModel.metadata   ← 只包含本模块
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version",              ← 默认即可
        version_table_schema="iam",                   ← 版本表也在本模块 schema
    )

  manage.py 的 db 命令变成：

## 单模块迁移

  python manage.py db makemigrations --module iam -m "add oauth"
  python manage.py db migrate --module iam

## 全部模块迁移

  python manage.py db migrate --all

  ---
  动态扫描 vs 模块独立 application_*.py

  我看到了两条路：

  方案 1: 动态扫描 + 注册器

  src/iam/module.py (每个模块一个声明文件)
  ┌────────────────────────────────────────────────┐
  │  class IAMModule(ModuleDescriptor):             │
  │      name = "iam"                               │
  │      schema = "iam"                             │
  │      models = iam.models                        │
  │      routers = [iam_router, admin_router, ...]  │
  │      seeds = SEED_MODULES                        │
  │      lifespan_hooks = [register_tenant_provider]│
  │      middlewares = [TenantMiddleware]            │
  └────────────────────────────────────────────────┘

  application_web.py (动态装配)
  ┌────────────────────────────────────────────────┐
  │  modules = discover_modules()                    │
  │  │  # 扫描 src/*/module.py                       │
  │  │  # 或按 --module 参数过滤                     │
  │  │                                                │
  │  for m in modules:                               │
  │    app.include_router(m.routers)                 │
  │    app.add_middleware(m.middlewares)              │
  │    lifespan_hooks.extend(m.lifespan_hooks)       │
  └────────────────────────────────────────────────┘

  优点：添加新模块只需在 src/new_module/module.py 声明，零修改 application 文件。
  缺点：模块间依赖关系（如 demo 依赖 iam 的 seed）需要显式声明。

  方案 2: 模块独立 application_*.py

  src/iam/app.py      → IAM 模块自己的 FastAPI app factory
  src/demo/app.py     → Demo 模块自己的 FastAPI app factory

  manage.py
  ┌────────────────────────────────────────────────┐
  │  python manage.py runserver                     │
  │  → 扫描 src/*/app.py                            │
  │  → 合成一个大 app (mount sub-apps)              │
  │                                                  │
  │  python manage.py runserver --module iam         │
  │  → 只加载 iam/app.py                            │
  │  → 独立服务                                      │
  └────────────────────────────────────────────────┘

  优点：每个模块完全自包含，可以独立运行测试、独立部署。
  缺点：mount 子应用时，中间件和 lifespan 的交互比较复杂（FastAPI mount 的子应用有自己的 lifespan）。

  我的倾向：方案 1 + 方案 2 的混合

  每个模块有 module.py (声明注册信息)
    → 用于单体模式下的动态装配

  每个模块可选有 app.py (完整独立应用工厂)
    → 用于独立部署模式

  manage.py 根据参数选择模式：
    无参数 → 扫描所有 module.py，动态装配
    --module iam → 加载 iam/app.py，独立运行

  ---

# 模块分别部署

  这引出几个关键问题需要你思考：

  ┌─────────────────────────────────────────────────┐
  │  模块独立部署时的架构问题                          │
  │                                                   │
  │  1. 数据库：共享一个 DB 多 schema？                │
  │     还是每个模块各自独立 DB？                      │
  │     ┌─ 共享 DB 多 schema: 简单，但有连接池竞争    │
  │     ┌─ 独立 DB: 完全隔离，但跨模块查询变复杂       │
  │                                                   │
  │  2. 跨模块调用：                                   │
  │     IAM 独立部署时，demo 怎么获取租户信息？        │
  │     ┌─ HTTP API 调用（微服务间通信）               │
  │     ┌─ 共享 Protocol + 远程实现                   │
  │     ┌─ 消息队列异步通知                            │
  │                                                   │
  │  3. TenantMiddleware:                              │
  │     当 IAM 独立运行，租户解析还需要吗？            │
  │     → 需要，但 tenant_provider 改为本地查询        │
  │                                                   │
  │  4. API 网关：                                     │
  │     单体模式：一个 app 所有路由                     │
  │     微服务模式：需要网关分发                        │
  │       /api/v1/datasets → demo-service             │
  │       /api/v1/auth    → iam-service               │
  │       /admin/v1/*     → iam-service               │
  └─────────────────────────────────────────────────┘

  ---

# 重建迁移脚本

  这个是最实操的部分。重构后需要一个脚本：

## scripts/rebuild_migrations.py

  1. DROP SCHEMA iam CASCADE; DROP SCHEMA demo CASCADE;
  2. DROP TABLE public.alembic_version;
  3. 为每个模块 CREATE SCHEMA {module_name};
  4. 对每个模块运行 alembic upgrade head
  5. 运行 seed 初始化

  ---

# 一些我还在思考的问题

  1. framework 的表要不要也放独立 schema？ framework 目前没有业务表（只有 Base/Mixin），但如果以后 framework 有自己的表（比如全局配置），它们应该在 public
  还是 framework schema？
  2. IAM 的 TenantAdmin 表比较特殊——它是全局性的（不属于任何租户），放在 iam schema 会不会让其他模块访问时需要跨 schema
  查询？这是性能问题还是架构清晰度问题？
  3. 现有测试怎么办？ 大量测试 import 的是 from framework.database import BaseModel，重构后这些 import 要改。
  4. 跨模块的外键关系怎么处理？ 比如 user_tenants.user_id 引用 users.id，如果两个表在不同 schema，PostgreSQL 支持跨 schema 外键，但 Alembic autogenerate
  会变得复杂。

  ---

# 你觉得这个方向对不对？有几个决策点想听听你的想法

- 数据库隔离级别：共享 DB 多 schema vs 每模块独立 DB？
- 模块声明方式：module.py 注册器 vs app.py 独立应用 vs 两者兼备？
- 跨模块外键：保留跨 schema FK 还是去掉（改用应用层一致性）？
