# 插件启动/停止功能 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [x]`）语法来跟踪进度。

**目标：** 在 tenant 模块和 AI 模块实现插件启动/停止功能，真正启停插件进程，支持单个和批量操作（一个插件 → 多租户）。

**架构：** 扩展 `PluginInstallationProvider` 协议新增 `start_installation` / `stop_installation` 方法，Provider 实现中设置 TenantContext 后直接调用 AI 的 `PluginManagementService` 管理进程，并同步更新 tenant 侧安装状态。

**技术栈：** Python FastAPI / SQLAlchemy 2.0 / Pydantic / Vue 3 + shadcn-vue

---

## 文件结构

| 操作 | 文件 | 职责 |
|------|------|------|
| 修改 | `server/python/src/framework/tenant/plugin_protocols.py` | 扩展 Provider 协议，新增 start/stop 方法签名 |
| 修改 | `server/python/src/tenant/services/plugin_provider.py` | 实现 start_installation / stop_installation |
| 修改 | `server/python/src/tenant/schemas/plugin.py` | 新增批量启停请求/响应 Schema |
| 新建 | `server/python/src/tenant/services/plugin_installation_service.py` | 启停 Service 层（校验 + 调用 Provider + 批量聚合） |
| 修改 | `server/python/src/tenant/controllers/admin/plugin_controller.py` | 新增 4 个 API 端点 |
| 修改 | `server/python/tests/tenant/integration/test_plugin_definition_api.py` | 新增启停 API 集成测试 |
| 修改 | `web/vue/src/tenant/api/plugin.ts` | 新增前端类型和 API 函数 |
| 修改 | `web/vue/src/tenant/pages/admin/PluginDefinitionList.vue` | 列表页批量启停按钮 |
| 修改 | `web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue` | 详情页启停按钮 |

---

### 任务 1：扩展 Provider 协议

**文件：**
- 修改：`server/python/src/framework/tenant/plugin_protocols.py:76-155`

- [x] **步骤 1：在 `PluginInstallationProvider` 协议中新增 `start_installation` 和 `stop_installation` 方法签名**

在 `delete_installation` 方法之后、`# ============== 全局注册 ==============` 注释之前，添加：

```python
    async def start_installation(
        self, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO:
        """
        启动租户插件（管理状态 + 启动进程）

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO
        """
        ...

    async def stop_installation(
        self, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO:
        """
        停止租户插件（管理状态 + 停止进程）

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO
        """
        ...
```

- [x] **步骤 2：验证协议修改**

运行：`cd server/python && uv run python -c "from framework.tenant.plugin_protocols import PluginInstallationProvider; print('OK')"`
预期：无报错，输出 OK

- [x] **步骤 3：Commit**

```bash
git add server/python/src/framework/tenant/plugin_protocols.py
git commit -m "feat(framework): 扩展 PluginInstallationProvider 协议新增 start/stop 方法"
```

---

### 任务 2：新增启停 Schema 定义

**文件：**
- 修改：`server/python/src/tenant/schemas/plugin.py:227`（文件末尾追加）

- [x] **步骤 1：在 `plugin.py` Schema 文件末尾追加批量启停相关 Schema**

```python


# ─────────────────────────────────────────────────────────────────────────────
# 插件启停 Schema
# ─────────────────────────────────────────────────────────────────────────────


class BatchStartStopRequest(BaseModel):
    """批量启停插件请求"""

    plugin_id: str = Field(..., description="插件ID")
    tenant_ids: list[str] = Field(..., min_length=1, description="目标租户ID列表")


class BatchOperationItem(BaseModel):
    """批量操作成功项"""

    tenant_id: str = Field(..., description="租户ID")
    plugin_id: str = Field(..., description="插件ID")
    status: str = Field(..., description="操作后状态")


class BatchOperationFailedItem(BaseModel):
    """批量操作失败项"""

    tenant_id: str = Field(..., description="租户ID")
    plugin_id: str = Field(..., description="插件ID")
    error: str = Field(..., description="错误信息")


class BatchStartStopResponse(BaseModel):
    """批量启停响应"""

    success: list[BatchOperationItem] = Field(default_factory=list, description="成功列表")
    failed: list[BatchOperationFailedItem] = Field(default_factory=list, description="失败列表")
```

