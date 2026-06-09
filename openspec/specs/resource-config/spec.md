## ADDED Requirements

### 需求:数据库配置管理

系统必须支持数据库配置的 CRUD，配置独立于租户存在，多个租户可共享同一配置。

#### 场景:创建数据库配置
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/databases` 并提供 name、type、host、port、database、username、password
- **那么** 创建配置记录，密码 AES 加密存储

#### 场景:查询数据库配置列表
- **当** 管理员请求 `GET /api/v1/tenant/resource-configs/databases`
- **那么** 返回配置列表，密码字段脱敏返回

#### 场景:获取单个数据库配置
- **当** 管理员请求 `GET /api/v1/tenant/resource-configs/databases/{id}`
- **那么** 返回配置详情，密码字段脱敏返回

#### 场景:更新数据库配置
- **当** 管理员请求 `PUT /api/v1/tenant/resource-configs/databases/{id}`
- **那么** 更新配置信息；密码更新时重新加密

#### 场景:删除数据库配置
- **当** 管理员请求 `DELETE /api/v1/tenant/resource-configs/databases/{id}` 且配置未被租户引用
- **那么** 删除配置

#### 场景:删除已引用的数据库配置
- **当** 管理员尝试删除已被租户引用的配置
- **那么** 返回 HTTP 400，错误消息为"配置已被租户使用，禁止删除"

### 需求:数据库连通性测试

系统必须支持数据库配置的连通性测试。

#### 场景:测试连接成功
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/databases/{id}/test-connection` 且连接参数正确
- **那么** 返回连接成功，执行 `SELECT 1` 验证

#### 场景:测试连接失败
- **当** 管理员请求测试连接且连接参数错误
- **那么** 返回连接失败及具体错误信息

#### 场景:测试连接超时
- **当** 连接测试超过 5 秒
- **那么** 返回超时错误

### 需求:存储配置管理

系统必须支持存储配置的 CRUD，模式与数据库配置一致。

#### 场景:创建存储配置
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/storages` 并提供 name、type、bucket
- **那么** 创建存储配置记录

#### 场景:存储连通性测试
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/storages/{id}/test-connection`
- **那么** 检查 bucket 是否存在且可访问

### 需求:缓存配置管理

系统必须支持缓存配置的 CRUD。

#### 场景:创建缓存配置
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/caches` 并提供 name、host、port
- **那么** 创建缓存配置记录

#### 场景:缓存连通性测试
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/caches/{id}/test-connection`
- **那么** 执行 Redis `PING` 命令验证

### 需求:队列配置管理

系统必须支持队列配置的 CRUD。

#### 场景:创建队列配置
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/queues` 并提供 name、type、host、port
- **那么** 创建队列配置记录

#### 场景:队列连通性测试
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/queues/{id}/test-connection`
- **那么** 根据类型测试：Redis 用 PING，RabbitMQ 检查队列列表

### 需求:发布订阅配置管理

系统必须支持发布订阅配置的 CRUD。

#### 场景:创建发布订阅配置
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/pubsubs` 并提供 name、type、host、port
- **那么** 创建发布订阅配置记录

#### 场景:发布订阅连通性测试
- **当** 管理员请求 `POST /api/v1/tenant/resource-configs/pubsubs/{id}/test-connection`
- **那么** 根据类型测试：Redis 用 PING，Kafka 检查 topic 列表

### 需求:密码加密与脱敏

系统必须对资源配置中的密码字段进行加密存储和脱敏返回。

#### 场景:密码加密存储
- **当** 创建或更新资源配置包含密码字段
- **那么** 密码使用 AES 加密后存储

#### 场景:密码脱敏返回
- **当** 查询资源配置
- **那么** 密码字段返回 `"******"`，不暴露明文
