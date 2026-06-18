# 默认资源配置初始化设计文档

## 上下文

### 背景

当前租户模块的资源配置（数据库、缓存、存储、队列、发布订阅）需要手动创建和关联。创建租户时，必须显式指定资源配置 ID，否则租户将没有任何资源配置关联。

### 当前状态

**资源配置模型**：
- `DatabaseConfig`、`CacheConfig`、`StorageConfig`、`QueueConfig`、`PubSubConfig` 已存在
- 每个配置模型包含连接参数和加密后的敏感字段
- 缺少"默认配置"的概念

**租户模型**：
- `Tenant` 模型已有 `db_config_id`、`cache_config_id` 等外键字段
- 创建租户时这些字段可选（可以为 `None`）

**配置来源**：
- 平台配置在 `application.yml` 中
- 包含 `sqlalchemy.url`、`redis.single.*`、`oss.minio.*` 等配置

### 约束

- 必须保持向后兼容（现有租户不受影响）
- 必须支持租户级资源隔离（默认共享，支持独立配置）
- 敏感信息必须加密存储

### 利益相关者

- **运维人员**：负责创建和管理租户
- **开发人员**：使用租户资源配置进行开发
- **平台管理员**：管理默认配置

## 目标 / 非目标

### 目标

1. **自动化默认配置创建**：应用启动时自动从 `application.yml` 创建默认资源配置
2. **租户自动关联默认配置**：创建租户时，如果未指定配置，自动使用默认配置
3. **唯一默认配置保证**：每种配置类型只能有一个默认配置
4. **前端友好交互**：创建租户时显示配置选择器，默认配置排在第一位

### 非目标

1. **配置自动同步**：不自动同步 `application.yml` 变更到数据库（仅首次创建）
2. **多默认配置**：不支持每种配置类型有多个默认配置
3. **租户密钥传递**：不将 `encryption_key` 添加到 `TenantContext`（安全优先）

## 决策

### 决策 1：使用 `is_default` 字段标记默认配置

**选择**：为每个资源配置模型添加 `is_default: Mapped[bool]` 字段

**理由**：
- 查询简单：`select(Config).where(is_default=True)`
- 排序直观：`order_by(is_default.desc())`
- 符合现有模式

**考虑的替代方案**：
1. **硬编码默认 ID**：在配置文件中指定固定 ID
   - 缺点：需要管理多个 ID，容易出错
2. **单独的默认配置表**：存储默认配置 ID
   - 缺点：增加表数量，查询需要 JOIN

### 决策 2：数据库部分唯一索引保证唯一性

**选择**：使用 PostgreSQL 部分唯一索引

```sql
CREATE UNIQUE INDEX uix_database_configs_default
ON tenant.database_configs (is_default)
WHERE is_default = TRUE;
```

**理由**：
- 数据库层保证唯一性，避免并发问题
- 部分索引只约束 `is_default=TRUE` 的行
- PostgreSQL 原生支持

**考虑的替代方案**：
1. **应用层唯一性检查**：先查询再插入
   - 缺点：并发时可能产生竞态条件
2. **触发器**：使用数据库触发器
   - 缺点：复杂，难以调试

### 决策 3：种子数据在同一个脚本中创建配置和租户

**选择**：在 `resource_config_seed.py` 中只创建资源配置，`tenant_seed.py` 保持独立

**理由**：
- 职责分离：资源配置和租户是不同的领域
- 种子脚本可以独立运行
- 通过查询默认配置实现关联

**种子数据执行顺序**：
```python
# tenant/module.py
def get_seeds(self):
    return {
        "resource_config": resource_config_seed_run,  # 先执行
        "tenant": tenant_seed_run,                    # 后执行
    }
```

Python 3.7+ 字典保持插入顺序，保证执行顺序。

### 决策 4：敏感信息使用 AES-256-GCM 加密

**选择**：使用 `framework.utils.resource_crypto.encrypt_password()` 加密

**理由**：
- 已有工具函数，复用现有能力
- AES-256-GCM 提供认证加密
- 主密钥从环境变量获取，支持安全部署

**加密字段**：
- `DatabaseConfig.password`
- `CacheConfig.password`
- `StorageConfig.secret_key`
- `QueueConfig.password`
- `PubSubConfig.password`

### 决策 5：前端创建租户时跳转到资源配置页面

**选择**：点击"+ 创建新配置"跳转到资源配置页面

**理由**：
- 配置创建是独立功能，有专门的页面
- 避免在创建租户页面内联复杂的配置表单
- 用户体验一致

**流程**：
1. 用户在创建租户页面
2. 点击"+ 创建新配置"
3. 跳转到资源配置页面
4. 创建配置后返回创建租户页面
5. 新配置自动出现在选择器中

## 风险 / 权衡

### 风险 1：默认配置被误删

**风险**：用户可能删除默认配置，导致创建租户时找不到默认配置

**缓解措施**：
1. 前端删除确认时，提示"此配置是默认配置"
2. 如果配置被租户引用，禁止删除（外键约束）
3. 种子脚本每次启动检查是否存在默认配置，不存在则创建

### 风险 2：并发创建默认配置

**风险**：多个实例同时启动时可能并发创建默认配置

**缓解措施**：
1. 数据库部分唯一索引会在并发插入时抛出唯一约束错误
2. 种子脚本捕获 `IntegrityError`，跳过创建
3. 使用 `INSERT ... ON CONFLICT DO NOTHING`（PostgreSQL）

### 风险 3：配置文件变更不同步

**风险**：`application.yml` 中的配置变更后，数据库中的默认配置不会自动更新

**缓解措施**：
1. 文档明确说明：默认配置仅在首次创建时生成
2. 提供手动更新接口或命令（未来考虑）
3. 前端显示提示："默认配置来自应用初始化，请手动更新"

### 风险 4：密钥丢失导致数据无法解密

**风险**：环境变量 `TENANT_ENCRYPTION_MASTER_KEY` 丢失，导致所有加密数据无法解密

**缓解措施**：
1. 文档明确要求备份主密钥
2. 生产环境部署时检查主密钥配置
3. 开发环境自动生成主密钥并打印警告

## 迁移计划

### 阶段 1：数据库迁移

1. 创建迁移脚本 `XXX_add_is_default_to_resource_configs.py`
2. 添加 `is_default` 字段（默认 `False`，非空）
3. 创建部分唯一索引
4. 执行迁移：`uv run python manage.py db migrate --module tenant`

### 阶段 2：种子数据初始化

1. 创建 `resource_config_seed.py` 脚本
2. 应用启动时自动执行（通过 `ModuleDescriptor.get_seeds()`）
3. 检查默认配置是否存在，不存在则创建

### 阶段 3：服务层修改

1. 修改 `TenantService.create()` 支持自动填充默认配置
2. 修改资源配置服务支持 `is_default` 唯一性控制

### 阶段 4：前端集成

1. 修改类型定义添加 `is_default` 字段
2. 修改创建租户页面显示配置选择器

### 回滚策略

如果出现问题，可以：
1. 回滚代码到之前版本
2. 数据库迁移向下执行：`uv run python manage.py db downgrade -1`
3. 删除种子脚本注册

## 开放问题

无。所有关键设计决策已明确。