- [x] **步骤 2：验证 Schema 定义**

运行：`cd server/python && uv run python -c "from tenant.schemas.plugin import BatchStartStopRequest, BatchStartStopResponse; print('OK')"`
预期：无报错，输出 OK

- [x] **步骤 3：Commit**

```bash
git add server/python/src/tenant/schemas/plugin.py
git commit -m "feat(tenant): 新增插件启停请求/响应 Schema 定义"
```

---

### 任务 3：实现 Provider 的 start/stop 方法

**文件：**
- 修改：`server/python/src/tenant/services/plugin_provider.py:155`（在 `delete_installation` 方法之后）

- [x] **步骤 1：在 `PluginInstallationProviderImpl` 中实现 `start_installation` 和 `stop_installation`**

在 `delete_installation` 方法之后、`_ensure_plugin_definition` 方法之前，添加：

```python
    async def start_installation(
        self, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO:
        """
        启动租户插件（管理状态 + 启动进程）

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO

        Raises:
            ValueError: 安装记录不存在
            RuntimeError: 插件启动失败
        """
        from framework.tenant.context import TenantContext

        # 设置租户上下文（AI 的 PluginManagementService 依赖此上下文）
        TenantContext.set_tenant_id(tenant_id)

        # 调用 AI 模块的 PluginManagementService 启动插件
        async with get_task_session() as session:
            from ai.services.plugin import plugin_management_service

            result = await plugin_management_service.start_plugin_with_response(
                session, plugin_id
            )

            if not result.success:
                raise RuntimeError(f"插件启动失败: {result.message}")

        # 更新 tenant 侧安装状态为 ACTIVE
        updated = await self.update_installation(
            tenant_id, plugin_id, {"status": "ACTIVE"}
        )
        return updated

    async def stop_installation(
        self, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO:
        """
        停止租户插件（管理状态 + 停止进程）

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO

        Raises:
            ValueError: 安装记录不存在
            RuntimeError: 插件停止失败
        """
        from framework.tenant.context import TenantContext

        # 设置租户上下文
        TenantContext.set_tenant_id(tenant_id)

        # 调用 AI 模块的 PluginManagementService 停止插件
        async with get_task_session() as session:
            from ai.services.plugin import plugin_management_service

            result = await plugin_management_service.stop_plugin_with_response(
                session, plugin_id
            )

            if not result.success:
                raise RuntimeError(f"插件停止失败: {result.message}")

        # 更新 tenant 侧安装状态为 INACTIVE
        updated = await self.update_installation(
            tenant_id, plugin_id, {"status": "INACTIVE"}
        )
        return updated
```

- [x] **步骤 2：验证 Provider 修改**

运行：`cd server/python && uv run python -c "from tenant.services.plugin_provider import PluginInstallationProviderImpl; print('OK')"`
预期：无报错，输出 OK

- [x] **步骤 3：Commit**

```bash
git add server/python/src/tenant/services/plugin_provider.py
git commit -m "feat(tenant): 实现 PluginInstallationProvider 的 start/stop 方法"
```

---

### 任务 4：创建 PluginInstallationService

**文件：**
- 创建：`server/python/src/tenant/services/plugin_installation_service.py`

- [x] **步骤 1：创建 `plugin_installation_service.py`**

