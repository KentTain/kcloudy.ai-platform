# Tenant 模块 TODO 解决方案 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 解决 Tenant 模块中 8 处 TODO，将直接 import UserService 改为使用 IamClient，实现模块间解耦。

**架构：** 新增 2 个 IAM inner 接口供模块间调用，扩展 IamClient 提供统一调用入口，改造 Tenant 模块 4 个文件使用 IamClient。

**技术栈：** Python 3.12+ / FastAPI / Pydantic / SQLAlchemy 2.0

---

## 文件结构

### 新增文件
无

### 修改文件
| 文件 | 职责 |
|------|------|
| `server/python/src/iam/services/user_service.py` | 新增 `get_user_tenants_detail()` 方法 |
| `server/python/src/iam/controllers/inner/user_controller.py` | 新增 2 个 inner 接口 |
| `server/python/src/framework/clients/iam_client.py` | 新增 2 个方法 |
| `server/python/src/tenant/services/tenant_provider_impl.py` | 改用 IamClient（2 处） |
| `server/python/src/tenant/controllers/inner/tenant_controller.py` | 改用 IamClient（1 处） |
| `server/python/src/tenant/controllers/console/tenant_controller.py` | 改用 IamClient（3 处） |
| `server/python/src/tenant/controllers/admin/tenant_controller.py` | 改用 IamClient（2 处） |

### 测试文件
| 文件 | 职责 |
|------|------|
| `server/python/tests/iam/unit/services/test_user_service_tenants.py` | 新增方法的单元测试 |
| `server/python/tests/framework/unit/test_iam_client.py` | IamClient 新增方法测试 |

---

## 任务 1：UserService 新增 get_user_tenants_detail 方法

**文件：**
- 修改：`server/python/src/iam/services/user_service.py`
- 测试：`server/python/tests/iam/unit/services/test_user_service_tenants.py`

- [ ] **步骤 1：编写失败的测试**

创建测试文件 `server/python/tests/iam/unit/services/test_user_service_tenants.py`：

```python
"""
UserService 租户相关方法测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from iam.services.user_service import UserService


class TestGetUserTenantsDetail:
    """get_user_tenants_detail 方法测试"""

    @pytest.mark.asyncio
    async def test_returns_list_of_user_tenant_info(self):
        """返回用户租户详细信息列表"""
        # 模拟 UserTenant 查询结果
        mock_user_tenant_1 = MagicMock()
        mock_user_tenant_1.tenant_id = "tenant-1"
        mock_user_tenant_1.role = "admin"
        mock_user_tenant_1.is_default = True

        mock_user_tenant_2 = MagicMock()
        mock_user_tenant_2.tenant_id = "tenant-2"
        mock_user_tenant_2.role = "member"
        mock_user_tenant_2.is_default = False

        with patch("iam.services.user_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [
                mock_user_tenant_1,
                mock_user_tenant_2,
            ]
            mock_session_context.execute.return_value = mock_result

            result = await UserService.get_user_tenants_detail("user-1")

        assert len(result) == 2
        assert result[0]["tenant_id"] == "tenant-1"
        assert result[0]["role"] == "admin"
        assert result[0]["is_default"] is True
        assert result[1]["tenant_id"] == "tenant-2"
        assert result[1]["role"] == "member"
        assert result[1]["is_default"] is False

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_tenants(self):
        """用户无租户时返回空列表"""
        with patch("iam.services.user_service.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session_context.execute.return_value = mock_result

            result = await UserService.get_user_tenants_detail("user-no-tenants")

        assert result == []
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/iam/unit/services/test_user_service_tenants.py -v`
预期：FAIL，报错 `AttributeError: type object 'UserService' has no attribute 'get_user_tenants_detail'`

- [ ] **步骤 3：编写实现代码**

在 `server/python/src/iam/services/user_service.py` 的 `UserService` 类中添加方法（在 `get_user_ids_by_tenant_id` 方法之后）：

