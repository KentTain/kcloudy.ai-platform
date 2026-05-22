# Framework 模块测试指南

本文件为 Claude Code 在 `tests/framework/` 中编写和维护 framework 测试时提供指导。

## 测试范围

Framework 测试覆盖底层基础设施能力，包括配置、缓存、数据库、存储、队列、发布订阅、分布式锁、多租户上下文、租户资源隔离和通用工具。

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `fixtures/` | 测试夹具、辅助函数和测试配置 |
| `unit/` | 单元测试，使用 mock 或内存对象隔离外部依赖 |
| `integration/` | 集成测试，验证 Redis、PostgreSQL、MinIO 等真实服务交互 |
| `conftest.py` | framework 测试 fixture 入口 |

## 运行命令

```bash
# 全部 framework 测试
uv run pytest tests/framework/ -v

# 单元测试
uv run pytest tests/framework/unit/ -v

# 集成测试
uv run pytest tests/framework/integration/ -v
```

按组件运行：

```bash
uv run pytest tests/framework/unit/cache/ tests/framework/integration/cache/ -v
uv run pytest tests/framework/unit/database/ tests/framework/integration/database/ -v
uv run pytest tests/framework/integration/lock/ -v
uv run pytest tests/framework/integration/pubsub/ -v
uv run pytest tests/framework/integration/queue/ -v
uv run pytest tests/framework/integration/storage/ -v
uv run pytest tests/framework/unit/tenant/ tests/framework/integration/tenant/ -v
```

## 测试标记

| 标记 | 说明 |
| --- | --- |
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.integration` | 集成测试，依赖真实服务或跨组件协作 |
| `@pytest.mark.asyncio` | 异步测试 |
| `@pytest.mark.slow` | 慢测试 |

## 集成测试依赖

| 服务 | 用途 | 配置位置 |
| --- | --- | --- |
| Redis | 缓存、锁、队列、发布订阅、租户缓存隔离 | `config/application-local.yml` |
| PostgreSQL | 数据库、迁移、租户数据库隔离 | `config/application-local.yml` |
| MinIO | 对象存储与租户存储隔离 | `config/application-local.yml` |

集成测试应在启动时检测外部服务可用性。服务不可用时跳过相关测试，不应让本地缺少外部服务导致测试套件整体失败。

## Fixture 约定

| Fixture | 作用域 | 用途 |
| --- | --- | --- |
| `integration_settings` | session | 加载集成测试配置 |
| `redis_client` | session | Redis 客户端或 RedisUtil 初始化 |
| `redis_key_prefix` | function | 为每个用例生成唯一键前缀 |
| `postgres_engine` | session | PostgreSQL 异步引擎 |
| `postgres_session` | function | PostgreSQL 会话，测试后回滚 |
| `minio_client` | session | MinIO 存储实例 |
| `minio_test_bucket` | function | 唯一测试 Bucket，测试后清理 |

服务可用性 fixture 包括 `redis_available`、`postgres_available`、`minio_available`。

## 数据隔离规则

- Redis 测试必须使用唯一 key 前缀并在测试后清理。
- PostgreSQL 测试使用独立会话，优先通过事务回滚清理数据。
- MinIO 测试使用唯一测试 Bucket 或对象前缀，测试后删除。
- 多租户隔离测试需同时验证默认资源路径和租户专属资源路径。
- 避免在生产环境运行集成测试。

## 覆盖重点

| 组件 | 单元测试 | 集成测试 |
| --- | --- | --- |
| `cache` | RedisUtil、TenantCacheManager | Redis 行为验证 |
| `database` | BaseModel、Mixin、EnginePool | PostgreSQL 会话与事务 |
| `storage` | TenantStorageManager | MinIO 上传、下载、清理 |
| `lock` | 工厂与接口 | Redis / SQLAlchemy 分布式锁 |
| `queue` | Handler 与接口 | Redis Stream 消费 |
| `pubsub` | Handler 与接口 | Redis Pub/Sub |
| `tenant` | TenantContext、协议、模型 | 租户上下文与隔离 |
| `utils` | crypto、jwt、session、json、time 等 | 按需补充 |
| `configs` | 配置加载与环境变量覆盖 | 按需补充 |

## 编写测试时注意

1. 单元测试不访问真实外部服务。
2. 集成测试依赖真实服务时必须可跳过、可重复运行、可清理。
3. 涉及加密、Token、Session 的测试要覆盖正常路径和异常路径。
4. 涉及多租户隔离的测试要验证租户 A 与租户 B 数据不会串用。