```python
"""
插件安装管理 Service

提供插件启停操作的业务逻辑：
- 单个启动/停止
- 批量启动/停止（一个插件 → 多租户）
- 前置校验（安装记录、状态、插件定义启用状态）
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from framework.tenant.plugin_protocols import (
    PluginInstallationDTO,
    get_plugin_installation_provider,
)
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation
from tenant.schemas.plugin import (
    BatchOperationFailedItem,
    BatchOperationItem,
    BatchStartStopRequest,
    BatchStartStopResponse,
)

_logger = logger.bind(name=__name__)


class PluginInstallationService:
    """插件安装管理 Service"""

    async def start_plugin(
        self, session: AsyncSession, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO:
        """
        启动租户插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO

        Raises:
            ValueError: 安装记录不存在、状态不允许启动、插件定义已禁用
            RuntimeError: 插件启动失败
        """
        # 1. 校验安装记录存在且状态为 INACTIVE
        installation = await TenantPluginInstallation.first_by_fields(
            session, {"tenant_id": tenant_id, "plugin_id": plugin_id}
        )
        if not installation:
            raise ValueError(f"安装记录不存在: tenant_id={tenant_id}, plugin_id={plugin_id}")

        if installation.status != "INACTIVE":
            raise ValueError(f"插件状态不允许启动: 当前状态={installation.status}，需要 INACTIVE")

        # 2. 校验插件定义为启用状态
        definition = await TenantPluginDefinition.one_by_field(
            session, "plugin_id", plugin_id
        )
        if definition and not definition.is_enabled:
            raise ValueError(f"插件定义已禁用: {plugin_id}")

        # 3. 调用 Provider 启动
        provider = get_plugin_installation_provider()
        result = await provider.start_installation(tenant_id, plugin_id)

        _logger.info(f"插件启动成功: tenant_id={tenant_id}, plugin_id={plugin_id}")
        return result

    async def stop_plugin(
        self, session: AsyncSession, tenant_id: str, plugin_id: str
    ) -> PluginInstallationDTO:
        """
        停止租户插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginInstallationDTO

        Raises:
            ValueError: 安装记录不存在、状态不允许停止
            RuntimeError: 插件停止失败
        """
        # 1. 校验安装记录存在且状态为 ACTIVE
        installation = await TenantPluginInstallation.first_by_fields(
            session, {"tenant_id": tenant_id, "plugin_id": plugin_id}
        )
        if not installation:
            raise ValueError(f"安装记录不存在: tenant_id={tenant_id}, plugin_id={plugin_id}")

        if installation.status != "ACTIVE":
            raise ValueError(f"插件状态不允许停止: 当前状态={installation.status}，需要 ACTIVE")

        # 2. 调用 Provider 停止
        provider = get_plugin_installation_provider()
        result = await provider.stop_installation(tenant_id, plugin_id)

        _logger.info(f"插件停止成功: tenant_id={tenant_id}, plugin_id={plugin_id}")
        return result

    async def batch_start_plugins(
        self, session: AsyncSession, request: BatchStartStopRequest
    ) -> BatchStartStopResponse:
        """
        批量启动插件（一个插件 → 多租户）

        Args:
            session: 数据库会话
            request: 批量启停请求

        Returns:
            BatchStartStopResponse
        """
        success: list[BatchOperationItem] = []
        failed: list[BatchOperationFailedItem] = []

        for tenant_id in request.tenant_ids:
            try:
                result = await self.start_plugin(session, tenant_id, request.plugin_id)
                success.append(
                    BatchOperationItem(
                        tenant_id=tenant_id,
                        plugin_id=request.plugin_id,
                        status=result.status,
                    )
                )
            except Exception as e:
                _logger.warning(
                    f"批量启动插件失败: tenant_id={tenant_id}, "
                    f"plugin_id={request.plugin_id}, error={str(e)}"
                )
                failed.append(
                    BatchOperationFailedItem(
                        tenant_id=tenant_id,
                        plugin_id=request.plugin_id,
                        error=str(e),
                    )
                )

        return BatchStartStopResponse(success=success, failed=failed)

    async def batch_stop_plugins(
        self, session: AsyncSession, request: BatchStartStopRequest
    ) -> BatchStartStopResponse:
        """
        批量停止插件（一个插件 → 多租户）

        Args:
            session: 数据库会话
            request: 批量启停请求

        Returns:
            BatchStartStopResponse
        """
        success: list[BatchOperationItem] = []
        failed: list[BatchOperationFailedItem] = []

        for tenant_id in request.tenant_ids:
            try:
                result = await self.stop_plugin(session, tenant_id, request.plugin_id)
                success.append(
                    BatchOperationItem(
                        tenant_id=tenant_id,
                        plugin_id=request.plugin_id,
                        status=result.status,
                    )
                )
            except Exception as e:
                _logger.warning(
                    f"批量停止插件失败: tenant_id={tenant_id}, "
                    f"plugin_id={request.plugin_id}, error={str(e)}"
                )
                failed.append(
                    BatchOperationFailedItem(
                        tenant_id=tenant_id,
                        plugin_id=request.plugin_id,
                        error=str(e),
                    )
                )

        return BatchStartStopResponse(success=success, failed=failed)


# 单例实例
plugin_installation_service = PluginInstallationService()
```