```python
    @staticmethod
    async def get_user_tenants_detail(user_id: str) -> list[dict]:
        """
        获取用户所属租户详细信息列表

        Args:
            user_id: 用户 ID

        Returns:
            list[dict]: 包含 tenant_id、role、is_default 的字典列表
        """
        async with async_session() as session:
            stmt = select(UserTenant).where(UserTenant.user_id == user_id)
            result = await session.execute(stmt)
            user_tenants = result.scalars().all()

            return [
                {
                    "tenant_id": ut.tenant_id,
                    "role": ut.role,
                    "is_default": ut.is_default,
                }
                for ut in user_tenants
            ]
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/iam/unit/services/test_user_service_tenants.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/iam/services/user_service.py server/python/tests/iam/unit/services/test_user_service_tenants.py
git commit -m "feat(iam): add get_user_tenants_detail method to UserService"
```

---

## 任务 2：IAM inner 接口新增用户租户列表接口

**文件：**
- 修改：`server/python/src/iam/controllers/inner/user_controller.py`

- [ ] **步骤 1：编写响应模型和接口**

在 `server/python/src/iam/controllers/inner/user_controller.py` 中：

1. 在现有响应模型之后（约第 66 行后）添加新模型：

```python
class UserTenantInfo(BaseModel):
    """用户-租户关联信息"""
    tenant_id: str = Field(..., description="租户ID")
    role: str = Field(..., description="角色")
    is_default: bool = Field(..., description="是否默认租户")


class UserTenantsResponse(BaseModel):
    """用户租户列表响应"""
    user_id: str = Field(..., description="用户ID")
    tenants: list[UserTenantInfo] = Field(default_factory=list, description="租户列表")


class TenantUsersResponse(BaseModel):
    """租户用户列表响应"""
    tenant_id: str = Field(..., description="租户ID")
    user_ids: list[str] = Field(default_factory=list, description="用户ID列表")
```

2. 在文件末尾添加新接口（在 `get_user_departments` 之后）：

```python
@router.get("/users/{user_id}/tenants")
async def get_user_tenants(user_id: str) -> ORJSONResponse:
    """
    获取用户租户列表

    场景：获取用户租户列表
    WHEN 请求 GET /inner/v1/users/{user_id}/tenants
    THEN 返回用户所属的租户列表，包含 role 和 is_default
    """
    tenants = await UserService.get_user_tenants_detail(user_id)

    return ORJSONResponse(
        content=Success(
            UserTenantsResponse(
                user_id=user_id,
                tenants=[
                    UserTenantInfo(
                        tenant_id=t["tenant_id"],
                        role=t["role"],
                        is_default=t["is_default"],
                    )
                    for t in tenants
                ],
            ).model_dump()
        )
    )


@router.get("/tenants/{tenant_id}/users")
async def get_tenant_users(tenant_id: str) -> ORJSONResponse:
    """
    获取租户下的用户 ID 列表

    场景：获取租户用户列表
    WHEN 请求 GET /inner/v1/tenants/{tenant_id}/users
    THEN 返回该租户下所有用户的 ID 列表
    """
    user_ids = await UserService.get_user_ids_by_tenant_id(tenant_id)

    return ORJSONResponse(
        content=Success(
            TenantUsersResponse(
                tenant_id=tenant_id,
                user_ids=user_ids,
            ).model_dump()
        )
    )
```

- [ ] **步骤 2：验证接口可访问**

