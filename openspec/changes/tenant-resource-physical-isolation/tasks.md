## 1. 验证已有修改

- [x] 1.1 验证 Tenant 模型字段完整性（确认内嵌字段已删除、关联字段保留）
- [x] 1.2 验证数据库迁移脚本正确性（003_tenant_resource_ref.py）
- [x] 1.3 验证缓存 L2 序列化/反序列化包含完整资源配置
- [x] 1.4 验证 TenantSettings 配置类已更新为关联 ID
- [x] 1.5 运行语法检查确认所有修改文件无错误

## 2. TenantCacheManager 增强

- [x] 2.1 添加 `_instance_clients: dict[str, Redis]` 属性用于缓存不同实例客户端
- [x] 2.2 实现 `_is_physical_isolation()` 方法判断是否使用物理隔离
- [x] 2.3 修改 `get_client()` 方法支持根据 host/port/password 连接不同实例
- [x] 2.4 实现 `_create_instance_client()` 方法创建实例级客户端
- [x] 2.5 添加 `release_idle_instances()` 方法清理空闲实例客户端
- [x] 2.6 更新 `close()` 方法关闭所有实例客户端
- [x] 2.7 更新 `_build_key()` 方法，物理隔离场景不添加租户前缀

## 3. TenantStorageManager 增强

- [x] 3.1 添加 `_instance_storages: dict[str, MinioStorage]` 属性缓存不同实例客户端
- [x] 3.2 实现 `get_storage()` 方法根据配置获取存储客户端
- [x] 3.3 实现 `_create_storage()` 方法创建实例级存储客户端
- [x] 3.4 修改 `upload()` 方法支持独立存储服务
- [x] 3.5 修改 `download()` 方法支持独立存储服务
- [x] 3.6 修改 `delete()` 方法支持独立存储服务
- [x] 3.7 修改 `exists()` 方法支持独立存储服务
- [x] 3.8 修改 `get_presigned_url()` 方法支持独立存储服务
- [x] 3.9 修改 `list_objects()` 方法支持独立存储服务
- [x] 3.10 添加 `release_idle_instances()` 方法清理空闲客户端
- [x] 3.11 更新 `close()` 方法关闭所有实例客户端

## 4. TenantQueueManager 实现

- [x] 4.1 创建 `framework/queue/tenant_queue_manager.py` 文件
- [x] 4.2 实现 `TenantQueueManager` 类框架
- [x] 4.3 实现实例客户端缓存（依赖 TenantCacheManager）
- [x] 4.4 实现 `xadd()` 发送消息方法
- [x] 4.5 实现 `xreadgroup()` 消费消息方法
- [x] 4.6 实现 `xack()` 确认消息方法
- [x] 4.7 实现队列名隔离逻辑（物理隔离 vs 逻辑隔离）
- [x] 4.8 添加全局管理器初始化函数 `init_queue_manager()`
- [x] 4.9 添加全局获取函数 `get_queue_manager()`

## 5. TenantPubSubManager 实现

- [x] 5.1 创建 `framework/pubsub/tenant_pubsub_manager.py` 文件
- [x] 5.2 实现 `TenantPubSubManager` 类框架
- [x] 5.3 实现实例客户端缓存（依赖 TenantCacheManager）
- [x] 5.4 实现 `publish()` 发布消息方法
- [x] 5.5 实现 `subscribe()` 订阅频道方法
- [x] 5.6 实现 `unsubscribe()` 取消订阅方法
- [x] 5.7 实现频道名隔离逻辑（物理隔离 vs 逻辑隔离）
- [x] 5.8 添加全局管理器初始化函数 `init_pubsub_manager()`
- [x] 5.9 添加全局获取函数 `get_pubsub_manager()`

## 6. 单元测试

- [x] 6.1 测试 TenantCacheManager 物理隔离场景
- [x] 6.2 测试 TenantCacheManager 客户端缓存
- [x] 6.3 测试 TenantStorageManager 物理隔离场景
- [x] 6.4 测试 TenantStorageManager 客户端缓存
- [x] 6.5 测试 TenantQueueManager 消息发送和消费
- [x] 6.6 测试 TenantPubSubManager 发布和订阅

## 7. 集成测试与文档

- [ ] 7.1 编写集成测试验证完整流程
- [ ] 7.2 更新 API 文档说明资源配置使用方式
- [ ] 7.3 更新 CLAUDE.md 添加物理隔离使用说明