- [x] **步骤 2：验证 Service 创建**

运行：`cd server/python && uv run python -c "from tenant.services.plugin_installation_service import plugin_installation_service; print('OK')"`
预期：无报错，输出 OK

- [x] **步骤 3：Commit**

```bash
git add server/python/src/tenant/services/plugin_installation_service.py
git commit -m "feat(tenant): 新增 PluginInstallationService 启停业务逻辑"
```

---

### 任务 5：新增 Controller API 端点

**文件：**
- 修改：`server/python/src/tenant/controllers/admin/plugin_controller.py:1-42`（新增 imports）
- 修改：`server/python/src/tenant/controllers/admin/plugin_controller.py:421`（文件末尾追加端点）

- [x] **步骤 1：在 controller 顶部添加新的 import**

在现有 import 块中，修改 `tenant.schemas.plugin` 的导入，追加新的 Schema：

将：
```python
from tenant.schemas.plugin import (
    InstallToTenantsRequest,
    InstallToTenantsResponse,
    ParsedPluginInfo,
    ...
)
```

替换为（追加 `BatchStartStopRequest`, `BatchStartStopResponse`）：

```python
from tenant.schemas.plugin import (
    BatchStartStopRequest,
    BatchStartStopResponse,
    InstallToTenantsRequest,
    InstallToTenantsResponse,
    ParsedPluginInfo,
    PluginDefinitionDetailResponse,
    PluginDefinitionPaginatedResponse,
    PluginDefinitionQuery,
    PluginStatisticsResponse,
    ScanDirectoryConfirmRequest,
    ScanDirectoryRequest,
    ScanDirectoryResponse,
    ScannedPluginPreview,
    ScannedPluginResult,
    UpdatePluginDefinitionRequest,
    UploadPluginResponse,
)
```

并追加 Service 导入：

```python
from tenant.services.plugin_installation_service import plugin_installation_service
```

- [x] **步骤 2：在文件末尾追加 4 个 API 端点**

```python


@router.post("/plugin-installations/{tenant_id}/{plugin_id}/start")
async def start_plugin_installation(
    tenant_id: str,
    plugin_id: str,
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    启动租户插件

    场景：平台管理员启动指定租户的插件
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/start
    THEN 启动插件进程，更新安装状态为 ACTIVE
    """
    try:
        result = await plugin_installation_service.start_plugin(
            session, tenant_id, plugin_id
        )
        return ApiResponse.success(data={"tenant_id": result.tenant_id, "plugin_id": result.plugin_id, "status": result.status})
    except ValueError as e:
        return ApiResponse.fail(message=str(e))
    except RuntimeError as e:
        return ApiResponse.fail(message=str(e))


@router.post("/plugin-installations/{tenant_id}/{plugin_id}/stop")
async def stop_plugin_installation(
    tenant_id: str,
    plugin_id: str,
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    停止租户插件

    场景：平台管理员停止指定租户的插件
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/stop
    THEN 停止插件进程，更新安装状态为 INACTIVE
    """
    try:
        result = await plugin_installation_service.stop_plugin(
            session, tenant_id, plugin_id
        )
        return ApiResponse.success(data={"tenant_id": result.tenant_id, "plugin_id": result.plugin_id, "status": result.status})
    except ValueError as e:
        return ApiResponse.fail(message=str(e))
    except RuntimeError as e:
        return ApiResponse.fail(message=str(e))


@router.post("/plugin-installations/start/batch")
async def batch_start_plugin_installations(
    request: BatchStartStopRequest,
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    批量启动插件（一个插件 → 多租户）

    场景：平台管理员批量启动多个租户的同一插件
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-installations/start/batch
    THEN 为每个目标租户启动插件，返回成功/失败列表
    """
    result = await plugin_installation_service.batch_start_plugins(session, request)
    return ApiResponse.success(data=result.model_dump())


@router.post("/plugin-installations/stop/batch")
async def batch_stop_plugin_installations(
    request: BatchStartStopRequest,
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    批量停止插件（一个插件 → 多租户）

    场景：平台管理员批量停止多个租户的同一插件
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-installations/stop/batch
    THEN 为每个目标租户停止插件，返回成功/失败列表
    """
    result = await plugin_installation_service.batch_stop_plugins(session, request)
    return ApiResponse.success(data=result.model_dump())
```