运行服务：`cd server/python && uv run python manage.py runserver --module iam`
访问：`http://localhost:8000/docs`，确认接口出现在文档中

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/iam/controllers/inner/user_controller.py
git commit -m "feat(iam): add inner APIs for user tenants and tenant users"
```

---

## 任务 3：IamClient 新增 get_user_tenants 方法

**文件：**
- 修改：`server/python/src/framework/clients/iam_client.py`
- 测试：`server/python/tests/framework/unit/test_iam_client.py`

- [ ] **步骤 1：编写失败的测试**

创建测试文件 `server/python/tests/framework/unit/test_iam_client.py`：

```python
"""
IamClient 单元测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from framework.clients.iam_client import IamClient, UserTenantInfo


class TestIamClientGetUserTenants:
    """get_user_tenants 方法测试"""

    @pytest.mark.asyncio
    async def test_monolith_mode_returns_user_tenants(self):
        """单体模式返回用户租户列表"""
        client = IamClient(inner_url=None)  # 单体模式

        mock_user_tenant_1 = MagicMock()
        mock_user_tenant_1.tenant_id = "tenant-1"
        mock_user_tenant_1.role = "admin"
        mock_user_tenant_1.is_default = True

        mock_user_tenant_2 = MagicMock()
        mock_user_tenant_2.tenant_id = "tenant-2"
        mock_user_tenant_2.role = "member"
        mock_user_tenant_2.is_default = False

        with patch("framework.clients.iam_client.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [
                mock_user_tenant_1,
                mock_user_tenant_2,
            ]
            mock_session_context.execute.return_value = mock_result

            result = await client.get_user_tenants("user-1")

        assert len(result) == 2
        assert result[0].tenant_id == "tenant-1"
        assert result[0].role == "admin"
        assert result[0].is_default is True
        assert result[1].tenant_id == "tenant-2"
        assert result[1].role == "member"
        assert result[1].is_default is False

    @pytest.mark.asyncio
    async def test_monolith_mode_returns_empty_list(self):
        """单体模式用户无租户时返回空列表"""
        client = IamClient(inner_url=None)

        with patch("framework.clients.iam_client.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_session_context.execute.return_value = mock_result

            result = await client.get_user_tenants("user-no-tenants")

        assert result == []


class TestIamClientGetTenantUserIds:
    """get_tenant_user_ids 方法测试"""

    @pytest.mark.asyncio
    async def test_monolith_mode_returns_user_ids(self):
        """单体模式返回租户用户 ID 列表"""
        client = IamClient(inner_url=None)

        with patch("framework.clients.iam_client.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.all.return_value = [("user-1",), ("user-2",)]
            mock_session_context.execute.return_value = mock_result

            result = await client.get_tenant_user_ids("tenant-1")

        assert result == ["user-1", "user-2"]

    @pytest.mark.asyncio
    async def test_monolith_mode_returns_empty_list(self):
        """单体模式租户无用户时返回空列表"""
        client = IamClient(inner_url=None)

        with patch("framework.clients.iam_client.async_session") as mock_session:
            mock_session_context = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_session_context

            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_session_context.execute.return_value = mock_result

            result = await client.get_tenant_user_ids("tenant-no-users")

        assert result == []
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/framework/unit/test_iam_client.py -v`
预期：FAIL，报错 `AttributeError: 'IamClient' object has no attribute 'get_user_tenants'`

- [ ] **步骤 3：编写实现代码**

在 `server/python/src/framework/clients/iam_client.py` 中：

1. 在现有模型 `DepartmentInfo` 之后添加新模型：

```python
class UserTenantInfo(BaseModel):
    """用户-租户关联信息"""
    tenant_id: str = Field(..., description="租户ID")
    role: str = Field(..., description="角色")
    is_default: bool = Field(..., description="是否默认租户")
```

2. 在 `IamClient` 类中，在 `health_check` 方法之前添加两个新方法：

```python
    async def get_user_tenants(self, user_id: str) -> list[UserTenantInfo]:
        """
        获取用户租户列表

        Args:
            user_id: 用户 ID

        Returns:
            list[UserTenantInfo]
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/inner/v1/users/{user_id}/tenants",
            )
            if data and isinstance(data, dict) and "tenants" in data:
                return [UserTenantInfo.model_validate(t) for t in data["tenants"]]
            return []
        else:
            # 单体模式
            from iam.models import UserTenant
            from framework.database.core.engine import async_session
            from sqlalchemy import select

            async with async_session() as session:
                stmt = select(UserTenant).where(UserTenant.user_id == user_id)
                result = await session.execute(stmt)
                user_tenants = result.scalars().all()

                return [
                    UserTenantInfo(
                        tenant_id=ut.tenant_id,
                        role=ut.role,
                        is_default=ut.is_default,
                    )
                    for ut in user_tenants
                ]

    async def get_tenant_user_ids(self, tenant_id: str) -> list[str]:
        """
        获取租户下的用户 ID 列表

        Args:
            tenant_id: 租户 ID

        Returns:
            list[str]
        """
        if self._http_client:
            # 微服务模式
            data = await self._http_client.get(
                f"/inner/v1/tenants/{tenant_id}/users",
            )
            if data and isinstance(data, dict) and "user_ids" in data:
                return data["user_ids"]
            return []
        else:
            # 单体模式
            from iam.models import UserTenant
            from framework.database.core.engine import async_session
            from sqlalchemy import select

            async with async_session() as session:
                stmt = select(UserTenant.user_id).where(
                    UserTenant.tenant_id == tenant_id
                )
                result = await session.execute(stmt)
                return [row[0] for row in result.all()]
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/framework/unit/test_iam_client.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/framework/clients/iam_client.py server/python/tests/framework/unit/test_iam_client.py
git commit -m "feat(framework): add get_user_tenants and get_tenant_user_ids to IamClient"
```

---

## 任务 4：改造 tenant_provider_impl.py

**文件：**
- 修改：`server/python/src/tenant/services/tenant_provider_impl.py`

- [ ] **步骤 1：修改 validate_access 方法**

找到 `validate_access` 方法（约第 42-64 行），将：

```python
    async def validate_access(self, user_id: str, tenant_id: str) -> bool:
        """
        验证用户是否有权访问租户

        注意：此方法需要访问 IAM 模块的 UserTenant 表。
        在内部接口实现后，将通过 inner 接口调用。

        Args:
            user_id: 用户 ID
            tenant_id: 租户 ID

        Returns:
            bool
        """
        # 验证用户是否有权访问租户
        # TODO: 通过 inner 接口调用 IAM 模块
        from iam.services.user_service import UserService

        tenant_ids = await UserService.get_user_tenant_ids(user_id)
        if not tenant_ids:
            return False

        return tenant_id in tenant_ids
