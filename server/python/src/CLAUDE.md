# Python 源码开发指南

本文件为 Claude Code 在 `server/python/src/` 源码目录中工作时提供指导。

## 目录定位

`src/` 按顶级模块组织源码。模块是 `src/{module}/`，功能是模块内的子域；不要把功能域提升为新的顶级目录。

## 架构特性

- **模块级 Schema 隔离**：每个模块拥有独立的 PostgreSQL schema（如 `iam.users`）
- **模块动态加载**：通过 `module.py` 声明模块信息，支持按需加载
- **模块独立部署**：每个模块可通过 `app.py` 提供独立应用工厂

## 顶级模块

| 模块 | 定位 | Schema | 详细文档 |
| --- | --- | --- | --- |
| `demo/` | AI 助手平台业务演示模块 | `demo` | 暂无模块级 CLAUDE.md，参考本文件通用规则 |
| `framework/` | 底层基础设施模块 | - | [framework/CLAUDE.md](framework/CLAUDE.md) |
| `framework/module/` | 模块系统（动态加载、注册中心） | - | [framework/module/CLAUDE.md](framework/module/CLAUDE.md) |
| `tenant/` | 租户管理模块 | `tenant` | [tenant/CLAUDE.md](tenant/CLAUDE.md) |
| `iam/` | 身份认证与权限模块 | `iam` | [iam/CLAUDE.md](iam/CLAUDE.md) |

入口文件：

| 文件 | 用途 |
| --- | --- |
| `application_web.py` | FastAPI Web 应用装配入口（动态模块扫描） |
| `application_task.py` | 定时任务调度器入口（支持 --module 参数） |
| `application_listener.py` | 消息监听器入口（支持 --module 参数） |
| `run.py` | Web 服务启动入口 |

## 模块结构规范

每个业务模块应包含以下关键文件：

```
src/{module}/
├── module.py           # 模块声明（必需）
├── app.py              # 独立应用工厂
├── models/
│   └── __init__.py     # 使用 create_module_base("{module}") 创建 Base
├── migrations/
│   ├── env.py          # 配置 version_table_schema="{module}"
│   └── versions/       # 迁移文件
├── controllers/        # API 控制器
├── services/           # 业务逻辑层
└── schemas/            # Pydantic 模型
```

### 模块声明文件 (module.py)

每个模块必须定义 `module.py`，实现 `ModuleDescriptor` 协议：

```python
class MyModule:
    @property
    def name(self) -> str:
        return "my_module"

    @property
    def schema(self) -> str:
        return "my_module"

    @property
    def dependencies(self) -> list[str]:
        return []  # 依赖的其他模块

    def get_base(self) -> type:
        from my_module.models import Base
        return Base

    def get_routers(self) -> list[tuple]:
        return [(router, "/api/v1", ["MyModule"])]

    def get_seeds(self) -> dict[str, Callable]:
        return {"default": seed_func}

    def get_task_setup(self) -> tuple | None:
        return (setup_scheduler, cleanup_scheduler)

    def get_listener_setup(self) -> tuple | None:
        return (setup_listeners, cleanup_listeners)
```

### 模块 Base 创建 (models/__init__.py)

```python
from framework.database import create_module_base, create_base_model

Base = create_module_base("my_module")
BaseModel = create_base_model(Base)
```

### 模块迁移配置 (migrations/env.py)

```python
MODULE_SCHEMA = "my_module"

context.configure(
    connection=connection,
    target_metadata=Base.metadata,
    version_table_schema=MODULE_SCHEMA,
)
```

## 通用分层规则

业务模块遵循 MVC / 分层结构：

| 层级 | 目录 | 职责 |
| --- | --- | --- |
| Controller | `controllers/` | HTTP 路由、请求参数、鉴权依赖、响应封装 |
| Service | `services/` | 业务规则、事务边界、跨模型协作、外部组件调用 |
| Model | `models/` | SQLAlchemy ORM 映射、数据库约束、领域枚举 |
| Schema | `schemas/` | Pydantic 请求 DTO、响应 VO、内部数据结构 |
| Migration | `migrations/` | Alembic 迁移、seed、迁移模板 |

## 开发约定

- 新模块放在 `src/{module}/`，不要放在 `src/core/`、`src/common/` 等跨模块目录；可复用基础能力应进入 `framework/`。
- **必须** 在新模块中创建 `module.py` 实现模块声明。
- **必须** 使用 `create_module_base(schema)` 创建模块级 Base，确保表归属正确 schema。
- Controller 不直接写复杂业务逻辑和数据库事务。
- Service 是主要业务逻辑入口，涉及写操作时明确事务提交与回滚策略。
- Model 字段使用 SQLAlchemy 2.0 声明式类型：`Mapped[...] = mapped_column(...)`。
- Schema 不复用 ORM 模型作为 API 响应，使用 Pydantic 模型表达边界数据。
- 模块内的迁移、seed、初始化逻辑应与模块代码同目录维护。
- 业务模块可以依赖 framework；framework 禁止依赖业务模块。
- 跨模块数据引用**不使用外键约束**，改用应用层一致性检查。

## Demo 子域

Demo 模块除常规 MVC 目录外，还包含：

| 子域 | 职责 |
| --- | --- |
| `examples/` | LangChain、LangGraph、MCP、插件、RAG 等示例代码 |
| `listeners/` | 消息监听器，支持 Pub/Sub 和 Queue 两类消费模式 |
| `tasks/` | 定时任务，区分本地任务和集群唯一任务 |
| `utils/` | Demo 专属工具函数 |
| `configs/`、`core/`、`common/` | Demo 历史通用能力，新增跨模块基础能力优先放入 framework |

### 监听器开发

- Pub/Sub 处理器继承 framework 的 `SingleTopicHandler`。
- Queue 处理器继承 framework 的 `SingleQueueHandler`。
- 主题名和队列名放在 `constants.py`，不要硬编码在处理逻辑中。
- 新处理器需要在 `listeners/setup.py` 注册。

### 任务开发

- 任务函数使用 async，内部捕获并记录异常。
- 本地任务每个实例独立执行；集群任务通过共享 JobStore 保证唯一执行。
- 新任务需要在 `tasks/setup.py` 注册，并补充对应测试。

## API 入口

常见接口包括：

| 路径 | 用途 |
| --- | --- |
| `/health` | 健康检查 |
| `/api/v1/datasets` | Demo 知识库 CRUD 示例 |
| `/admin/v1/tenants` | Tenant 模块租户管理接口 |
| `/console/v1/tenants` | Tenant 模块用户端租户接口 |
| `/inner/v1/tenants` | Tenant 模块内部接口 |
| `/inner/v1/users` | IAM 模块用户内部接口 |
| `/inner/v1/departments` | IAM 模块部门内部接口 |
| `/docs` | Swagger API 文档 |
| `/redoc` | ReDoc API 文档 |

以实际路由注册为准。新增或修改接口时，同时检查 Controller、Schema、Service、权限和测试。

## 测试入口

源码修改后优先运行对应模块测试。测试目录说明见 [../tests/CLAUDE.md](../tests/CLAUDE.md)。
