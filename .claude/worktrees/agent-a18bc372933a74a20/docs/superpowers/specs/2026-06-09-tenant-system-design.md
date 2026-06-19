# 租户系统设计文档

## 1. 概述

### 1.1 设计目标

重新设计租户系统的数据模型及功能，实现模块化、可扩展的租户管理体系。

### 1.2 核心架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                        模块定义层 (Tenant Module)                     │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────────┐                │
│  │  Module  │──│ ModuleMenu  │  │ ModulePermission │                │
│  └──────────┘  └─────────────┘  └──────────────────┘                │
│       │                                                              │
│       │ ┌──────────────┐  ┌─────────────────────┐                   │
│       └─│  ModuleRole  │──│ ModuleRolePermission│                   │
│         └──────────────┘  └─────────────────────┘                   │
│       │                                                              │
│       │ 分配模块（自动同步）                                          │
│       ▼                                                              │
├──────────────────────────────────────────────────────────────────────┤
│                        租户实例层 (IAM Module)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐│
│  │   Menu   │  │Permission│  │   Role   │  │ UserRole /           ││
│  │(ref_id)  │  │(ref_id)  │  │(ref_id)  │  │ RolePermission       ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

### 1.3 模块划分

| 模块 | 职责 |
|------|------|
| **Tenant 模块** | 租户管理、资源配置、模块定义、模块分配 |
| **IAM 模块** | 用户管理、角色管理、权限管理、菜单管理（租户实例层） |

### 1.4 数据层级

1. **模块定义层**（全局）：定义模块包含的菜单、权限、默认角色
2. **租户实例层**：租户实际使用的菜单、权限、角色（通过 `tenant_id` + `ref_id` 关联）

### 1.5 默认角色

每个模块定义两个默认角色：
- **系统管理员**：拥有模块所有权限（读 + 写）
- **普通用户**：只有查看权限（只读）

## 2. 模型设计

### 2.1 租户基础模型

#### Tenant（租户）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | String(100) | NOT NULL | 租户名称 |
| code | String(50) | UNIQUE, NOT NULL | 租户编码 |
| status | String(20) | NOT NULL, DEFAULT 'active' | 状态 |
| contact_name | String(100) | NULLABLE | 联系人姓名 |
| contact_email | String(128) | NULLABLE | 联系人邮箱 |
| contact_phone | String(20) | NULLABLE | 联系人电话 |
| expired_at | DateTime | NULLABLE | 过期时间 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

**索引：** `ix_tenants_code`、`ix_tenants_status`

---

#### TenantConfig（业务资源配置）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| tenant_id | UUID | FK → tenants.id, NOT NULL | 租户ID |
| max_users | Integer | NOT NULL, DEFAULT 100 | 最大用户数 |
| max_storage_mb | Integer | NOT NULL, DEFAULT 1024 | 最大存储空间（MB） |
| max_api_calls | Integer | NOT NULL, DEFAULT 10000 | 最大API调用次数 |
| created_at | DateTime | NOT NULL | 创建时间 |
| updated_at | DateTime | NOT NULL | 更新时间 |

**索引：** `ix_tenant_configs_tenant_id`