```

改为：

```python
    async def validate_access(self, user_id: str, tenant_id: str) -> bool:
        """
        验证用户是否有权访问租户

        Args:
            user_id: 用户 ID
            tenant_id: 租户 ID

        Returns:
            bool
        """
        from framework.clients.iam_client import get_iam_client

        iam_client = get_iam_client()
        user_tenants = await iam_client.get_user_tenants(user_id)
        if not user_tenants:
            return False

        tenant_ids = [ut.tenant_id for ut in user_tenants]
        return tenant_id in tenant_ids
```

- [ ] **步骤 2：修改 get_user_tenants 方法**

找到 `get_user_tenants` 方法（约第 66-89 行），将：

```python
    async def get_user_tenants(self, user_id: str) -> list[TenantInfo]:
        """
        获取用户所属的租户列表

        注意：此方法需要访问 IAM 模块的 UserTenant 表。
        在内部接口实现后，将通过 inner 接口调用。

        Args:
            user_id: 用户 ID

        Returns:
            list[TenantInfo]
        """
        # 获取用户所属的租户列表
        # TODO: 通过 inner 接口调用 IAM 模块
        from iam.services.user_service import UserService

        tenant_ids = await UserService.get_user_tenant_ids(user_id)
        if not tenant_ids:
            return []

        # 批量获取租户信息
        tenants = await TenantService.get_tenants_batch(tenant_ids)
        return [self._build_tenant_info(t) for t in tenants]
```

改为：

```python
    async def get_user_tenants(self, user_id: str) -> list[TenantInfo]:
        """
        获取用户所属的租户列表

        Args:
            user_id: 用户 ID

        Returns:
            list[TenantInfo]
        """
        from framework.clients.iam_client import get_iam_client

        iam_client = get_iam_client()
        user_tenants = await iam_client.get_user_tenants(user_id)
        if not user_tenants:
            return []

        # 批量获取租户信息
        tenant_ids = [ut.tenant_id for ut in user_tenants]
        tenants = await TenantService.get_tenants_batch(tenant_ids)
        return [self._build_tenant_info(t) for t in tenants]
