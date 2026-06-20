# CLAUDE.md

本文件为 Claude Code 在后端服务目录工作时提供指导。

## 目录定位

`server/` 目录包含多种后端技术栈的独立实现，每种技术栈作为独立子项目存在。所有实现遵循统一的架构设计和 API 规范。

## 技术栈状态

| 技术栈 | 语言 | 框架 | 状态 | 详细文档 |
|--------|------|------|------|----------|
| Python | Python 3.12 | FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic + LangChain | ✅ 可用 | [python/CLAUDE.md](python/CLAUDE.md) |
| Rust | Rust 1.95+ | Axum + SQLx + serde + Tokio + LangChainRust | ✅ 可用 | [rust/CLAUDE.md](rust/CLAUDE.md) |
| Java | Java 21 | Spring Boot 3.x + MyBatis + LangChain4j | 🚧 规划中 | - |
| .NET | .NET 8.0 | ASP.NET Core + EF Core + LangChain.NET | 🚧 规划中 | - |

## 统一项目结构

```text
server/{技术栈}/
├── src/
│   ├── framework/                 # 基础设施层（跨模块共享）
│   │   ├── database/              # 基础设施：数据库-database
│   │   │   ├── core/              # - 核心（engine, session, base）
│   │   │   ├── mixins/            # - 模型混入（tree, tenant, audit...）
│   │   │   ├── types/             # - 自定义类型（datetime, enum, uuid...）
│   │   │   ├── events/            # - 事件监听
│   │   │   └── interceptors/      # - 拦截器
│   │   ├── {基础设施}/             # 基础设施：Cache-缓存、storage-对象存储、queue-消息队列、pubsub-发布订阅
│   │   │   ├── factory.*          # - 工厂函数
│   │   │   ├── impl/              # - 实现类
│   │   │   ├── handler.*          # - 处理器基类：基础设施 queue-消息队列、pubsub-发布订阅 所独有
│   │   │   └── tenant_*_manager.* # - 租户管理器：不同基础设施的多租户实现
│   │   ├── lock/                  # 分布式锁
│   │   │   ├── factory.*
│   │   │   └── impl/
│   │   ├── schemas/               # 公共 Schema/VO（tree.py 等）
│   │   ├── utils/                 # 工具函数
│   │   ├── middlewares/           # 中间件
│   │   ├── clients/               # 内部 HTTP 客户端
│   │   ├── events/                # 事件总线
│   │   ├── module/                # 模块系统
│   │   └── tenant/                # 多租户支持
│   │
│   └── {module}/                  # 业务模块：tenant、iam、demo 等
│       ├── controllers/           # API 控制器
│       ├── services/              # 业务逻辑层
│       ├── models/                # 数据库模型
│       ├── schemas/               # DTO 模型
│       ├── listeners/             # 消息监听器
│       │   ├── services/
│       │   │   ├── pubsub/        # - PubSub 处理器
│       │   │   └── queue/         # - Queue 处理器
│       │   └── setup.*            # - 生命周期管理
│       ├── tasks/                 # 定时任务
│       │   ├── services/          # - 任务函数
│       │   └── setup.*            # - 调度器管理
│       ├── migrations/            # 数据库迁移
│       │   ├── versions/          # - 迁移版本
│       │   ├── seeds/             # - 种子数据
│       │   └── env.*              # - 迁移环境
│       ├── middlewares/           # 模块级中间件（可选）
│       ├── utils/                 # 模块工具函数（可选）
│       ├── common/                # 模块公共定义（可选）
│       ├── module.*               # 模块声明（必需）
│       └── app.*                  # 独立应用工厂（可选）
│
└── tests/                         # 测试目录
    └── {module}/
        ├── fixtures/              # 测试夹具
        ├── unit/                  # 单元测试
        └── integration/           # 集成测试
```

## 统一基础设施及架构

### 基础设施

| 组件 | 用途 |
|------|------|
| PostgreSQL + pgvector | 主数据库：关系数据存储 + 向量检索 |
| Redis | 缓存 / 队列 / 发布订阅 |
| MinIO | 对象存储：文件、图片等非结构化数据 |

### 架构规则

