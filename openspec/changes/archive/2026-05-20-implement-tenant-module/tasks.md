## 1. 租户模型与数据库迁移

- [x] 1.1 创建 `Tenant` 模型（`src/demo/models/tenant.py`）
- [x] 1.2 创建 `TenantConfig` 模型（`src/demo/models/tenant_config.py`）
- [x] 1.3 创建 `TenantAdmin` 模型（`src/demo/models/tenant_admin.py`）
- [x] 1.4 创建 `UserTenant` 用户-租户关联模型（`src/demo/models/user_tenant.py`）
- [x] 1.5 创建数据库迁移脚本（`src/demo/migrations/versions/20260520_001_add_tenant_tables.py`）

## 2. 租户上下文与中间件

- [x] 2.1 完善租户上下文管理（`src/demo/framework/tenant/context.py`）
- [x] 2.2 创建租户解析器（`src/demo/framework/tenant/resolver.py`）
- [x] 2.3 创建租户中间件（`src/demo/framework/tenant/middleware.py`）
- [x] 2.4 创建租户相关异常类（`src/demo/framework/tenant/exceptions.py`）
- [x] 2.5 编写租户上下文单元测试（`tests/framework/tenant/test_context.py`）

## 3. 租户服务层

- [x] 3.1 创建租户服务（`src/demo/services/tenant_service.py`）
- [x] 3.2 实现租户缓存（`src/demo/framework/tenant/cache.py`）
- [x] 3.3 实现租户缓存失效通知（Redis Pub/Sub）
- [ ] 3.4 编写租户服务单元测试（`tests/services/test_tenant_service.py`）

## 4. 数据库隔离增强

- [x] 4.1 完善 `TenantMixin`（`src/demo/framework/database/mixins/tenant.py`）
- [x] 4.2 完善 `TenantEventListener`（`src/demo/framework/database/events/tenant.py`）
- [x] 4.3 实现查询拦截器自动过滤 tenant_id（`src/demo/framework/database/interceptors/tenant.py`）
- [ ] 4.4 编写数据库隔离单元测试（`tests/framework/database/test_tenant_isolation.py`）

## 5. Redis 隔离实现

- [x] 5.1 改造 `RedisUtil` 支持自动租户前缀（`src/demo/framework/cache/redis_util.py`）
- [x] 5.2 实现缓存 Key 隔离
- [x] 5.3 实现队列 Stream Key 隔离
- [x] 5.4 实现发布订阅 Channel 隔离
- [x] 5.5 实现锁 Key 隔离
- [ ] 5.6 编写 Redis 隔离单元测试（`tests/framework/cache/test_tenant_redis.py`）

## 6. MinIO 存储隔离实现

- [x] 6.1 改造 `StorageService` 支持自动租户目录前缀（`src/demo/framework/storage/minio_service.py`）
- [x] 6.2 实现上传/下载路径隔离
- [x] 6.3 实现预签名 URL 包含租户路径
- [x] 6.4 实现对象列举隔离
- [ ] 6.5 编写存储隔离单元测试（`tests/framework/storage/test_tenant_storage.py`）

## 7. 异步任务租户上下文支持

- [x] 7.1 定义任务消息格式（`src/demo/framework/queue/task_message.py`）
- [x] 7.2 实现任务入队自动携带 tenant_id（`src/demo/framework/queue/task_queue.py`）
- [x] 7.3 实现任务执行器自动恢复租户上下文（`src/demo/framework/queue/task_executor.py`）
- [ ] 7.4 编写异步任务租户上下文测试（`tests/framework/queue/test_tenant_task.py`）

## 8. 管理后台 API

- [x] 8.1 创建管理员认证中间件（`src/demo/middlewares/admin_auth_middleware.py`）
- [x] 8.2 创建管理后台租户控制器（`src/demo/controllers/admin/tenant_controller.py`）
- [x] 8.3 实现租户列表 API（`GET /admin/v1/tenants`）
- [x] 8.4 实现租户创建 API（`POST /admin/v1/tenants`）
- [x] 8.5 实现租户详情 API（`GET /admin/v1/tenants/{id}`）
- [x] 8.6 实现租户更新 API（`PUT /admin/v1/tenants/{id}`）
- [x] 8.7 实现租户删除 API（`DELETE /admin/v1/tenants/{id}`）
- [x] 8.8 实现租户激活 API（`POST /admin/v1/tenants/{id}/activate`）
- [x] 8.9 实现租户停用 API（`POST /admin/v1/tenants/{id}/deactivate`）
- [x] 8.10 实现租户统计 API（`GET /admin/v1/tenants/{id}/stats`）
- [x] 8.11 创建相关 Schema（`src/demo/schemas/admin/tenant.py`）

## 9. 用户端租户 API

- [x] 9.1 创建用户端租户控制器（`src/demo/controllers/console/tenant_controller.py`）
- [x] 9.2 实现获取可用租户列表 API（`GET /console/v1/tenants`）
- [x] 9.3 实现获取当前租户信息 API（`GET /console/v1/tenants/current`）
- [x] 9.4 实现租户切换 API（`POST /console/v1/tenants/{id}/switch`）
- [x] 9.5 创建相关 Schema（`src/demo/schemas/console/tenant.py`）

## 10. 默认租户管理员初始化

- [x] 10.1 创建租户管理员初始化器（`src/demo/initializers/tenant_admin_initializer.py`）
- [x] 10.2 在应用启动时调用初始化器

## 11. 集成测试

- [x] 11.1 编写租户上下文集成测试（`tests/integration/test_tenant_context.py`）
- [x] 11.2 编写租户隔离集成测试（`tests/integration/test_tenant_isolation.py`）
- [x] 11.3 编写管理后台 API 集成测试（`tests/integration/test_tenant_admin_api.py`）
- [x] 11.4 编写用户端 API 集成测试（`tests/integration/test_tenant_user_api.py`）