```

- [ ] **步骤 3：验证修改正确**

运行：`cd server/python && uv run python -c "from tenant.services.tenant_provider_impl import TenantProviderImpl; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/tenant/services/tenant_provider_impl.py
git commit -m "refactor(tenant): use IamClient in TenantProviderImpl"
```

---

## 任务 5：改造 inner/tenant_controller.py

**文件：**
- 修改：`server/python/src/tenant/controllers/inner/tenant_controller.py`

- [ ] **步骤 1：修改 validate_tenant_access 函数**

找到 `validate_tenant_access` 函数（约第 176-230 行），将第 212-220 行：

```python
    # 检查用户是否属于该租户
    # TODO: 通过 inner 接口调用 IAM 模块
    from iam.services.user_service import UserService

    tenant_ids = await UserService.get_user_tenant_ids(user_id)
    if not tenant_ids:
        valid = False

    valid = tenant_id in tenant_ids
```

改为：

```python
    # 检查用户是否属于该租户
    from framework.clients.iam_client import get_iam_client

    iam_client = get_iam_client()
    user_tenants = await iam_client.get_user_tenants(user_id)
    tenant_ids = [ut.tenant_id for ut in user_tenants]
    valid = tenant_id in tenant_ids
```

- [ ] **步骤 2：验证修改正确**

运行：`cd server/python && uv run python -c "from tenant.controllers.inner.tenant_controller import router; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/tenant/controllers/inner/tenant_controller.py
git commit -m "refactor(tenant): use IamClient in inner tenant controller"
```

---

## 任务 6：改造 console/tenant_controller.py

**文件：**
- 修改：`server/python/src/tenant/controllers/console/tenant_controller.py`

- [ ] **步骤 1：修改 list_user_tenants 函数**

找到 `list_user_tenants` 函数（约第 21-59 行），将：

```python
@router.get("")
async def list_user_tenants(user_id: str = "test_user") -> ORJSONResponse:
    """
    获取用户可用租户列表

    场景：获取用户可用租户列表
    WHEN 用户请求 GET /console/v1/tenants
    THEN 返回用户所属的所有租户列表

    场景：用户不属于任何租户
    WHEN 用户不属于任何租户时请求 GET /console/v1/tenants
    THEN 返回空列表
    """

    # 获取用户可用租户列表
    # TODO: 通过 inner 接口调用 IAM 模块
    from iam.services.user_service import UserService

    tenant_ids = await UserService.get_user_tenant_ids(user_id)
    if not tenant_ids:
        return ORJSONResponse(content=Success([]))

    # 批量获取租户信息
    tenants = await TenantService.get_tenants_batch(tenant_ids)

    items = []
    for tenant in tenants:
        items.append(
            UserTenantVo(
                id=tenant.id,
                name=tenant.name,
                code=tenant.code,
                status=tenant.status,
                role="member",  # TODO: 从 UserTenant 获取实际角色
                is_default=False,  # TODO: 从 UserTenant 获取
            )
        )

    return ORJSONResponse(content=Success(items))
```

改为：

```python
@router.get("")
async def list_user_tenants(user_id: str = "test_user") -> ORJSONResponse:
    """
    获取用户可用租户列表

    场景：获取用户可用租户列表
    WHEN 用户请求 GET /console/v1/tenants
    THEN 返回用户所属的所有租户列表

    场景：用户不属于任何租户
    WHEN 用户不属于任何租户时请求 GET /console/v1/tenants
    THEN 返回空列表
    """
    from framework.clients.iam_client import get_iam_client

    iam_client = get_iam_client()
    user_tenants = await iam_client.get_user_tenants(user_id)
    if not user_tenants:
        return ORJSONResponse(content=Success([]))

    # 构建租户 ID 到用户租户信息的映射
    user_tenant_map = {ut.tenant_id: ut for ut in user_tenants}

    # 批量获取租户信息
    tenant_ids = list(user_tenant_map.keys())
    tenants = await TenantService.get_tenants_batch(tenant_ids)

    items = []
    for tenant in tenants:
        ut = user_tenant_map.get(tenant.id)
        items.append(
            UserTenantVo(
                id=tenant.id,
                name=tenant.name,
                code=tenant.code,
                status=tenant.status,
                role=ut.role if ut else "member",
                is_default=ut.is_default if ut else False,
            )
        )

    return ORJSONResponse(content=Success(items))
