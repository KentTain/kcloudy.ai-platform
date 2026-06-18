# 默认资源配置初始化任务清单

## 1. 数据库模型修改

- [x] 1.1 为 `DatabaseConfig` 模型添加 `is_default` 字段（`Mapped[bool]`，默认 `False`）
- [x] 1.2 为 `CacheConfig` 模型添加 `is_default` 字段（`Mapped[bool]`，默认 `False`）
- [x] 1.3 为 `StorageConfig` 模型添加 `is_default` 字段（`Mapped[bool]`，默认 `False`）
- [x] 1.4 为 `QueueConfig` 模型添加 `is_default` 字段（`Mapped[bool]`，默认 `False`）
- [x] 1.5 为 `PubSubConfig` 模型添加 `is_default` 字段（`Mapped[bool]`，默认 `False`）

## 2. 数据库迁移

- [x] 2.1 创建迁移脚本 `004_add_is_default_to_resource_configs.py`
- [x] 2.2 添加 `is_default` 字段到五个资源配置表（非空，默认 `False`）
- [x] 2.3 创建部分唯一索引 `uix_database_configs_default`（WHERE is_default = TRUE）
- [x] 2.4 创建部分唯一索引 `uix_cache_configs_default`
- [x] 2.5 创建部分唯一索引 `uix_storage_configs_default`
- [x] 2.6 创建部分唯一索引 `uix_queue_configs_default`
- [x] 2.7 创建部分唯一索引 `uix_pubsub_configs_default`

## 3. Schema 响应模型修改

- [x] 3.1 为 `DatabasePropertyResponse` 添加 `is_default: bool` 字段
- [x] 3.2 为 `CachePropertyResponse` 添加 `is_default: bool` 字段
- [x] 3.3 为 `StoragePropertyResponse` 添加 `is_default: bool` 字段
- [x] 3.4 为 `QueuePropertyResponse` 添加 `is_default: bool` 字段
- [x] 3.5 为 `PubSubPropertyResponse` 添加 `is_default: bool` 字段

## 4. 种子数据脚本

- [x] 4.1 创建 `resource_config_seed.py` 文件
- [x] 4.2 实现数据库连接字符串解析函数 `_parse_database_url()`
- [x] 4.3 实现创建数据库配置函数 `_create_database_config()`
- [x] 4.4 实现创建缓存配置函数 `_create_cache_config()`
- [x] 4.5 实现创建存储配置函数 `_create_storage_config()`
- [x] 4.6 实现创建队列配置函数 `_create_queue_config()`
- [x] 4.7 实现创建发布订阅配置函数 `_create_pubsub_config()`
- [x] 4.8 实现主函数 `run()` 协调创建逻辑
- [x] 4.9 在 `module.py` 的 `get_seeds()` 中注册种子脚本

## 5. 租户种子脚本修改

- [ ] 5.1 修改 `tenant_seed.py` 查询默认资源配置
- [ ] 5.2 修改创建默认租户逻辑，关联默认配置 ID

## 6. 服务层修改

- [ ] 6.1 修改 `DatabaseConfigService.create()` 支持 `is_default` 唯一性控制
- [ ] 6.2 修改 `CacheConfigService.create()` 支持 `is_default` 唯一性控制
- [ ] 6.3 修改 `StorageConfigService.create()` 支持 `is_default` 唯一性控制
- [ ] 6.4 修改 `QueueConfigService.create()` 支持 `is_default` 唯一性控制
- [ ] 6.5 修改 `PubSubConfigService.create()` 支持 `is_default` 唯一性控制
- [ ] 6.6 创建 `_get_default_config()` 辅助函数
- [ ] 6.7 修改 `TenantService.create()` 支持自动填充默认配置

## 7. API 控制器修改

- [ ] 7.1 修改数据库配置查询接口，按 `is_default` 降序排序
- [ ] 7.2 修改缓存配置查询接口，按 `is_default` 降序排序
- [ ] 7.3 修改存储配置查询接口，按 `is_default` 降序排序
- [ ] 7.4 修改队列配置查询接口，按 `is_default` 降序排序
- [ ] 7.5 修改发布订阅配置查询接口，按 `is_default` 降序排序

## 8. 前端类型定义修改

- [ ] 8.1 为 `DatabaseConfig` 接口添加 `is_default: boolean` 字段
- [ ] 8.2 为 `CacheConfig` 接口添加 `is_default: boolean` 字段
- [ ] 8.3 为 `StorageConfig` 接口添加 `is_default: boolean` 字段
- [ ] 8.4 为 `QueueConfig` 接口添加 `is_default: boolean` 字段
- [ ] 8.5 为 `PubsubConfig` 接口添加 `is_default: boolean` 字段

## 9. 前端创建租户页面修改

- [ ] 9.1 添加资源配置查询 API 调用
- [ ] 9.2 实现配置选择器组件，支持 `is_default` 排序
- [ ] 9.3 实现默认配置自动选中逻辑
- [ ] 9.4 添加"+ 创建新配置"按钮，支持跳转到资源配置页面
- [ ] 9.5 修改创建租户表单提交逻辑

## 10. 文档更新

- [ ] 10.1 更新 `server/python/README.md` 说明默认配置初始化机制
- [ ] 10.2 更新 API 文档说明 `is_default` 字段

## 11. 测试

- [ ] 11.1 编写数据库模型单元测试（`is_default` 字段）
- [ ] 11.2 编写种子脚本测试（默认配置创建）
- [ ] 11.3 编写服务层测试（`is_default` 唯一性控制）
- [ ] 11.4 编写租户创建测试（自动关联默认配置）
- [ ] 11.5 编写前端组件测试（配置选择器）