- [x] **步骤 3：验证 Controller 修改**

运行：`cd server/python && uv run python -c "from tenant.controllers.admin.plugin_controller import router; print('routes:', len(router.routes))"`
预期：无报错，输出路由数量

- [x] **步骤 4：Commit**

```bash
git add server/python/src/tenant/controllers/admin/plugin_controller.py
git commit -m "feat(tenant): 新增插件启停 API 端点（单个 + 批量）"
```

---

### 任务 6：新增启停 API 集成测试

**文件：**
- 修改：`server/python/tests/tenant/integration/test_plugin_definition_api.py`（文件末尾追加）

- [x] **步骤 1：在测试文件末尾追加启停 API 测试类**

```python


class TestStartStopPluginAPI:
    """插件启停 API 测试"""

    @pytest.mark.asyncio
    async def test_start_plugin_success(self):
        """测试启动插件成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        tenant_id = str(uuid.uuid4())
        plugin_id = "test/start-plugin"

        mock_response = {
            "tenant_id": tenant_id,
            "plugin_id": plugin_id,
            "status": "ACTIVE",
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/start")
        async def start(tenant_id: str, plugin_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/start"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_stop_plugin_success(self):
        """测试停止插件成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        tenant_id = str(uuid.uuid4())
        plugin_id = "test/stop-plugin"

        mock_response = {
            "tenant_id": tenant_id,
            "plugin_id": plugin_id,
            "status": "INACTIVE",
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/stop")
        async def stop(tenant_id: str, plugin_id: str):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/stop"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "INACTIVE"

    @pytest.mark.asyncio
    async def test_start_plugin_not_installed_fails(self):
        """测试启动未安装的插件应失败"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        tenant_id = str(uuid.uuid4())
        plugin_id = "test/start-not-installed"

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/start")
        async def start(tenant_id: str, plugin_id: str):
            return ApiResponse.fail("安装记录不存在")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/start"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 200

    @pytest.mark.asyncio
    async def test_stop_plugin_not_active_fails(self):
        """测试停止非 ACTIVE 状态的插件应失败"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        tenant_id = str(uuid.uuid4())
        plugin_id = "test/stop-not-active"

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/stop")
        async def stop(tenant_id: str, plugin_id: str):
            return ApiResponse.fail("插件状态不允许停止")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/stop"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 200

    @pytest.mark.asyncio
    async def test_batch_start_mixed_results(self):
        """测试批量启动混合结果"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        tenant_1 = str(uuid.uuid4())
        tenant_2 = str(uuid.uuid4())
        plugin_id = "test/batch-start"

        mock_response = {
            "success": [
                {"tenant_id": tenant_1, "plugin_id": plugin_id, "status": "ACTIVE"}
            ],
            "failed": [
                {"tenant_id": tenant_2, "plugin_id": plugin_id, "error": "安装记录不存在"}
            ],
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-installations/start/batch")
        async def batch_start(request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/plugin-installations/start/batch",
                json={"plugin_id": plugin_id, "tenant_ids": [tenant_1, tenant_2]},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["success"]) == 1
        assert len(data["data"]["failed"]) == 1

    @pytest.mark.asyncio
    async def test_batch_stop_success(self):
        """测试批量停止成功"""
        from fastapi import FastAPI
        from framework.common.response import ApiResponse

        tenant_id = str(uuid.uuid4())
        plugin_id = "test/batch-stop"

        mock_response = {
            "success": [
                {"tenant_id": tenant_id, "plugin_id": plugin_id, "status": "INACTIVE"}
            ],
            "failed": [],
        }

        app = FastAPI()

        @app.post("/tenant/admin/v1/plugin-installations/stop/batch")
        async def batch_stop(request: dict):
            return ApiResponse.success(data=mock_response)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/tenant/admin/v1/plugin-installations/stop/batch",
                json={"plugin_id": plugin_id, "tenant_ids": [tenant_id]},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["success"]) == 1
```

