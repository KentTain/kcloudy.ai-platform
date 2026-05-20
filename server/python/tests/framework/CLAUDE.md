# Framework 模块测试

本文件为 Claude Code 在 Framework 模块测试目录中工作时提供指导。

## 测试目录结构

```
tests/framework/
├── conftest.py                    # 测试 fixtures 入口
├── conftest_integration.py        # 集成测试专用 fixtures
├── cache/
│   ├── test_redis_util.py         # Redis 单元测试（mock）
│   └── test_redis_integration.py  # Redis 集成测试
├── lock/
│   └── test_lock_integration.py   # 分布式锁集成测试
├── queue/
│   └── test_queue_integration.py  # Redis Stream 队列集成测试
├── pubsub/
│   └── test_pubsub_integration.py # Redis 发布订阅集成测试
├── storage/
│   └── test_storage_integration.py # MinIO 存储集成测试
├── database/
│   ├── test_database.py           # 数据库单元测试
│   └── test_database_integration.py # PostgreSQL 集成测试
├── common/
│   └── test_common.py             # 通用组件测试
├── utils/
│   └── test_utils.py              # 工具函数测试
├── core/
│   └── test_core.py               # 核心接口测试
├── configs/
│   └── test_config.py             # 配置模块测试
└── tenant/
    └── test_tenant.py             # 租户模块测试
```

## 运行测试

### 运行所有测试

```bash
# 运行所有 framework 测试
uv run pytest tests/framework/ -v

# 运行单元测试（排除集成测试）
uv run pytest tests/framework/ -v -m "not integration"

# 运行集成测试
uv run pytest tests/framework/ -v -m integration
```

### 运行特定模块测试

```bash
# Redis 缓存测试
uv run pytest tests/framework/cache/ -v

# 分布式锁测试
uv run pytest tests/framework/lock/ -v

# 队列测试
uv run pytest tests/framework/queue/ -v

# 发布订阅测试
uv run pytest tests/framework/pubsub/ -v

# 存储测试
uv run pytest tests/framework/storage/ -v

# 数据库测试
uv run pytest tests/framework/database/ -v
```

## 测试标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.integration` | 集成测试（需要真实服务） |
| `@pytest.mark.asyncio` | 异步测试 |

## 集成测试依赖服务

集成测试需要以下外部服务：

| 服务 | 用途 | 配置位置 |
|------|------|----------|
| Redis | 缓存、锁、队列、发布订阅 | `config/application-local.yml` |
| PostgreSQL | 数据库 | `config/application-local.yml` |
| MinIO | 对象存储 | `config/application-local.yml` |

### 服务不可用时的行为

- 测试启动时检测服务可用性
- 服务不可用时自动跳过相关测试
- 不会因服务不可用而导致测试失败

## 集成测试 Fixtures

### 核心 fixtures

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `integration_settings` | session | 加载配置 |
| `redis_client` | session | Redis 客户端（RedisUtil） |
| `redis_key_prefix` | function | 唯一键前缀 |
| `postgres_engine` | session | PostgreSQL 引擎 |
| `postgres_session` | function | PostgreSQL 会话 |
| `minio_storage` | session | MinIO 存储实例 |
| `minio_test_bucket` | function | 测试存储桶名 |

### 服务可用性检测

| Fixture | 说明 |
|---------|------|
| `redis_available` | Redis 服务可用性 |
| `postgres_available` | PostgreSQL 服务可用性 |
| `minio_available` | MinIO 服务可用性 |

## 测试数据隔离

- Redis: 使用 `redis_key_prefix` 生成唯一键前缀
- PostgreSQL: 使用独立会话，测试后回滚
- MinIO: 使用唯一存储桶名，测试后清理

## 注意事项

1. 集成测试运行时间较长，建议在 CI 中单独运行
2. 大文件上传测试可能因网络问题超时，已标记为跳过
3. 测试完成后会自动清理测试数据
4. 避免在生产环境运行集成测试

## 测试覆盖

| 模块 | 单元测试 | 集成测试 |
|------|----------|----------|
| cache | ✅ | ✅ |
| lock | - | ✅ |
| queue | - | ✅ |
| pubsub | - | ✅ |
| storage | - | ✅ |
| database | ✅ | ✅ |
| common | ✅ | - |
| utils | ✅ | - |
| core | ✅ | - |
| configs | ✅ | - |
| tenant | ✅ | - |
