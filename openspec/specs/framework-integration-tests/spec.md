## ADDED Requirements

### Requirement: Redis 缓存集成测试

Framework 的 RedisUtil 类 SHALL 在真实 Redis 服务上进行集成测试，验证缓存操作的正确性。

#### Scenario: 字符串操作
- **WHEN** 调用 RedisUtil.set 设置键值对并指定 TTL
- **THEN** 键值正确存储，过期时间正确设置

#### Scenario: 键值获取
- **WHEN** 调用 RedisUtil.get 获取存在的键
- **THEN** 返回正确的值

#### Scenario: 键值删除
- **WHEN** 调用 RedisUtil.delete 删除键
- **THEN** 键被成功删除

#### Scenario: 健康检查
- **WHEN** 调用 RedisUtil.health_check
- **THEN** 服务可用时返回 True

---

### Requirement: Redis 分布式锁集成测试

Framework 的 RedisLock 类 SHALL 在真实 Redis 服务上进行集成测试，验证分布式锁的正确性。

#### Scenario: 锁获取与释放
- **WHEN** 调用 acquire 获取锁成功
- **THEN** 锁状态正确，释放后其他客户端可获取

#### Scenario: 锁超时
- **WHEN** 设置锁的 TTL 过期
- **THEN** 锁自动释放

#### Scenario: 锁延长
- **WHEN** 调用 extend 延长锁的 TTL
- **THEN** 锁的过期时间成功延长

#### Scenario: 互斥访问
- **WHEN** 一个客户端持有锁
- **THEN** 其他客户端无法同时获取同一把锁

---

### Requirement: Redis Stream 队列集成测试

Framework 的 RedisQueue 类 SHALL 在真实 Redis 服务上进行集成测试，验证消息队列的正确性。

#### Scenario: 消息入队
- **WHEN** 调用 enqueue 发送消息
- **THEN** 消息成功写入 Stream

#### Scenario: 消息出队
- **WHEN** 调用 dequeue 读取消息
- **THEN** 正确获取消息内容

#### Scenario: 消息确认
- **WHEN** 调用 ack 确认消息
- **THEN** 消息标记为已处理

#### Scenario: 队列长度
- **WHEN** 调用 get_queue_length
- **THEN** 返回正确的队列长度

---

### Requirement: Redis 发布订阅集成测试

Framework 的 RedisPubSub 类 SHALL 在真实 Redis 服务上进行集成测试，验证发布订阅的正确性。

#### Scenario: 消息发布
- **WHEN** 调用 publish 发布消息
- **THEN** 订阅者收到消息

#### Scenario: 订阅管理
- **WHEN** 调用 subscribe 订阅主题
- **THEN** 成功接收后续消息

#### Scenario: 取消订阅
- **WHEN** 调用 unsubscribe 取消订阅
- **THEN** 不再接收该主题的消息

---

### Requirement: MinIO 对象存储集成测试

Framework 的 MinioStorage 类 SHALL 在真实 MinIO 服务上进行集成测试，验证对象存储的正确性。

#### Scenario: 文件上传
- **WHEN** 调用 upload 上传文件
- **THEN** 文件成功存储并返回访问路径

#### Scenario: 文件下载
- **WHEN** 调用 download 下载已上传的文件
- **THEN** 返回正确的文件内容

#### Scenario: 文件删除
- **WHEN** 调用 delete 删除文件
- **THEN** 文件被成功删除

#### Scenario: 预签名 URL
- **WHEN** 调用 get_presigned_url 获取预签名 URL
- **THEN** 返回有效的访问 URL

#### Scenario: 存储桶操作
- **WHEN** 调用 bucket_exists 和 create_bucket
- **THEN** 正确检测和创建存储桶

---

### Requirement: PostgreSQL 数据库集成测试

Framework 的数据库组件 SHALL 在真实 PostgreSQL 服务上进行集成测试，验证数据库操作的正确性。

#### Scenario: 连接测试
- **WHEN** 创建数据库引擎并连接
- **THEN** 成功建立连接

#### Scenario: 自定义类型映射
- **WHEN** 使用 StringUUID、SnowflakeID 等自定义类型
- **THEN** 正确映射到数据库字段

#### Scenario: Mixin 行为验证
- **WHEN** 使用 AuditMixin、TenantMixin 等混入
- **THEN** 自动处理审计字段和租户隔离

#### Scenario: 会话管理
- **WHEN** 使用 async session 进行数据库操作
- **THEN** 事务正确提交和回滚

---

### Requirement: 集成测试 Fixture

集成测试 SHALL 提供可复用的 fixture 用于初始化和清理测试环境。

#### Scenario: 服务连接 fixture
- **WHEN** 测试需要连接外部服务
- **THEN** fixture 提供已初始化的连接

#### Scenario: 自动清理
- **WHEN** 测试完成
- **THEN** fixture 自动清理测试数据

#### Scenario: 服务不可用跳过
- **WHEN** 外部服务不可用
- **THEN** 测试自动跳过而非失败