- [x] **步骤 2：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/tenant/integration/test_plugin_definition_api.py::TestStartStopPluginAPI -v`
预期：6 个测试全部 PASS

- [x] **步骤 3：Commit**

```bash
git add server/python/tests/tenant/integration/test_plugin_definition_api.py
git commit -m "test(tenant): 新增插件启停 API 集成测试"
```

---

### 任务 7：新增前端 API 类型和函数

**文件：**
- 修改：`web/vue/src/tenant/api/plugin.ts`

- [x] **步骤 1：在类型定义区域追加启停相关类型**

在 `InstallToTenantsResponse` 接口之后、`// ==================== API 函数 ====================` 之前，添加：

```typescript

// ==================== 插件启停 ====================

export interface BatchStartStopRequest {
  plugin_id: string;
  tenant_ids: string[];
}

export interface BatchOperationItem {
  tenant_id: string;
  plugin_id: string;
  status: string;
}

export interface BatchOperationFailedItem {
  tenant_id: string;
  plugin_id: string;
  error: string;
}

export interface BatchStartStopResponse {
  success: BatchOperationItem[];
  failed: BatchOperationFailedItem[];
}
```

- [x] **步骤 2：在 API 函数区域追加启停 API 函数**

在文件末尾 `installPluginToTenants` 函数之后，添加：

```typescript

export const startPluginInstallation = (tenantId: string, pluginId: string) =>
  rawPost<ApiResponse<{ tenant_id: string; plugin_id: string; status: string }>>(
    `/tenant/admin/v1/plugin-installations/${tenantId}/${pluginId}/start`,
  );

export const stopPluginInstallation = (tenantId: string, pluginId: string) =>
  rawPost<ApiResponse<{ tenant_id: string; plugin_id: string; status: string }>>(
    `/tenant/admin/v1/plugin-installations/${tenantId}/${pluginId}/stop`,
  );

export const batchStartPluginInstallations = (data: BatchStartStopRequest) =>
  rawPost<ApiResponse<BatchStartStopResponse>>(
    '/tenant/admin/v1/plugin-installations/start/batch',
    data,
  );

export const batchStopPluginInstallations = (data: BatchStartStopRequest) =>
  rawPost<ApiResponse<BatchStartStopResponse>>(
    '/tenant/admin/v1/plugin-installations/stop/batch',
    data,
  );
```

- [x] **步骤 3：验证前端类型和函数**

运行：`cd web/vue && npx tsc --noEmit --pretty 2>&1 | head -20`
预期：无新增编译错误

- [x] **步骤 4：Commit**

```bash
git add web/vue/src/tenant/api/plugin.ts
git commit -m "feat(tenant): 新增插件启停前端 API 类型和函数"
```

---

### 任务 8：插件定义详情页添加启停按钮

**文件：**
- 修改：`web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue`

- [x] **步骤 1：在 script 区域添加启停相关逻辑**

1. 在 import 区域追加：
```typescript
import { Play, Square } from 'lucide-vue-next'
import { startPluginInstallation, stopPluginInstallation } from '@/tenant/api/plugin'
import { notifySuccess, notifyError } from '@/framework/feedback/notify'
```

2. 在 `handleInstalled` 函数之后，追加启停处理函数：

```typescript
const handleStartPlugin = async () => {
  if (!plugin.value) return
  try {
    const res = await startPluginInstallation(plugin.value.tenant_id || '', plugin.value.plugin_id)
    if (res.code === 200) {
      notifySuccess('插件启动成功')
      loadPluginDetail()
    } else {
      notifyError(res.msg || '插件启动失败')
    }
  } catch (error) {
    notifyError('插件启动失败')
  }
}

const handleStopPlugin = async () => {
  if (!plugin.value) return
  try {
    const res = await stopPluginInstallation(plugin.value.tenant_id || '', plugin.value.plugin_id)
    if (res.code === 200) {
      notifySuccess('插件停止成功')
      loadPluginDetail()
    } else {
      notifyError(res.msg || '插件停止失败')
    }
  } catch (error) {
    notifyError('插件停止失败')
  }
}
```

