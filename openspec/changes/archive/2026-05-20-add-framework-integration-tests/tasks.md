## 1. 基础设施准备

- [x] 1.1 创建集成测试专用 conftest 文件 `tests/framework/conftest_integration.py`
- [x] 1.2 添加服务可用性检测 fixture（Redis、PostgreSQL、MinIO）
- [x] 1.3 配置 pytest 标记 `@pytest.mark.integration`

## 2. Redis 缓存集成测试

- [x] 2.1 创建 `tests/framework/cache/test_redis_integration.py`
- [x] 2.2 实现字符串操作测试（set/get/delete with TTL）
- [x] 2.3 实现健康检查测试
- [x] 2.4 实现连接池测试

## 3. Redis 分布式锁集成测试

- [x] 3.1 创建 `tests/framework/lock/test_lock_integration.py`
- [x] 3.2 实现锁获取与释放测试
- [x] 3.3 实现锁超时自动释放测试
- [x] 3.4 实现锁延长测试
- [x] 3.5 实现互斥访问测试

## 4. Redis Stream 队列集成测试

- [x] 4.1 创建 `tests/framework/queue/test_queue_integration.py`
- [x] 4.2 实现消息入队测试
- [x] 4.3 实现消息出队测试
- [x] 4.4 实现消息确认测试
- [x] 4.5 实现队列长度测试

## 5. Redis 发布订阅集成测试

- [x] 5.1 创建 `tests/framework/pubsub/test_pubsub_integration.py`
- [x] 5.2 实现消息发布测试
- [x] 5.3 实现订阅管理测试
- [x] 5.4 实现取消订阅测试

## 6. MinIO 对象存储集成测试

- [x] 6.1 创建 `tests/framework/storage/test_storage_integration.py`
- [x] 6.2 实现文件上传下载测试
- [x] 6.3 实现文件删除测试
- [x] 6.4 实现预签名 URL 测试
- [x] 6.5 实现存储桶操作测试

## 7. PostgreSQL 数据库集成测试

- [x] 7.1 创建 `tests/framework/database/test_database_integration.py`
- [x] 7.2 实现连接测试
- [x] 7.3 实现自定义类型映射测试（UUID、SnowflakeID）
- [x] 7.4 实现 Mixin 行为验证测试
- [x] 7.5 实现会话管理测试

## 8. 验证与清理

- [x] 8.1 运行所有集成测试验证通过（68 通过）
- [x] 8.2 确保测试数据正确清理
- [x] 8.3 更新 `tests/framework/CLAUDE.md` 文档