| 规则 | 说明 |
|------|------|
| 分层架构 | Controller → Service → Model |
| Schema 隔离 | 每个模块独立 PostgreSQL schema |
| 依赖边界 | 业务模块可依赖 framework，反向禁止 |
| 跨模块调用 | 通过 inner 接口或事件总线，禁止直接依赖 |

## 层次职责

### 基础设施层（framework/）

| 目录 | 职责 | 说明 |
|------|------|------|
| `database/core/` | 数据库核心 | 引擎管理、会话工厂、模型基类 |
| `database/mixins/` | 模型混入 | 可复用的模型能力（树、租户、审计、时间戳） |
| `database/types/` | 自定义类型 | 数据库列类型封装 |
| `database/events/` | 事件监听 | 数据库事件钩子 |
| `database/interceptors/` | 拦截器 | 查询拦截、软删除等 |
| `cache/` | 缓存 | Redis 工具、租户缓存管理 |
| `storage/` | 对象存储 | MinIO/OSS/腾讯云存储封装 |
| `queue/` | 消息队列 | Redis Stream 队列封装 |
| `pubsub/` | 发布订阅 | Redis PubSub 封装 |
| `lock/` | 分布式锁 | Redis/数据库锁实现 |
| `schemas/` | 公共 Schema | 跨模块共享的 VO（如 TreeVo） |
| `utils/` | 工具函数 | 加密、JWT、时间、树工具等 |
| `middlewares/` | 中间件 | 跨切面中间件 |
| `clients/` | 内部客户端 | 模块间 HTTP 调用 |
| `events/` | 事件总线 | 领域事件发布 |
| `module/` | 模块系统 | 模块加载、注册、生命周期 |
| `tenant/` | 多租户 | 租户上下文、中间件、解析器 |

### 业务模块层（{module}/）

| 目录 | 职责 | 说明 |
|------|------|------|
| `controllers/` | API 控制器 | 路由定义、参数校验、响应封装 |
| `services/` | 业务逻辑层 | 事务边界、业务校验、跨模型协作 |
| `models/` | 数据库模型 | ORM 模型定义、表映射 |
| `schemas/` | DTO 模型 | 请求/响应 Schema、VO 定义 |
| `listeners/` | 消息监听器 | PubSub/Queue 消息处理 |
| `tasks/` | 定时任务 | 本地任务、集群唯一任务 |
| `migrations/` | 数据库迁移 | Alembic 迁移版本、种子数据 |
| `module.*` | 模块声明 | 实现 ModuleDescriptor 协议 |

## Service 层职责规范

### 核心职责

Service 层是业务逻辑的核心，负责：

| 职责 | 说明 |
|------|------|
| 事务边界 | 管理数据库事务的生命周期 |
| 业务校验 | 执行业务规则验证 |
| 跨模型协作 | 协调多个 Model 的操作 |
| 数据聚合 | 组合多个数据源返回完整响应 |

### 聚合方法规范

Service 层提供聚合方法，用于组合多个数据源并返回完整的响应 Schema 对象。

**命名规范**：

- 聚合方法命名为 `get_<entity>_detail()` 或 `get_<entity>_full()`
- 返回类型为对应的响应 Schema 类型，如 `UserDetailResponse | None`

### Service 调用规则

| 场景 | 规则 | 示例 |
|------|------|------|
| 同模块 Service 调用 | ✅ 直接导入调用 | `user_roles_service.get_user_roles(user_id)` |
| 跨模块 Service 调用 | ⚠️ 通过 Inner 接口 | `tenant_service.get_tenants_by_ids(tenant_ids)` |

**跨模块调用原则**：

- 禁止直接导入其他模块的 Service
- 通过 `/{module}/inner/v1` 接口或框架机制调用
- 明确模块依赖方向，避免循环依赖

## Schema 层转换规范

### 转换方法规则

Schema 层提供 `from_entity()` 类方法，用于处理复杂转换逻辑。

**简单转换**：提供 `from_attributes` 属性的自动映射

**复杂转换**：提供 `from_entity()` 类方法，处理计算、合并、裁剪等复杂操作

### 转换方法参数规范

| 场景 | 方法签名 |
|------|----------|
| 单实体转换 | `from_entity(cls, entity: EntityType) -> SchemaType` |
| 多数据源转换 | `from_user(cls, user: User, roles: list[Role], ...) -> SchemaType` |

### 转换方法禁止事项