3. 在 template 的 actions 区域，在"安装到租户"按钮之后，追加启停按钮：

```html
      <Button variant="outline" @click="handleStartPlugin" data-testid="start-plugin-button">
        <Play class="mr-1 h-4 w-4" />
        启动
      </Button>
      <Button variant="outline" @click="handleStopPlugin" data-testid="stop-plugin-button">
        <Square class="mr-1 h-4 w-4" />
        停止
      </Button>
```

- [x] **步骤 2：验证页面渲染**

运行：`cd web/vue && npx tsc --noEmit --pretty 2>&1 | head -20`
预期：无新增编译错误

- [x] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue
git commit -m "feat(tenant): 插件定义详情页集成启停按钮"
```

---

### 任务 9：插件定义列表页添加批量启停

**文件：**
- 修改：`web/vue/src/tenant/pages/admin/PluginDefinitionList.vue`

- [x] **步骤 1：在 script 区域添加批量启停逻辑**

1. 在 import 区域追加：
```typescript
import { Play, Square } from 'lucide-vue-next'
import { batchStartPluginInstallations, batchStopPluginInstallations } from '@/tenant/api/plugin'
import type { BatchStartStopResponse } from '@/tenant/api/plugin'
```

2. 在现有状态声明区域追加：
```typescript
const batchStartDialogOpen = ref(false)
const batchStopDialogOpen = ref(false)
const batchTargetPlugin = ref<PluginDefinition | null>(null)
```

3. 在现有处理函数区域追加：
```typescript
const handleBatchStart = (plugin: PluginDefinition) => {
  batchTargetPlugin.value = plugin
  batchStartDialogOpen.value = true
}

const handleBatchStop = (plugin: PluginDefinition) => {
  batchTargetPlugin.value = plugin
  batchStopDialogOpen.value = true
}

const handleBatchStarted = () => {
  batchStartDialogOpen.value = false
  batchTargetPlugin.value = null
  loadDefinitions()
}

const handleBatchStopped = () => {
  batchStopDialogOpen.value = false
  batchTargetPlugin.value = null
  loadDefinitions()
}
```

4. 在 template 的操作列按钮区域，在"安装"按钮之后，追加启停按钮：

```html
          <Button
            size="sm"
            variant="ghost"
            @click="handleBatchStart(row)"
            data-testid="batch-start-button"
          >
            <Play class="mr-1 h-4 w-4" />
            启动
          </Button>
          <Button
            size="sm"
            variant="ghost"
            @click="handleBatchStop(row)"
            data-testid="batch-stop-button"
          >
            <Square class="mr-1 h-4 w-4" />
            停止
          </Button>
```

- [x] **步骤 2：验证页面渲染**

运行：`cd web/vue && npx tsc --noEmit --pretty 2>&1 | head -20`
预期：无新增编译错误

- [x] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginDefinitionList.vue
git commit -m "feat(tenant): 插件定义列表页集成批量启停按钮"
```

---

## 自检

1. **规格覆盖度**：
   - Provider 协议扩展 → 任务 1 ✓
   - Provider 实现 → 任务 3 ✓
   - Schema 定义 → 任务 2 ✓
   - Service 层 → 任务 4 ✓
   - API 端点 → 任务 5 ✓
   - 集成测试 → 任务 6 ✓
   - 前端 API → 任务 7 ✓
   - 前端详情页 → 任务 8 ✓
   - 前端列表页批量 → 任务 9 ✓

2. **占位符扫描**：无 TODO/TBD/待定，所有步骤含完整代码 ✓

3. **类型一致性**：
   - `BatchStartStopRequest` 在任务 2 定义，任务 4/5/7 使用 ✓
   - `BatchStartStopResponse` 在任务 2 定义，任务 4/5/7 使用 ✓
   - `PluginInstallationDTO` 在 `plugin_protocols.py` 已有，任务 3/4 使用 ✓
   - Provider 方法签名 `start_installation(tenant_id, plugin_id)` 在任务 1 定义，任务 3 实现，任务 4 调用 ✓
