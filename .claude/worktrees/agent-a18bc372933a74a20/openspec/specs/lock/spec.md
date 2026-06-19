## ADDED Requirements

### Requirement: Redis 分布式锁实现
系统 SHALL 基于 Redis 实现分布式锁，使用 SET NX EX 命令保证原子性。

#### Scenario: 获取锁成功
- **WHEN** 调用 `lock.acquire("resource_key", ttl=30)` 且锁未被占用
- **THEN** 返回 Lock 对象，锁 30 秒后自动过期

#### Scenario: 获取锁失败
- **WHEN** 调用 `lock.acquire("resource_key")` 且锁已被其他进程持有
- **THEN** 返回 `None`

#### Scenario: 释放自己的锁
- **WHEN** 调用 `lock.release(lock_obj)` 且锁值匹配
- **THEN** 锁被释放

#### Scenario: 释放他人的锁失败
- **WHEN** 尝试释放非自己持有的锁
- **THEN** 释放失败，锁保持原状态

### Requirement: 锁自动续期
系统 SHALL 支持锁的自动续期功能，防止长时间任务执行时锁过期。

#### Scenario: 手动续期
- **WHEN** 调用 `lock.extend(lock_obj, ttl=60)`
- **THEN** 锁的过期时间延长到 60 秒

### Requirement: 锁超时等待
系统 SHALL 支持获取锁时的超时等待。

#### Scenario: 等待获取锁
- **WHEN** 调用 `lock.acquire("resource_key", timeout=10)` 且锁被占用
- **THEN** 等待最多 10 秒，期间锁释放则立即获取

#### Scenario: 超时放弃
- **WHEN** 等待 10 秒后锁仍未释放
- **THEN** 返回 `None`

### Requirement: 锁工厂
系统 SHALL 提供锁工厂，根据配置 `lock.provider` 返回对应的锁实现。

#### Scenario: 获取 Redis 锁
- **WHEN** 配置 `lock.provider=redis`
- **THEN** 工厂返回 RedisLock 实例

#### Scenario: 获取数据库锁
- **WHEN** 配置 `lock.provider=sqlalchemy`
- **THEN** 工厂返回 DatabaseLock 实例

### Requirement: 锁上下文管理器
系统 SHALL 支持使用 async with 语法管理锁生命周期。

#### Scenario: 上下文管理器获取锁
- **WHEN** 使用 `async with lock.acquire_context("key") as lock_obj:`
- **THEN** 自动获取锁，退出代码块时自动释放