| 禁止 | 说明 |
|------|------|
| 数据库查询 | 转换方法不得执行数据库查询，所需数据由 Service 传入 |
| 业务规则验证 | 业务规则在 Service 层处理，Schema 只负责数据转换 |
| 副作用操作 | 转换方法必须是纯函数，无副作用 |

### 响应 Schema 命名规范

| 分类 | 命名模式 | 示例 |
|------|----------|------|
| 简单响应 | `{Entity}Response` | `UserResponse` |
| 聚合响应 | `{Entity}DetailResponse` | `UserDetailResponse` |
| 列表响应 | `{Entity}ListResponse` | `ModelListResponse` |
| 分页列表响应 | `{Entity}PaginatedListResponse` | `UserPaginatedListResponse` |
| 树结构响应 | `{Entity}TreeResponse` | `ModuleMenuTreeResponse` |

## 命名规范

### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 模型文件 | 小写下划线 | `dataset.py`, `user_role.py` |
| Schema 文件 | 小写下划线 | `dataset.py`, `chat.py` |
| 服务文件 | 小写下划线 | `dataset.py`, `credential_service.py` |
| 控制器文件 | 小写下划线 | `dataset.py`, `health.py` |
| 迁移文件 | 序号前缀 | `001_demo_tables.py` |
| 处理器文件 | 小写下划线 + handler | `heartbeat_handler.py` |
| 任务文件 | 小写下划线 + task | `heartbeat_task.py` |

### 类命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 模型类 | 大驼峰 | `Dataset`, `User` |
| 混入类 | 大驼峰 + Mixin | `TreeNodeMixin`, `TenantMixin` |
| Schema 类 | 大驼峰 + DTO 后缀 | 详见下节「通信对象（DTO）命名规范」 |
| 服务类 | 大驼峰 + Service | `DatasetService` |
| 处理器类 | 大驼峰 + Handler | `HeartbeatHandler`, `DatasetNotifyHandler` |
| 工厂函数 | get_xxx_provider | `get_cache_provider`, `get_storage_provider` |

#### 通信对象（DTO）命名规范

前后端通信对象（Schema 类）命名遵循以下统一规范，{Entity}{Action}

| 分类 | 命名模式 | 示例 |
|------|----------|------|
| 非分页查询 | `{Entity}Query` | `DepartmentQuery` |
| 分页查询 | `{Entity}PaginatedQuery` | `TenantPaginatedQuery` |
| 新增（创建） | `{Entity}Create` | `TenantCreate` |
| 编辑（更新） | `{Entity}Update` | `TenantUpdate` |
| 保存（新增或编辑） | `{Entity}Save` | `ConfigSave` |
| 导入 | `{Entity}Import` | `UserImport` |
| 导出 | `{Entity}Export` | `UserExport` |
| 基本响应 | `{Entity}Response` | `TenantResponse` |
| 全量列表响应 | `{Entity}ListResponse` | `MenuListResponse` |
| 分页列表响应 | `{Entity}PaginatedListResponse` | `TenantPaginatedListResponse` |
| 树结构响应 | `{Entity}TreeResponse` | `ModuleMenuTreeResponse` |
| 属性/配置响应 | `{Entity}PropertyResponse` | `CachePropertyResponse` |

### 变量命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 服务实例 | 小写下划线 + service | `dataset_service` |
| 路由器 | 小写下划线 | `router` |
| 枚举 | 大驼峰 | `DatasetStatus`, `TreeNodeEventType` |
| 常量 | 大写下划线 | `HEARTBEAT_TOPIC`, `DEFAULT_SORT` |

### 树结构的字段命名

| 字段 | 说明 | 示例 |
|------|------|------|
| `parent_id` | 父节点 ID | `parent_id: str \| None` |
| `tree_level` | 树层级 | `tree_level: int` |
| `tree_leaf` | 是否叶子节点 | `tree_leaf: bool` |
| `tree_sort` | 排序号 | `tree_sort: int` |
| `tree_sorts` | 排序路径 | `tree_sorts: str` |
| `tree_names` | 名称路径 | `tree_names: str` |
| `parent_ids` | 祖先 ID 路径 | `parent_ids: str` |
| `tenant_id` | 租户 ID | `tenant_id: str` |
| `created_at` | 创建时间 | `created_at: datetime` |
| `updated_at` | 更新时间 | `updated_at: datetime` |
| `created_by` | 创建人 | `created_by: str` |
| `updated_by` | 更新人 | `updated_by: str` |

