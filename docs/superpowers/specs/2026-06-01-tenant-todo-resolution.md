# Tenant 模块 TODO 解决方案

**日期**: 2026-06-01
**状态**: 待实现

## 概述

解决 Tenant 模块中 8 处 TODO 标记，将直接 `import UserService` 的调用方式改为使用 `IamClient`，实现模块间解耦。

## 工作范围

| 类型 | 数量 | 说明 |
|------|------|------|
| A 类 | 2 处 | 新增 IAM inner 接口 |
| B 类 | 6 处 | 使用 IamClient 替代直接 import |
| 排除 | 2 处 | 统计功能暂不实现 |

## 第一节：IAM inner 接口新增

### 1.1 新增接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/inner/v1/users/{user_id}/tenants` | GET | 获取用户租户列表（含 role、is_default） |
| `/inner/v1/tenants/{tenant_id}/users` | GET | 获取租户下的用户 ID 列表 |

### 1.2 响应模型

```python
# 用户-租户关联信息
class UserTenantInfo(BaseModel):
    tenant_id: str = Field(..., description="租户ID")
    role: str = Field(..., description="角色")
    is_default: bool = Field(..., description="是否默认租户")

# 用户租户列表响应
class UserTenantsResponse(BaseModel):
    user_id: str = Field(..., description="用户ID")
    tenants: list[UserTenantInfo] = Field(default_factory=list)

# 租户用户列表响应
class TenantUsersResponse(BaseModel):
    tenant_id: str = Field(..., description="租户ID")
    user_ids: list[str] = Field(default_factory=list)
```

### 1.3 实现位置

- 文件：`server/python/src/iam/controllers/inner/user_controller.py`
- 复用 `UserService.get_user_tenant_ids()` 和 `UserService.get_user_ids_by_tenant_id()`
- 新增 `UserService.get_user_tenants_detail()` 方法获取完整信息

## 第二节：IamClient 扩展

### 2.1 新增方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_user_tenants()` | `user_id: str` | `list[UserTenantInfo]` | 获取用户租户列表 |
| `get_tenant_user_ids()` | `tenant_id: str` | `list[str]` | 获取租户用户 ID 列表 |

### 2.2 实现模式

遵循现有双模式设计：
- **单体模式**：直接查询 `UserTenant` 表
- **微服务模式**：调用 IAM inner 接口

### 2.3 实现位置

- 文件：`server/python/src/framework/clients/iam_client.py`

## 第三节：Tenant 模块调用改造

### 3.1 改造文件清单

| 文件 | 改动点 | 说明 |
|------|--------|------|
| `tenant/services/tenant_provider_impl.py` | 2 处 | `validate_access`、`get_user_tenants` |
| `tenant/controllers/inner/tenant_controller.py` | 1 处 | `validate_tenant_access` |
| `tenant/controllers/console/tenant_controller.py` | 3 处 | `list_user_tenants`、`switch_tenant` |
| `tenant/controllers/admin/tenant_controller.py` | 2 处 | `delete_tenant`、`get_tenant_stats` |

### 3.2 改造示例

**改造前：**
```python
# TODO: 通过 inner 接口调用 IAM 模块
from iam.services.user_service import UserService

tenant_ids = await UserService.get_user_tenant_ids(user_id)
```

**改造后：**
```python
from framework.clients.iam_client import get_iam_client

iam_client = get_iam_client()
user_tenants = await iam_client.get_user_tenants(user_id)
tenant_ids = [ut.tenant_id for ut in user_tenants]
```

### 3.3 console/tenant_controller.py 特殊处理

该文件需要获取 `role` 和 `is_default` 字段：

**改造前：**
```python
role="member",  # TODO: 从 UserTenant 获取实际角色
is_default=False,  # TODO: 从 UserTenant 获取
```

**改造后：**
```python
role=ut.role,
is_default=ut.is_default,
```

## 排除项

| TODO | 文件 | 说明 |
|------|------|------|
| 存储用量统计 | `admin/tenant_controller.py:461` | 暂不实现 |
| 活跃用户统计 | `admin/tenant_controller.py:462` | 暂不实现 |

## 影响范围

- IAM 模块：新增 2 个 inner 接口、1 个 Service 方法
- Framework：扩展 IamClient 2 个方法
- Tenant 模块：改造 4 个文件、解决 8 处 TODO

## 验收标准

1. 所有 8 处 TODO 已移除，替换为 IamClient 调用
2. 新增的 IAM inner 接口可正常访问
3. IamClient 单体模式测试通过
4. 现有测试不受影响
