## 1. 数据库迁移 - Tenant 模型扩展

- [x] 1.1 创建数据库迁移脚本 `20260522_001_add_tenant_resource_config.py`
- [x] 1.2 添加数据库配置字段：`db_type`, `db_host`, `db_port`, `db_name`, `db_username`, `db_password`
- [x] 1.3 添加存储配置字段：`storage_type`, `storage_bucket`
- [x] 1.4 添加缓存配置字段：`cache_db`
- [x] 1.5 添加加密密钥字段：`encryption_key`
- [ ] 1.6 执行数据库迁移

## 2. Framework 模块 - 协议定义扩展

- [x] 2.1 更新 `framework/tenant/protocols.py` 添加 `TenantCacheConfig` 数据类
- [x] 2.2 更新 `TenantInfo` 协议添加 `cache` 属性
- [x] 2.3 更新 `SimpleTenant` 数据类支持缓存配置
- [x] 2.4 扩展 `TenantContext` 添加资源配置访问方法

## 3. Framework 模块 - 加密工具

- [x] 3.1 创建 `framework/utils/crypto.py` 加密工具模块
- [x] 3.2 实现 AES-256-GCM 加密函数 `encrypt()`
- [x] 3.3 实现 AES-256-GCM 解密函数 `decrypt()`
- [x] 3.4 实现主密钥管理（环境变量/配置文件/自动生成）
- [x] 3.5 添加加密工具单元测试

## 4. Framework 模块 - DatabaseEnginePool

- [x] 4.1 创建 `framework/database/core/engine_pool.py`
- [x] 4.2 实现 `DatabaseEnginePool` 类 - 连接池缓存管理
- [x] 4.3 实现惰性加载 `get_engine(tenant_id, config)`
- [x] 4.4 实现会话获取 `get_session(tenant_id, config)`
- [x] 4.5 实现 LRU 回收机制 `release_idle(timeout=1800)`
- [x] 4.6 实现最大连接池数量限制（默认 50）
- [x] 4.7 添加连接池状态监控接口
- [x] 4.8 添加 DatabaseEnginePool 单元测试

## 5. Framework 模块 - TenantStorageManager

- [x] 5.1 创建 `framework/storage/tenant_storage_manager.py`
- [x] 5.2 实现 `TenantStorageManager` 类 - 存储桶路由
- [x] 5.3 实现 `get_bucket(tenant_id)` 获取租户存储桶
- [x] 5.4 实现 `upload(tenant_id, path, data)` 上传文件
- [x] 5.5 实现 `download(tenant_id, path)` 下载文件
- [x] 5.6 实现 `delete(tenant_id, path)` 删除文件
- [x] 5.7 实现 `get_presigned_url(tenant_id, path)` 生成预签名 URL
- [x] 5.8 支持存储桶自动创建
- [x] 5.9 添加 TenantStorageManager 单元测试

## 6. Framework 模块 - TenantCacheManager

- [x] 6.1 创建 `framework/cache/tenant_cache_manager.py`
- [x] 6.2 实现 `TenantCacheManager` 类 - Redis DB 路由
- [x] 6.3 实现 `get_client(tenant_id)` 获取租户 Redis 客户端
- [x] 6.4 实现 `get_db(tenant_id)` 获取租户 Redis DB 编号
- [x] 6.5 实现 Redis 客户端缓存
- [x] 6.6 支持 DB 编号范围验证（0-15）
- [x] 6.7 添加 TenantCacheManager 单元测试

## 7. IAM 模块 - Tenant 模型更新

- [x] 7.1 更新 `iam/models/tenant.py` 添加资源配置字段
- [x] 7.2 更新 `iam/schemas/admin/tenant.py` 添加资源配置 Schema
- [x] 7.3 更新 `iam/services/tenant_service.py` 支持资源配置 CRUD
- [x] 7.4 实现数据库密码加密存储
- [x] 7.5 实现加密密钥自动生成
- [x] 7.6 更新 `iam/services/tenant_provider_impl.py` 返回完整资源配置
- [x] 7.7 更新 `SimpleTenant.from_model()` 映射资源配置字段

## 8. IAM 模块 - 控制器更新

- [x] 8.1 更新 `iam/controllers/admin/tenant_controller.py` 支持资源配置
- [x] 8.2 添加数据库连接验证端点
- [x] 8.3 添加存储桶验证端点
- [x] 8.4 添加 Redis DB 编号验证端点

## 9. 集成测试

- [ ] 9.1 添加 DatabaseEnginePool 集成测试
- [ ] 9.2 添加 TenantStorageManager 集成测试
- [ ] 9.3 添加 TenantCacheManager 集成测试
- [ ] 9.4 添加租户资源配置端到端测试
- [ ] 9.5 添加物理隔离验证测试

## 10. 文档更新

- [x] 10.1 更新 `server/python/src/framework/CLAUDE.md` 添加资源管理器说明
- [x] 10.2 更新 `server/python/src/iam/CLAUDE.md` 添加资源配置说明
- [x] 10.3 更新 `server/python/tests/framework/CLAUDE.md` 添加测试说明