## API 规范

### 健康检查端点

所有技术栈必须提供统一的健康检查 API：

```
GET /health → {"status": "healthy", "timestamp": "..."}
```

### RESTful 规范

- URL 设计：资源导向，小写连字符分隔
- HTTP 方法：GET 查询、POST 创建、PUT 更新、DELETE 删除
- 响应格式：统一 JSON 结构，包含 `code`、`msg`、`data` 字段
- API 路由规范：遵循 `/{模块}/{类型}/v1/{功能}` 格式

### 响应结构

```json
{
  "code": 200,
  "msg": "success",
  "data": { ... },
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

### 统一响应工具类

各技术栈应提供统一的响应工具类，用于 Controller 层封装 HTTP 响应：

| 技术栈 | 文件位置 | 工具类 |
|--------|---------|--------|
| Python | `python/src/framework/schemas/base.py` | `Success`、`SuccessExtra`、`Fail` |
| Rust | `rust/src/demo/common/error.rs` | `ApiResponse<T>` |

## 数据模型规范

各技术栈应遵循统一的数据模型命名和结构规范，确保跨技术栈一致性。

### 查询模型

| 模型名 | 用途 | 必含字段 |
|--------|------|----------|
| `BaseQuery` | 列表查询基类 | `keyword: str \| None` |
| `BasePaginatedQuery` | 分页查询基类 | 继承 `BaseQuery`，添加 `page: int`、`page_size: int` |

**字段约束**：

- `page`：页码，最小值 1，默认值 1
- `page_size`：每页条数，最小值 1，最大值 100，默认值 20

### Mixin 模型

各技术栈应提供可复用的 Mixin 组件：

| Mixin 名 | 用途 | 字段 |
|----------|------|------|
| `TreeNodeMixin` | 树形结构 | `parent_id`、`tree_level`、`tree_leaf`、`tree_sort`、`parent_ids`、`tree_sorts`、`tree_names` |
| `TimestampMixin` | 时间戳 | `created_at`、`updated_at` |
| `AuditMixin` | 审计信息 | `created_by`、`updated_by`、`created_at`、`updated_at` |

## API 路由规范

### 路由格式

**统一格式**：`/{模块}/{类型}/v1/{功能}/{其他}`

| 组成部分 | 说明 | 可选值 |
|---------|------|--------|
| 模块 | 业务模块标识 | `tenant`、`iam`、`ai` |
| 类型 | 接口类型 | `admin`（管理端）、`console`（用户端）、`inner`（内部接口） |
| v1 | API 版本号 | 固定为 `v1` |
| 功能 | 资源名称 | `users`、`tenants`、`chat-messages` 等 |

### 路由示例

| 模块 | 类型 | 功能 | 完整路径 |
|------|------|------|---------|
| tenant | admin | tenants | `/tenant/admin/v1/tenants` |
| tenant | console | tenants | `/tenant/console/v1/tenants` |
| tenant | inner | tenants | `/tenant/inner/v1/tenants` |
| iam | admin | users | `/iam/admin/v1/users` |
| iam | console | auth/login | `/iam/console/v1/auth/login` |

### 中间件策略

| 路径前缀 | 认证方式 | 说明 |
|---------|---------|------|
| `/tenant/admin/*` | AdminAuthMiddleware | 租户管理员 Token 认证 |
| `/tenant/console/*` | IAMAuthMiddleware | JWT Token 认证 |
| `/iam/*` | IAMAuthMiddleware | JWT Token 认证 |
| `/*/inner/*` | 无认证 | 模块间内部调用 |

### 接口类型说明

| 类型 | 用途 | 权限 |
|------|------|------|
| admin | 管理后台接口 | 需要管理员权限 |
| console | 用户端接口 | 需要登录用户权限 |
| inner | 内部接口 | 无认证，仅供模块间调用 |

## 环境要求

| 技术栈 | 版本要求 | 包管理器 |
|--------|----------|----------|
| Python | 3.12+ | uv |
| Rust | 1.95+ | cargo |
| Java | 21+ | maven |
| .NET | 8.0+ | dotnet cli |

公共依赖：PostgreSQL 14+、Redis 6+、MinIO（可选）
