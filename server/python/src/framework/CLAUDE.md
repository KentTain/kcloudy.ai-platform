# Framework 模块开发指南

本文件为 Claude Code 在 `src/framework/` 基础设施模块中工作时提供指导。

## 模块定位

Framework 是 Python 后端的底层基础设施模块，提供配置、缓存、数据库、存储、队列、发布订阅、分布式锁、多租户和通用工具能力。

## 依赖边界

```
demo / iam / ai ──▶ framework
framework ──X──▶ demo / iam / ai
```

- 业务模块可以依赖 framework
- framework 禁止依赖业务模块
- 如需业务能力，必须通过 Protocol、注册器或启动期注入实现依赖倒置

## 目录职责

| 目录 | 职责 |
|------|------|
| cache/ | Redis 工具、租户缓存管理 |
| clients/ | 内部 HTTP 客户端、IAM 客户端 |
| common/ | 通用上下文、异常、响应、枚举 |
| configs/ | YAML 配置加载、环境变量覆盖 |
| core/ | 存储队列发布订阅锁等 Protocol 抽象接口 |
| database/ | SQLAlchemy 基础模型、Mixin、引擎池 |
| lock/ | 分布式锁工厂与实现 |
| module/ | 模块动态加载系统、注册中心 |
| pubsub/ | 发布订阅工厂与 Redis 实现 |
| queue/ | 队列工厂、Redis Stream 实现 |
| schemas/ | Pydantic VO 基类 |
| storage/ | 对象存储工厂、MinIO/OSS 实现 |
| tenant/ | 租户模型、上下文、中间件 |
| utils/ | 加密、JWT、时间、树形结构等工具 |

## 核心组件

| 组件 | 用途 |
|------|------|
| TenantContext | 租户上下文管理（contextvars） |
| DatabaseEnginePool | 租户引擎池管理（LRU 缓存） |
| ModuleRegistry | 模块注册中心 |
| TenantCacheManager | 租户缓存管理器 |
| TenantStorageManager | 租户存储管理器 |

## 多租户资源隔离

| 资源 | 物理隔离 | 逻辑隔离 |
|------|---------|---------|
| 数据库 | 独立 Database / Schema | tenant_id 字段过滤 |
| 缓存 | 独立 Redis DB | Key 前缀 {tenant_id}:{key} |
| 存储 | 独立 Bucket | 路径前缀 {tenant_id}/{path} |
| 队列 | 独立 Stream Key | Key 前缀 {tenant_id}:queue:{name} |

## 开发规则

- 抽象能力优先定义在 `core/` 或 `tenant/protocols.py`
- 根据配置选择实现时使用工厂函数
- 数据库模型继承 framework 提供的基类和 Mixin
- Redis、存储、队列等外部资源访问应通过 framework 封装入口
- 敏感租户配置使用 AES-256-GCM 加密工具处理

## 测试

- 单元测试：`tests/framework/unit/`
- 集成测试：`tests/framework/integration/`（依赖 Redis、PostgreSQL、MinIO）

```bash
uv run pytest tests/framework/unit/ -v
uv run pytest tests/framework/integration/ -v
```

详细设计和使用示例见 [README.md](README.md)。
