## Context

Framework 模块提供统一的基础设施组件，包括 cache、lock、queue、pubsub、storage、database 等。当前测试覆盖仅限于单元测试（使用 mock），无法验证与真实服务的集成。

**约束条件：**
- 集成测试需要外部服务（Redis、PostgreSQL、MinIO）
- 测试应可独立运行，不依赖特定环境顺序
- 需要支持跳过集成测试（本地开发无服务时）

## Goals / Non-Goals

**Goals:**
- 为 framework 模块添加真实服务连接的集成测试
- 验证各组件与对应服务的正确交互
- 提供可复用的集成测试 fixture
- 确保测试可独立运行且幂等

**Non-Goals:**
- 不替换现有单元测试
- 不测试服务本身的正确性（假设服务已正确配置）
- 不涉及性能测试或压力测试

## Decisions

### 1. 测试组织结构

**决策：** 在 `tests/framework/` 目录下按模块组织集成测试，使用 `_integration.py` 后缀区分。

**理由：**
- 与现有单元测试保持在同一目录结构
- 使用文件命名后缀而非子目录，便于查找和维护
- 可通过 pytest 的 `-k` 参数选择性运行

**目录结构：**
```
tests/framework/
├── cache/
│   ├── test_redis_util.py        # 单元测试（mock）
│   └── test_redis_integration.py # 集成测试
├── lock/
│   └── test_lock_integration.py
├── queue/
│   └── test_queue_integration.py
├── pubsub/
│   └── test_pubsub_integration.py
├── storage/
│   └── test_storage_integration.py
├── database/
│   └── test_database_integration.py
└── conftest_integration.py       # 集成测试专用 fixture
```

### 2. 测试标记策略

**决策：** 使用 `@pytest.mark.integration` 标记所有集成测试。

**理由：**
- pytest 标记是标准做法
- 便于通过 `-m "not integration"` 跳过集成测试
- CI 环境可选择性运行

### 3. Fixture 设计

**决策：** 创建独立的集成测试 fixture 模块，使用 session 作用域复用连接。

**理由：**
- 避免每个测试重新建立连接的开销
- 隔离集成测试 fixture 与单元测试 fixture
- 支持测试后清理

### 4. 服务可用性检测

**决策：** 测试启动时检测服务可用性，不可用时跳过测试。

**理由：**
- 本地开发环境可能没有所有服务
- 避免因服务不可用导致测试失败
- 使用 `pytest.skip()` 实现优雅跳过

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| 集成测试运行时间较长 | 使用 session 作用域 fixture，复用连接 |
| 服务不可用时测试失败 | 启动时检测并跳过 |
| 测试数据残留污染 | 每个测试使用唯一键前缀，测试后清理 |
| 并发测试冲突 | 使用随机 UUID 作为测试标识 |
