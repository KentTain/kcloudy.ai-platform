# IAM 模块开发指南

## 概述

IAM（Identity and Access Management）模块提供身份认证和权限管理功能。

## 模块结构

```
iam/
├── controllers/    # API 控制器
│   ├── admin/      # 管理后台接口
│   └── console/    # 用户端接口
├── services/       # 业务逻辑层
├── models/         # 数据库模型
├── schemas/        # Pydantic 模型
├── migrations/     # 数据库迁移
├── initializers/   # 初始化器
└── middlewares/    # 中间件
```

## 核心功能

| 功能 | 说明 |
|------|------|
| 租户管理 | 多租户创建、配置、过期管理 |
| 用户认证 | JWT 令牌、密码验证 |
| 权限控制 | 基于角色的访问控制 |
| 资源配置 | 租户级数据库、存储、缓存物理隔离 |
| 租户上下文 | 通过 X-Tenant-Id 解析当前租户并注入 TenantContext |

## 角色体系

| 角色 | 职责 | 核心场景 |
|------|------|----------|
| 租户管理员 | 创建租户、管理租户级系统管理员 | 系统初始化时创建，负责租户开通 |
| 系统管理员 | 管理本租户的组织架构、用户、角色、权限 | 租户内的管理操作 |
| 普通用户 | 使用系统业务功能 | 日常登录、个人信息管理 |

## 启动初始化

应用启动时会自动执行 IAM seed：默认租户、预定义角色权限、默认租户管理员。初始化异常会记录日志但不阻止应用启动。

## 租户资源配置

Tenant 模型支持以下资源配置字段：

### 数据库配置

| 字段 | 类型 | 说明 |
|------|------|------|
| db_type | str | 数据库类型（postgresql/mysql/sqlite） |
| db_host | str | 数据库主机 |
| db_port | int | 数据库端口 |
| db_name | str | 数据库名称（配置后启用物理隔离） |
| db_username | str | 数据库用户名 |
| db_password | str | 数据库密码（AES-256-GCM 加密存储） |

### 存储配置

| 字段 | 类型 | 说明 |
|------|------|------|
| storage_type | str | 存储类型（minio/aliyun/tencent） |
| storage_bucket | str | 存储桶名称（配置后启用物理隔离） |

### 缓存配置

| 字段 | 类型 | 说明 |
|------|------|------|
| cache_db | int | Redis DB 编号（0-15，配置后启用物理隔离） |

### 加密密钥

| 字段 | 类型 | 说明 |
|------|------|------|
| encryption_key | str | 租户加密密钥（主密钥加密存储） |

## 使用示例

### 创建带物理隔离的租户

```python
from iam.services.tenant_service import TenantService

tenant = await TenantService.create(
    name="高安全租户",
    code="secure_tenant",
    # 数据库配置
    db_type="postgresql",
    db_host="db.example.com",
    db_port=5432,
    db_name="tenant_secure_db",
    db_username="tenant_user",
    db_password="secure_password",  # 自动加密存储
    # 存储配置
    storage_type="minio",
    storage_bucket="tenant-secure-bucket",
    # 缓存配置
    cache_db=5,
)
```

### 更新租户资源配置

```python
tenant = await TenantService.update(
    tenant_id="tenant-001",
    db_name="new_database",
    db_password="new_password",  # 自动加密
)
```

### 获取租户完整配置

```python
from iam.services.tenant_provider_impl import iam_tenant_provider

tenant_info = await iam_tenant_provider.get_tenant("tenant-001")

# 访问资源配置
if tenant_info.database:
    print(f"数据库: {tenant_info.database.database}")
if tenant_info.storage:
    print(f"存储桶: {tenant_info.storage.bucket}")
if tenant_info.cache:
    print(f"Redis DB: {tenant_info.cache.db}")
```

## 隔离模式

| 模式 | 数据库 | 存储 | 缓存 |
|------|--------|------|------|
| 逻辑隔离 | 共享 DB + tenant_id 过滤 | 共享 Bucket + 路径前缀 | 共享 DB + Key 前缀 |
| 物理隔离 | 独立 Database | 独立 Bucket | 独立 Redis DB |

**切换方式**：配置 `db_name`、`storage_bucket`、`cache_db` 字段后自动启用物理隔离。

## 安全注意事项

1. **密码加密**：`db_password` 字段使用 AES-256-GCM 加密存储
2. **密钥管理**：每个租户生成独立的 `encryption_key`，由主密钥加密保护
3. **主密钥**：通过环境变量 `TENANT_ENCRYPTION_MASTER_KEY` 配置

## API 端点

- `/admin/v1/tenants` - 租户 CRUD
- `/admin/v1/tenants/validate/database` - 验证数据库配置
- `/admin/v1/tenants/validate/storage` - 验证存储配置
- `/admin/v1/tenants/validate/cache` - 验证缓存配置