```

- [ ] **步骤 2：修改 switch_tenant 函数**

找到 `switch_tenant` 函数（约第 95-148 行），将第 129-135 行：

```python
    # 验证用户访问权限
    # TODO: 通过 inner 接口调用 IAM 模块
    from iam.services.user_service import UserService

    user_tenant_ids = await UserService.get_user_tenant_ids(user_id)
    if tenant_id not in user_tenant_ids:
        raise HTTPException(status_code=403, detail="无权访问该租户")
```

改为：

```python
    # 验证用户访问权限
    from framework.clients.iam_client import get_iam_client

    iam_client = get_iam_client()
    user_tenants = await iam_client.get_user_tenants(user_id)
    tenant_ids = [ut.tenant_id for ut in user_tenants]
    if tenant_id not in tenant_ids:
        raise HTTPException(status_code=403, detail="无权访问该租户")
```

- [ ] **步骤 3：验证修改正确**

运行：`cd server/python && uv run python -c "from tenant.controllers.console.tenant_controller import router; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/tenant/controllers/console/tenant_controller.py
git commit -m "refactor(tenant): use IamClient in console tenant controller"
```

---

## 任务 7：改造 admin/tenant_controller.py

**文件：**
- 修改：`server/python/src/tenant/controllers/admin/tenant_controller.py`

- [ ] **步骤 1：修改 delete_tenant 函数**

找到 `delete_tenant` 函数（约第 386-414 行），将第 402-408 行：

```python
    # 检查租户下是否有用户
    # TODO: 通过 inner 接口调用 IAM 模块
    from iam.services.user_service import UserService

    user_ids = await UserService.get_user_ids_by_tenant_id(tenant_id)
    if len(user_ids) > 0:
        raise HTTPException(status_code=400, detail="租户下存在用户，无法删除")
```

改为：

```python
    # 检查租户下是否有用户
    from framework.clients.iam_client import get_iam_client

    iam_client = get_iam_client()
    user_ids = await iam_client.get_tenant_user_ids(tenant_id)
    if len(user_ids) > 0:
        raise HTTPException(status_code=400, detail="租户下存在用户，无法删除")
```

- [ ] **步骤 2：修改 get_tenant_stats 函数**

找到 `get_tenant_stats` 函数（约第 455-485 行），将第 471-476 行：

```python
    # 统计用户数
    # TODO: 通过 inner 接口调用 IAM 模块
    from iam.services.user_service import UserService

    user_ids = await UserService.get_user_ids_by_tenant_id(tenant_id)
    user_count = len(user_ids)
```

改为：

```python
    # 统计用户数
    from framework.clients.iam_client import get_iam_client

    iam_client = get_iam_client()
    user_ids = await iam_client.get_tenant_user_ids(tenant_id)
    user_count = len(user_ids)
```

- [ ] **步骤 3：验证修改正确**

运行：`cd server/python && uv run python -c "from tenant.controllers.admin.tenant_controller import router; print('OK')"`
预期：输出 `OK`

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/tenant/controllers/admin/tenant_controller.py
git commit -m "refactor(tenant): use IamClient in admin tenant controller"
```

---

## 任务 8：验证并完成

- [ ] **步骤 1：验证所有 TODO 已解决**

运行：`cd server/python && grep -r "TODO.*inner.*IAM" src/tenant/`
预期：无输出（所有 TODO 已解决）

- [ ] **步骤 2：验证现有测试通过**

运行：`cd server/python && uv run pytest tests/framework/unit/test_iam_client.py tests/iam/unit/services/test_user_service_tenants.py -v`
预期：全部 PASS

- [ ] **步骤 3：最终 Commit**

```bash
git add -A
git commit -m "feat: resolve Tenant module TODOs using IamClient for cross-module calls"
```

---

## 验收清单

- [ ] 所有 8 处 TODO 已移除
- [ ] 新增 2 个 IAM inner 接口可访问
- [ ] IamClient 新增 2 个方法测试通过
- [ ] UserService 新增方法测试通过
- [ ] 现有测试不受影响
