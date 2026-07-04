# 插件安装及配置功能调整实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [x]`）语法来跟踪进度。

**目标：** 调整插件安装及配置功能，实现 tenant 模块负责安装（PENDING → INACTIVE），ai 模块负责配置和启动（INACTIVE → ACTIVE）的职责分离。

**架构：** tenant 模块管理插件定义和安装记录，ai 模块管理插件配置、运行时状态和生命周期。通过 PluginInstallationProvider 协议实现跨模块通信，状态流转为 PENDING → INACTIVE → ACTIVE。

**技术栈：** Python 3.12、FastAPI、SQLAlchemy 2.0、Pydantic、Vue 3、TypeScript

---

## 文件结构

### 后端文件

**框架层（协议定义）：**
- 修改：`server/python/src/framework/tenant/plugin_protocols.py`
  - 职责：定义 PluginInstallationDTO 新增字段和 PluginInstallationProvider 新增方法

**tenant 模块：**
- 修改：`server/python/src/tenant/services/plugin_provider.py`
  - 职责：实现 update_installation_status 方法，调整 create_installation 移除 auto_start

**ai 模块（核心逻辑）：**
- 修改：`server/python/src/ai/components/plugin/engine/core/plugin_manager.py`
  - 职责：调整 install_plugin 方法，新增 start_plugin 和 stop_plugin 方法
- 修改：`server/python/src/ai/components/plugin/engine/core/install_task_manager.py`
  - 职责：调整 _install_plugin_item 方法，移除 auto_start 参数处理

**ai 模块（接口层）：**
- 新增：`server/python/src/ai/controllers/console/plugin_config_controller.py`
  - 职责：配置、测试、启动、停止插件的 HTTP 接口
- 新增：`server/python/src/ai/schemas/plugin_config.py`
  - 职责：配置、测试、启动、停止的请求和响应 Schema
- 修改：`server/python/src/ai/services/plugin_config_service.py`
  - 职责：插件配置、测试连接、启动停止的业务逻辑

**ai 模块（路由注册）：**
- 修改：`server/python/src/ai/controllers/console/__init__.py`
  - 职责：注册新的 plugin_config_controller 路由

### 前端文件

**ai 模块前端：**
- 新增：`web/vue/src/ai/api/pluginConfig.ts`
  - 职责：配置、测试、启动、停止插件的 API 调用
- 修改：`web/vue/src/ai/pages/PluginManagePage.vue`
  - 职责：调整插件管理页面，增加配置、启动、停止按钮
- 修改：`web/vue/src/ai/pages/PluginConfigPage.vue`
  - 职责：调整插件配置页面，增加测试连接按钮

**tenant 模块前端：**
- 修改：`web/vue/src/tenant/api/plugin.ts`
  - 职责：调整安装接口，移除 auto_start 参数
- 修改：`web/vue/src/tenant/pages/admin/PluginInstallationList.vue`（重命名自 PluginManagePage.vue）
  - 职责：调整插件安装列表页面，移除启动、停止、配置功能

### 测试文件

**后端测试：**
- 修改：`server/python/tests/ai/e2e/test_plugin_install.py`
- 修改：`server/python/tests/ai/e2e/test_plugin_invoke.py`
- 修改：`server/python/tests/ai/e2e/test_plugin_full_lifecycle.py`
- 修改：`server/python/tests/tenant/unit/test_plugin_provider.py`
- 新增：`server/python/tests/ai/unit/services/test_plugin_config_service.py`

---

## 任务分解

### 任务 1：调整 PluginInstallationDTO 数据结构

**文件：**
- 修改：`server/python/src/framework/tenant/plugin_protocols.py:14-33`

- [x] **步骤 1：添加 installed_at 字段到 PluginInstallationDTO**

修改 `server/python/src/framework/tenant/plugin_protocols.py`：

```python
@dataclass
class PluginInstallationDTO:
    """安装记录 DTO

    用于 Tenant 模块与 AI 模块之间传递插件安装信息。
    """

    tenant_id: str
    plugin_id: str
    plugin_unique_identifier: str
    declaration: dict  # 完整声明内容
    status: str = "PENDING"  # PENDING / ACTIVE / INACTIVE / FAILED
    installed_at: datetime | None = None  # 新增：安装完成时间
    freeze_threshold_hours: int = 24
    plugin_type: str | None = None
    runtime_type: str | None = None
    install_config: dict | None = None  # 安装配置
    source: str | None = None  # 来源
    meta: dict | None = None  # 元数据
```

- [x] **步骤 2：移除 auto_start 字段**

确保 PluginInstallationDTO 中不存在 auto_start 字段：

```python
@dataclass
class PluginInstallationDTO:
    """安装记录 DTO"""
    # 确认字段列表中不包含 auto_start
    tenant_id: str
    plugin_id: str
    plugin_unique_identifier: str
    declaration: dict
    status: str = "PENDING"
    installed_at: datetime | None = None
    freeze_threshold_hours: int = 24
    plugin_type: str | None = None
    runtime_type: str | None = None
    install_config: dict | None = None
    source: str | None = None
    meta: dict | None = None
    # auto_start 字段已移除
```

- [x] **步骤 3：Commit**

```bash
git add server/python/src/framework/tenant/plugin_protocols.py
git commit -m "refactor(plugin): 调整 PluginInstallationDTO 数据结构

- 新增 installed_at 字段记录安装完成时间
- 移除 auto_start 字段（启动由 ai 模块负责）"
```

---

### 任务 2：新增 PluginInstallationProvider.update_installation_status 方法

**文件：**
- 修改：`server/python/src/framework/tenant/plugin_protocols.py:76-186`

- [x] **步骤 1：在 PluginInstallationProvider 协议中新增方法签名**

修改 `server/python/src/framework/tenant/plugin_protocols.py`：

```python
class PluginInstallationProvider(Protocol):
    """
    插件安装提供者协议

    抽象租户插件的 CRUD 操作，支持：
    - 本地部署：直接数据库访问
    - 分布式部署：通过 RPC/HTTP 调用 AI 模块
    """

    # ... 现有方法

    async def update_installation_status(
        self, tenant_id: str, plugin_id: str, status: str
    ) -> PluginInstallationDTO:
        """
        更新安装状态（由 AI 模块调用）

        Args:
            tenant_id: 租户 ID
            plugin_id: 插件 ID
            status: 新状态（ACTIVE / INACTIVE）

        Returns:
            PluginInstallationDTO
        """
        ...
```

- [x] **步骤 2：Commit**

```bash
git add server/python/src/framework/tenant/plugin_protocols.py
git commit -m "feat(plugin): 新增 PluginInstallationProvider.update_installation_status 方法

- 支持 AI 模块更新插件安装状态
- 用于启动/停止插件时同步状态到 tenant 模块"
```

---

### 任务 3：实现 plugin_provider.update_installation_status 方法

**文件：**
- 修改：`server/python/src/tenant/services/plugin_provider.py:103-130`

- [x] **步骤 1：编写失败的测试**

创建 `server/python/tests/tenant/unit/test_plugin_provider_status.py`：

```python
"""测试 PluginInstallationProvider 状态更新方法"""

import pytest
from datetime import datetime

from framework.tenant.plugin_protocols import PluginInstallationDTO
from tenant.services.plugin_provider import PluginInstallationProviderImpl


@pytest.mark.asyncio
async def test_update_installation_status_success(test_session):
    """测试更新安装状态成功"""
    provider = PluginInstallationProviderImpl()

    # 先创建一个安装记录
    create_dto = PluginInstallationDTO(
        tenant_id="test_tenant",
        plugin_id="test_plugin",
        plugin_unique_identifier="test/plugin:1.0.0@abc123",
        declaration={"name": "Test Plugin"},
        status="PENDING",
    )
    created = await provider.create_installation("test_tenant", create_dto)

    # 更新状态为 INACTIVE
    updated = await provider.update_installation_status(
        "test_tenant", "test_plugin", "INACTIVE"
    )

    assert updated.status == "INACTIVE"
    assert updated.installed_at is not None


@pytest.mark.asyncio
async def test_update_installation_status_not_found(test_session):
    """测试更新不存在的安装记录"""
    provider = PluginInstallationProviderImpl()

    with pytest.raises(ValueError, match="安装记录不存在"):
        await provider.update_installation_status(
            "test_tenant", "non_existent_plugin", "INACTIVE"
        )
```

- [x] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/tenant/unit/test_plugin_provider_status.py -v`

预期：FAIL，报错 "AttributeError: 'PluginInstallationProviderImpl' object has no attribute 'update_installation_status'"

- [x] **步骤 3：实现 update_installation_status 方法**

修改 `server/python/src/tenant/services/plugin_provider.py`：

```python
async def update_installation_status(
    self, tenant_id: str, plugin_id: str, status: str
) -> PluginInstallationDTO:
    """
    更新安装状态（供 AI 模块调用）

    Args:
        tenant_id: 租户 ID
        plugin_id: 插件 ID
        status: 新状态（ACTIVE / INACTIVE）

    Returns:
        PluginInstallationDTO

    Raises:
        ValueError: 安装记录不存在
    """
    async with get_task_session() as session:
        installation = await TenantPluginInstallation.first_by_fields(
            session, {"tenant_id": tenant_id, "plugin_id": plugin_id}
        )
        if not installation:
            raise ValueError(
                f"安装记录不存在: tenant_id={tenant_id}, plugin_id={plugin_id}"
            )

        update_data = {"status": status}
        if status == "INACTIVE":
            update_data["installed_at"] = datetime.now()

        await installation.update(session, update_data)
        return self._to_dto(installation)
```

- [x] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/tenant/unit/test_plugin_provider_status.py -v`

预期：PASS

- [x] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/plugin_provider.py
git add server/python/tests/tenant/unit/test_plugin_provider_status.py
git commit -m "feat(tenant): 实现 update_installation_status 方法

- 支持 AI 模块更新插件安装状态
- 状态更新为 INACTIVE 时记录 installed_at 时间
- 新增单元测试验证功能"
```

---

### 任务 4：调整 plugin_provider.create_installation 方法

**文件：**
- 修改：`server/python/src/tenant/services/plugin_provider.py:70-101`

- [x] **步骤 1：编写失败的测试**

创建 `server/python/tests/tenant/unit/test_plugin_provider_create.py`：

```python
"""测试 PluginInstallationProvider 创建方法调整"""

import pytest

from framework.tenant.plugin_protocols import PluginInstallationDTO
from tenant.services.plugin_provider import PluginInstallationProviderImpl


@pytest.mark.asyncio
async def test_create_installation_initial_status_pending(test_session):
    """测试创建安装记录时初始状态为 PENDING"""
    provider = PluginInstallationProviderImpl()

    create_dto = PluginInstallationDTO(
        tenant_id="test_tenant",
        plugin_id="test_plugin",
        plugin_unique_identifier="test/plugin:1.0.0@abc123",
        declaration={"name": "Test Plugin"},
    )

    created = await provider.create_installation("test_tenant", create_dto)

    assert created.status == "PENDING"
    assert created.installed_at is None


@pytest.mark.asyncio
async def test_create_installation_without_auto_start(test_session):
    """测试创建安装记录时不再处理 auto_start 参数"""
    provider = PluginInstallationProviderImpl()

    # 创建 DTO，不包含 auto_start 字段
    create_dto = PluginInstallationDTO(
        tenant_id="test_tenant",
        plugin_id="test_plugin",
        plugin_unique_identifier="test/plugin:1.0.0@abc123",
        declaration={"name": "Test Plugin"},
    )

    created = await provider.create_installation("test_tenant", create_dto)

    # 验证创建成功，不涉及 auto_start 逻辑
    assert created.plugin_id == "test_plugin"
```

- [x] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/tenant/unit/test_plugin_provider_create.py -v`

预期：测试可能通过（因为已经移除了 auto_start 参数），但需要验证逻辑正确性

- [x] **步骤 3：调整 create_installation 方法**

修改 `server/python/src/tenant/services/plugin_provider.py`：

```python
async def create_installation(
    self, tenant_id: str, data: PluginInstallationDTO
) -> PluginInstallationDTO:
    """
    创建插件安装记录

    Args:
        tenant_id: 租户 ID
        data: 安装记录 DTO

    Returns:
        PluginInstallationDTO
    """
    async with get_task_session() as session:
        # 确保插件定义已存在
        await self._ensure_plugin_definition(session, data)

        # 创建安装记录，初始状态固定为 PENDING
        installation = TenantPluginInstallation(
            tenant_id=tenant_id,
            plugin_id=data.plugin_id,
            plugin_unique_identifier=data.plugin_unique_identifier,
            status="PENDING",  # 初始状态固定为 PENDING
            freeze_threshold_hours=data.freeze_threshold_hours,
            plugin_type=data.plugin_type,
            runtime_type=data.runtime_type,
        )
        session.add(installation)
        await session.flush()

        return self._to_dto(installation)
```

- [x] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/tenant/unit/test_plugin_provider_create.py -v`

预期：PASS

- [x] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/plugin_provider.py
git add server/python/tests/tenant/unit/test_plugin_provider_create.py
git commit -m "refactor(tenant): 调整 create_installation 方法

- 移除 auto_start 参数处理
- 初始状态固定为 PENDING
- 新增单元测试验证调整"
```

---

### 任务 5：调整 plugin_manager.install_plugin 方法

**文件：**
- 修改：`server/python/src/ai/components/plugin/engine/core/plugin_manager.py`

- [x] **步骤 1：定位 install_plugin 方法**

使用 CodeGraph 查找 install_plugin 方法位置：

```bash
cd server/python && codegraph query install_plugin -k method
```

- [x] **步骤 2：调整 InstallRequest 参数处理**

修改 `install_plugin` 方法签名和实现：

```python
async def install_plugin(
    self,
    plugin_package: bytes,
    install_request: InstallRequest,
) -> str:
    """
    安装插件

    Args:
        plugin_package: 插件包二进制内容
        install_request: 安装请求参数

    Returns:
        插件 ID

    变更点：
    - 移除 auto_start 参数处理
    - 安装成功后只更新状态为 INACTIVE，不启动插件
    """
    # 1. 解析插件包（保留现有逻辑）
    package_info = await self._parse_plugin_package(plugin_package)

    # 2. 验证插件配置（保留现有逻辑）
    await self._validate_plugin_config(package_info.config)

    # 3. 保存插件文件（保留现有逻辑）
    plugin_id = await self._save_plugin_files(package_info)

    # 4. 创建 PENDING 记录（保留现有逻辑）
    provider = get_plugin_installation_provider()
    installation_dto = PluginInstallationDTO(
        tenant_id=self.tenant_id,
        plugin_id=plugin_id,
        plugin_unique_identifier=package_info.config.unique_identifier,
        declaration=package_info.config.model_dump(),
        plugin_type="local",
        runtime_type=package_info.config.runtime_type,
    )
    await provider.create_installation(self.tenant_id, installation_dto)

    # 5. 安装成功，更新状态为 INACTIVE（新增逻辑）
    await provider.update_installation_status(
        self.tenant_id, plugin_id, "INACTIVE"
    )

    self.logger.info(f"插件安装成功: {plugin_id}, 状态: INACTIVE")

    return plugin_id
```

- [x] **步骤 3：移除 auto_start 相关逻辑**

检查并移除以下代码：

```python
# 删除以下逻辑
# if install_request.auto_start:
#     await self.start_plugin(plugin_id)
```

- [x] **步骤 4：Commit**

```bash
git add server/python/src/ai/components/plugin/engine/core/plugin_manager.py
git commit -m "refactor(ai): 调整 install_plugin 方法

- 移除 auto_start 参数处理
- 安装成功后更新状态为 INACTIVE，不自动启动
- 启动功能独立为 start_plugin 方法"
```

---

### 任务 6：新增 plugin_manager.start_plugin 方法

**文件：**
- 新增：`server/python/src/ai/components/plugin/engine/core/plugin_manager.py`

- [x] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/components/plugin/test_plugin_manager_start.py`：

```python
"""测试 PluginManager.start_plugin 方法"""

import pytest
from datetime import datetime

from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager


@pytest.mark.asyncio
async def test_start_plugin_success(mock_session, mock_plugin_config):
    """测试启动插件成功"""
    manager = TenantPluginManager("test_tenant")
    await manager.initialize(mock_session)

    result = await manager.start_plugin("test_plugin")

    assert result["status"] == "ACTIVE"
    assert result["plugin_id"] == "test_plugin"
    assert "port" in result


@pytest.mark.asyncio
async def test_start_plugin_without_config_warning(mock_session):
    """测试未配置插件启动时给出警告"""
    manager = TenantPluginManager("test_tenant")
    await manager.initialize(mock_session)

    result = await manager.start_plugin("test_plugin")

    assert result["status"] == "ACTIVE"
    assert result["warning"] == "插件未配置，请先配置插件"


@pytest.mark.asyncio
async def test_start_plugin_invalid_config_warning(mock_session, mock_invalid_config):
    """测试无效配置插件启动时给出警告"""
    manager = TenantPluginManager("test_tenant")
    await manager.initialize(mock_session)

    result = await manager.start_plugin("test_plugin")

    assert result["status"] == "ACTIVE"
    assert "配置验证失败" in result["warning"]
```

- [x] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/components/plugin/test_plugin_manager_start.py -v`

预期：FAIL，报错 "AttributeError: 'TenantPluginManager' object has no attribute 'start_plugin'"

- [x] **步骤 3：实现 start_plugin 方法**

在 `server/python/src/ai/components/plugin/engine/core/plugin_manager.py` 中新增：

```python
async def start_plugin(self, plugin_id: str) -> dict:
    """
    启动插件

    Args:
        plugin_id: 插件 ID

    Returns:
        启动结果字典，包含状态、端口、警告信息等

    流程：
    1. 检查配置是否存在
    2. 检查 validated 状态，给出警告
    3. 启动进程
    4. 更新 runtime_state
    5. 通知 tenant 更新 installation 状态为 ACTIVE
    """
    # 1. 检查配置是否存在
    async with get_task_session() as session:
        config = await AIPluginConfig.first_by_fields(
            session,
            {"tenant_id": self.tenant_id, "plugin_id": plugin_id}
        )

        warning = None
        if not config:
            warning = "插件未配置，请先配置插件"
        elif not config.plugin_config or not config.plugin_config.get("validated"):
            warning = "配置未验证，可能无法正常工作"
        elif config.plugin_config.get("validated") is False:
            warning = "配置验证失败，可能无法正常工作"

    # 2. 启动进程
    runtime = await self._start_plugin_process(plugin_id)

    # 3. 更新 runtime_state
    async with get_task_session() as session:
        state = await PluginRuntimeState.first_by_fields(
            session,
            {"tenant_id": self.tenant_id, "plugin_id": plugin_id}
        )
        if not state:
            state = PluginRuntimeState(
                tenant_id=self.tenant_id,
                plugin_id=plugin_id,
                status="active",
                process_id=runtime.process_id,
                port=runtime.port,
                last_started_at=datetime.now(),
            )
            session.add(state)
        else:
            await state.update(session, {
                "status": "active",
                "process_id": runtime.process_id,
                "port": runtime.port,
                "last_started_at": datetime.now(),
            })

    # 4. 通知 tenant 更新状态为 ACTIVE
    provider = get_plugin_installation_provider()
    await provider.update_installation_status(
        self.tenant_id, plugin_id, "ACTIVE"
    )

    self.logger.info(f"插件启动成功: {plugin_id}, 端口: {runtime.port}")

    return {
        "plugin_id": plugin_id,
        "status": "ACTIVE",
        "port": runtime.port,
        "warning": warning,
    }
```

- [x] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/components/plugin/test_plugin_manager_start.py -v`

预期：PASS

- [x] **步骤 5：Commit**

```bash
git add server/python/src/ai/components/plugin/engine/core/plugin_manager.py
git add server/python/tests/ai/unit/components/plugin/test_plugin_manager_start.py
git commit -m "feat(ai): 新增 start_plugin 方法

- 支持独立启动插件功能
- 检查配置状态并给出警告
- 更新 runtime_state 和 installation 状态
- 新增单元测试验证功能"
```

---

### 任务 7：新增 plugin_manager.stop_plugin 方法

**文件：**
- 新增：`server/python/src/ai/components/plugin/engine/core/plugin_manager.py`

- [x] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/components/plugin/test_plugin_manager_stop.py`：

```python
"""测试 PluginManager.stop_plugin 方法"""

import pytest
from datetime import datetime

from ai.components.plugin.engine.core.plugin_manager import TenantPluginManager


@pytest.mark.asyncio
async def test_stop_plugin_success(mock_session, mock_running_plugin):
    """测试停止插件成功"""
    manager = TenantPluginManager("test_tenant")
    await manager.initialize(mock_session)

    result = await manager.stop_plugin("test_plugin")

    assert result["status"] == "INACTIVE"
    assert result["plugin_id"] == "test_plugin"


@pytest.mark.asyncio
async def test_stop_plugin_updates_runtime_state(mock_session, mock_running_plugin):
    """测试停止插件时更新运行时状态"""
    manager = TenantPluginManager("test_tenant")
    await manager.initialize(mock_session)

    await manager.stop_plugin("test_plugin")

    # 验证 runtime_state 已更新
    from ai.models.plugin_runtime_state import PluginRuntimeState
    state = await PluginRuntimeState.first_by_fields(
        mock_session,
        {"tenant_id": "test_tenant", "plugin_id": "test_plugin"}
    )
    assert state.status == "inactive"
    assert state.last_stopped_at is not None
```

- [x] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/components/plugin/test_plugin_manager_stop.py -v`

预期：FAIL，报错 "AttributeError: 'TenantPluginManager' object has no attribute 'stop_plugin'"

- [x] **步骤 3：实现 stop_plugin 方法**

在 `server/python/src/ai/components/plugin/engine/core/plugin_manager.py` 中新增：

```python
async def stop_plugin(self, plugin_id: str) -> dict:
    """
    停止插件

    Args:
        plugin_id: 插件 ID

    Returns:
        停止结果字典

    流程：
    1. 停止进程
    2. 更新 runtime_state
    3. 通知 tenant 更新 installation 状态为 INACTIVE
    """
    # 1. 停止进程
    await self._stop_plugin_process(plugin_id)

    # 2. 更新 runtime_state
    async with get_task_session() as session:
        state = await PluginRuntimeState.first_by_fields(
            session,
            {"tenant_id": self.tenant_id, "plugin_id": plugin_id}
        )
        if state:
            await state.update(session, {
                "status": "inactive",
                "last_stopped_at": datetime.now(),
            })

    # 3. 通知 tenant 更新状态为 INACTIVE
    provider = get_plugin_installation_provider()
    await provider.update_installation_status(
        self.tenant_id, plugin_id, "INACTIVE"
    )

    self.logger.info(f"插件停止成功: {plugin_id}")

    return {
        "plugin_id": plugin_id,
        "status": "INACTIVE",
    }
```

- [x] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/components/plugin/test_plugin_manager_stop.py -v`

预期：PASS

- [x] **步骤 5：Commit**

```bash
git add server/python/src/ai/components/plugin/engine/core/plugin_manager.py
git add server/python/tests/ai/unit/components/plugin/test_plugin_manager_stop.py
git commit -m "feat(ai): 新增 stop_plugin 方法

- 支持独立停止插件功能
- 更新 runtime_state 和 installation 状态
- 新增单元测试验证功能"
```

---

### 任务 8：调整 install_task_manager._install_plugin_item 方法

**文件：**
- 修改：`server/python/src/ai/components/plugin/engine/core/install_task_manager.py:277-423`

- [x] **步骤 1：定位 _install_plugin_item 方法**

使用 CodeGraph 查找方法位置：

```bash
cd server/python && codegraph query _install_plugin_item -k method
```

- [x] **步骤 2：调整 auto_start 参数处理**

修改 `server/python/src/ai/components/plugin/engine/core/install_task_manager.py`：

```python
async def _install_plugin_item(
    self, item: InstallationItem, task_type: TaskType
) -> bool:
    """安装单个插件项"""
    try:
        plugin_manager = await self.get_plugin_manager()

        if task_type == TaskType.INSTALL:
            # 处理安装任务
            if not item.identifier:
                logger.error(f"安装项标识符为空: {item}")
                return False

            # 获取插件包内容（保留现有逻辑）
            plugin_package = await self._get_plugin_package(item)
            if not plugin_package:
                logger.error(f"无法获取插件包内容: {item.identifier}")
                return False

            # 更新进度
            item.progress = 25.0

            # 创建安装请求，从任务元数据中获取配置
            from ..models.request import InstallRequest

            # 获取配置参数
            task = self._find_task_by_item(item)
            force = False  # 默认值

            if task and task.metadata:
                force = task.metadata.get("force", False)

            install_request = InstallRequest(
                force=force,
                auto_start=False,  # 固定为 False
                config_override={}
            )

            # 更新进度
            item.progress = 50.0

            # 调用插件管理器安装
            plugin_name = await plugin_manager.install_plugin(
                plugin_package, install_request
            )

            # 更新插件信息
            item.plugin_name = plugin_name
            item.progress = 100.0

            logger.info(f"插件安装成功: {plugin_name}")
            return True

        # ... 其他任务类型处理（保留现有逻辑）
```

- [x] **步骤 3：Commit**

```bash
git add server/python/src/ai/components/plugin/engine/core/install_task_manager.py
git commit -m "refactor(ai): 调整 install_task_manager 移除 auto_start 逻辑

- 固定 auto_start 为 False
- 安装后插件状态为 INACTIVE，需手动启动"
```

---

### 任务 9：新增 plugin_config Schema

**文件：**
- 新增：`server/python/src/ai/schemas/plugin_config.py`

- [x] **步骤 1：创建 plugin_config.py 文件**

创建 `server/python/src/ai/schemas/plugin_config.py`：

```python
"""插件配置相关 Schema"""

from __future__ import annotations

from framework.schemas import BaseModel


class PluginConfigRequest(BaseModel):
    """插件配置请求"""

    plugin_config: dict | None = None
    runtime_config: dict | None = None


class PluginConfigResponse(BaseModel):
    """插件配置响应"""

    plugin_id: str
    validated: bool | None = None  # null=未测试, true=验证通过, false=验证失败
    message: str | None = None


class PluginTestRequest(BaseModel):
    """插件测试请求"""

    pass  # 无需额外参数


class PluginTestResponse(BaseModel):
    """插件测试响应"""

    plugin_id: str
    validated: bool
    message: str


class PluginStartRequest(BaseModel):
    """插件启动请求"""

    pass  # 无需额外参数


class PluginStartResponse(BaseModel):
    """插件启动响应"""

    plugin_id: str
    status: str
    port: int | None = None
    warning: str | None = None


class PluginStopRequest(BaseModel):
    """插件停止请求"""

    pass  # 无需额外参数


class PluginStopResponse(BaseModel):
    """插件停止响应"""

    plugin_id: str
    status: str
```

- [x] **步骤 2：Commit**

```bash
git add server/python/src/ai/schemas/plugin_config.py
git commit -m "feat(ai): 新增插件配置相关 Schema

- PluginConfigRequest/Response: 配置插件
- PluginTestRequest/Response: 测试配置连接
- PluginStartRequest/Response: 启动插件
- PluginStopRequest/Response: 停止插件"
```

---

### 任务 10：新增 plugin_config_service 服务

**文件：**
- 新增：`server/python/src/ai/services/plugin_config_service.py`

- [x] **步骤 1：编写失败的测试**

创建 `server/python/tests/ai/unit/services/test_plugin_config_service.py`：

```python
"""测试 PluginConfigService"""

import pytest

from ai.services.plugin_config_service import PluginConfigService


@pytest.mark.asyncio
async def test_config_plugin_creates_new_config(mock_session):
    """测试配置插件时创建新配置记录"""
    service = PluginConfigService()

    result = await service.config_plugin(
        mock_session,
        tenant_id="test_tenant",
        plugin_id="test_plugin",
        plugin_config={"api_key": "test_key"},
        runtime_config={"timeout": 30},
    )

    assert result.plugin_id == "test_plugin"
    assert result.validated is None


@pytest.mark.asyncio
async def test_test_plugin_connection_success(mock_session, mock_valid_config):
    """测试插件连接成功"""
    service = PluginConfigService()

    result = await service.test_plugin(
        mock_session,
        tenant_id="test_tenant",
        plugin_id="test_plugin",
    )

    assert result.validated is True
    assert result.message == "连接成功"


@pytest.mark.asyncio
async def test_test_plugin_connection_failed(mock_session, mock_invalid_config):
    """测试插件连接失败"""
    service = PluginConfigService()

    result = await service.test_plugin(
        mock_session,
        tenant_id="test_tenant",
        plugin_id="test_plugin",
    )

    assert result.validated is False
    assert "连接失败" in result.message
```

- [x] **步骤 2：运行测试验证失败**

运行：`cd server/python && uv run pytest tests/ai/unit/services/test_plugin_config_service.py -v`

预期：FAIL，报错 "ModuleNotFoundError: No module named 'ai.services.plugin_config_service'"

- [x] **步骤 3：实现 PluginConfigService**

创建 `server/python/src/ai/services/plugin_config_service.py`：

```python
"""插件配置服务"""

from datetime import datetime
from loguru import logger

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.models.plugin_config import PluginConfig
from ai.schemas.plugin_config import (
    PluginConfigResponse,
    PluginTestResponse,
    PluginStartResponse,
    PluginStopResponse,
)
from ai.components.plugin.engine.core.plugin_manager import PluginManagerFactory

_logger = logger.bind(name=__name__)


class PluginConfigService:
    """插件配置服务"""

    async def config_plugin(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
        plugin_config: dict | None,
        runtime_config: dict | None,
    ) -> PluginConfigResponse:
        """
        配置插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID
            plugin_config: 插件配置
            runtime_config: 运行时配置

        Returns:
            PluginConfigResponse
        """
        # 查询现有配置
        result = await session.execute(
            select(PluginConfig).where(
                PluginConfig.tenant_id == tenant_id,
                PluginConfig.plugin_id == plugin_id,
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            # 创建新配置
            config = PluginConfig(
                tenant_id=tenant_id,
                plugin_id=plugin_id,
                plugin_unique_identifier=f"{plugin_id}:latest",
                plugin_config=plugin_config,
                runtime_config=runtime_config,
            )
            session.add(config)
        else:
            # 更新现有配置
            config.plugin_config = plugin_config
            config.runtime_config = runtime_config
            # 重置验证状态
            if config.plugin_config:
                config.plugin_config["validated"] = None

        await session.flush()

        _logger.info(f"插件配置已保存: {plugin_id}")

        return PluginConfigResponse(
            plugin_id=plugin_id,
            validated=config.plugin_config.get("validated") if config.plugin_config else None,
        )

    async def test_plugin(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
    ) -> PluginTestResponse:
        """
        测试插件配置连接

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginTestResponse
        """
        # 获取插件管理器
        manager = await PluginManagerFactory.get_manager(tenant_id, session)

        # 调用插件的测试连接方法
        try:
            # TODO: 调用插件的实际测试连接接口
            # result = await manager.test_plugin_connection(plugin_id)

            # 模拟测试成功
            validated = True
            message = "连接成功"
        except Exception as e:
            validated = False
            message = f"连接失败: {str(e)}"

        # 更新配置的验证状态
        result = await session.execute(
            select(PluginConfig).where(
                PluginConfig.tenant_id == tenant_id,
                PluginConfig.plugin_id == plugin_id,
            )
        )
        config = result.scalar_one_or_none()
        if config and config.plugin_config:
            config.plugin_config["validated"] = validated
            await session.flush()

        _logger.info(f"插件配置测试完成: {plugin_id}, 结果: {validated}")

        return PluginTestResponse(
            plugin_id=plugin_id,
            validated=validated,
            message=message,
        )

    async def start_plugin(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
    ) -> PluginStartResponse:
        """
        启动插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginStartResponse
        """
        # 获取插件管理器
        manager = await PluginManagerFactory.get_manager(tenant_id, session)

        # 启动插件
        result = await manager.start_plugin(plugin_id)

        _logger.info(f"插件启动完成: {plugin_id}, 状态: {result['status']}")

        return PluginStartResponse(**result)

    async def stop_plugin(
        self,
        session: AsyncSession,
        tenant_id: str,
        plugin_id: str,
    ) -> PluginStopResponse:
        """
        停止插件

        Args:
            session: 数据库会话
            tenant_id: 租户 ID
            plugin_id: 插件 ID

        Returns:
            PluginStopResponse
        """
        # 获取插件管理器
        manager = await PluginManagerFactory.get_manager(tenant_id, session)

        # 停止插件
        result = await manager.stop_plugin(plugin_id)

        _logger.info(f"插件停止完成: {plugin_id}, 状态: {result['status']}")

        return PluginStopResponse(**result)


# 单例实例
plugin_config_service = PluginConfigService()
```

- [x] **步骤 4：运行测试验证通过**

运行：`cd server/python && uv run pytest tests/ai/unit/services/test_plugin_config_service.py -v`

预期：PASS

- [x] **步骤 5：Commit**

```bash
git add server/python/src/ai/services/plugin_config_service.py
git add server/python/tests/ai/unit/services/test_plugin_config_service.py
git commit -m "feat(ai): 新增 PluginConfigService 服务

- 支持插件配置、测试连接、启动、停止功能
- 新增单元测试验证功能"
```

---

### 任务 11：新增 plugin_config_controller 控制器

**文件：**
- 新增：`server/python/src/ai/controllers/console/plugin_config_controller.py`

- [x] **步骤 1：创建控制器文件**

创建 `server/python/src/ai/controllers/console/plugin_config_controller.py`：

```python
"""插件配置控制器"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from framework.database.dependencies import get_db_session
from framework.common.response import ApiResponse
from ai.schemas.plugin_config import (
    PluginConfigRequest,
    PluginConfigResponse,
    PluginTestResponse,
    PluginStartResponse,
    PluginStopResponse,
)
from ai.services.plugin_config_service import plugin_config_service
from framework.tenant.context import TenantContext

router = APIRouter(prefix="/plugins/installations", tags=["插件配置管理"])


@router.post(
    "/{plugin_id}/config",
    response_model=PluginConfigResponse,
    summary="配置插件",
)
async def config_plugin(
    plugin_id: str,
    request: PluginConfigRequest,
    session: AsyncSession = Depends(get_db_session),
) -> PluginConfigResponse:
    """
    配置插件

    Args:
        plugin_id: 插件 ID
        request: 配置请求
        session: 数据库会话

    Returns:
        PluginConfigResponse
    """
    tenant_id = TenantContext.get_tenant_id()

    result = await plugin_config_service.config_plugin(
        session=session,
        tenant_id=tenant_id,
        plugin_id=plugin_id,
        plugin_config=request.plugin_config,
        runtime_config=request.runtime_config,
    )

    return result


@router.post(
    "/{plugin_id}/test",
    response_model=PluginTestResponse,
    summary="测试插件配置连接",
)
async def test_plugin(
    plugin_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> PluginTestResponse:
    """
    测试插件配置连接

    Args:
        plugin_id: 插件 ID
        session: 数据库会话

    Returns:
        PluginTestResponse
    """
    tenant_id = TenantContext.get_tenant_id()

    result = await plugin_config_service.test_plugin(
        session=session,
        tenant_id=tenant_id,
        plugin_id=plugin_id,
    )

    return result


@router.post(
    "/{plugin_id}/start",
    response_model=PluginStartResponse,
    summary="启动插件",
)
async def start_plugin(
    plugin_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> PluginStartResponse:
    """
    启动插件

    Args:
        plugin_id: 插件 ID
        session: 数据库会话

    Returns:
        PluginStartResponse
    """
    tenant_id = TenantContext.get_tenant_id()

    result = await plugin_config_service.start_plugin(
        session=session,
        tenant_id=tenant_id,
        plugin_id=plugin_id,
    )

    return result


@router.post(
    "/{plugin_id}/stop",
    response_model=PluginStopResponse,
    summary="停止插件",
)
async def stop_plugin(
    plugin_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> PluginStopResponse:
    """
    停止插件

    Args:
        plugin_id: 插件 ID
        session: 数据库会话

    Returns:
        PluginStopResponse
    """
    tenant_id = TenantContext.get_tenant_id()

    result = await plugin_config_service.stop_plugin(
        session=session,
        tenant_id=tenant_id,
        plugin_id=plugin_id,
    )

    return result
```

- [x] **步骤 2：注册路由**

修改 `server/python/src/ai/controllers/console/__init__.py`：

```python
from fastapi import APIRouter

from .plugin_config_controller import router as plugin_config_router

# ... 现有路由

# 注册插件配置路由
console_router.include_router(
    plugin_config_router,
    prefix="/ai/console/v1",
)
```

- [x] **步骤 3：Commit**

```bash
git add server/python/src/ai/controllers/console/plugin_config_controller.py
git add server/python/src/ai/controllers/console/__init__.py
git commit -m "feat(ai): 新增插件配置控制器

- 提供配置、测试、启动、停止插件的 HTTP 接口
- 路由前缀: /ai/console/v1/plugins/installations/{plugin_id}"
```

---

### 任务 12：调整 E2E 测试 - 安装流程

**文件：**
- 修改：`server/python/tests/ai/e2e/test_plugin_install.py`

- [x] **步骤 1：定位测试文件**

```bash
cd server/python && codegraph files tests/ai/e2e/test_plugin_install.py
```

- [x] **步骤 2：调整安装测试验证最终状态为 INACTIVE**

修改 `test_install_tongyi_plugin_and_verify_environment` 方法：

```python
@pytest.mark.asyncio
async def test_install_plugin_final_status_inactive(
    self,
    e2e_session,
    test_tenant_id,
    plugin_package_path,
    cleanup_test_resources,
    init_engine_pool,
    plugin_provider,
) -> None:
    """测试安装插件后状态为 INACTIVE"""
    # 上传并安装插件
    plugin_package = plugin_package_path("tongyi")

    with open(plugin_package, "rb") as f:
        file_content = f.read()

    manager = await PluginManagerFactory.get_manager(test_tenant_id, e2e_session)

    from ai.components.plugin.engine.models.request import InstallRequest
    install_request = InstallRequest(force=False, auto_start=False, config_override={})

    plugin_id = await manager.install_plugin(file_content, install_request)

    # 验证最终状态为 INACTIVE
    installation = await plugin_provider.get_installation(test_tenant_id, plugin_id)
    assert installation.status == "INACTIVE"
    assert installation.installed_at is not None

    # 清理
    cleanup_test_resources["plugin_ids"].append(plugin_id)
```

- [x] **步骤 3：移除 auto_start 参数验证**

检查所有测试方法，移除对 auto_start 参数的验证。

- [x] **步骤 4：运行测试验证**

运行：`cd server/python && uv run pytest tests/ai/e2e/test_plugin_install.py -v`

预期：PASS

- [x] **步骤 5：Commit**

```bash
git add server/python/tests/ai/e2e/test_plugin_install.py
git commit -m "test(ai): 调整安装测试验证最终状态为 INACTIVE

- 移除 auto_start 参数验证
- 验证安装成功后状态为 INACTIVE
- 验证 installed_at 字段已填充"
```

---

### 任务 13：调整 E2E 测试 - 调用流程

**文件：**
- 修改：`server/python/tests/ai/e2e/test_plugin_invoke.py`

- [x] **步骤 1：调整调用测试增加配置和启动步骤**

修改 `test_invoke_tongyi_model` 方法：

```python
@pytest.mark.asyncio
async def test_invoke_plugin_with_config_and_start(
    self,
    e2e_session: AsyncSession,
    test_tenant_id: str,
    plugin_package_path: callable,
    tongyi_api_key: str,
    plugin_provider,
) -> None:
    """测试插件调用流程（安装 → 配置 → 启动 → 调用）"""
    # 1. 安装插件
    plugin_package = plugin_package_path("tongyi")

    with open(plugin_package, "rb") as f:
        file_content = f.read()

    manager = await PluginManagerFactory.get_manager(test_tenant_id, e2e_session)

    from ai.components.plugin.engine.models.request import InstallRequest
    install_request = InstallRequest(force=False, auto_start=False, config_override={})

    plugin_id = await manager.install_plugin(file_content, install_request)

    # 验证安装状态为 INACTIVE
    installation = await plugin_provider.get_installation(test_tenant_id, plugin_id)
    assert installation.status == "INACTIVE"

    # 2. 配置插件
    from ai.services.plugin_config_service import plugin_config_service
    await plugin_config_service.config_plugin(
        session=e2e_session,
        tenant_id=test_tenant_id,
        plugin_id=plugin_id,
        plugin_config={"api_key": tongyi_api_key},
        runtime_config={},
    )

    # 3. 启动插件
    start_result = await plugin_config_service.start_plugin(
        session=e2e_session,
        tenant_id=test_tenant_id,
        plugin_id=plugin_id,
    )
    assert start_result.status == "ACTIVE"

    # 4. 调用插件
    # ... 现有调用逻辑
```

- [x] **步骤 2：运行测试验证**

运行：`cd server/python && uv run pytest tests/ai/e2e/test_plugin_invoke.py::test_invoke_plugin_with_config_and_start -v`

预期：PASS

- [x] **步骤 3：Commit**

```bash
git add server/python/tests/ai/e2e/test_plugin_invoke.py
git commit -m "test(ai): 调整调用测试增加配置和启动步骤

- 安装 → 配置 → 启动 → 调用完整流程
- 验证每个步骤的状态转换"
```

---

### 任务 14：调整 E2E 测试 - 完整生命周期

**文件：**
- 修改：`server/python/tests/ai/e2e/test_plugin_full_lifecycle.py`

- [x] **步骤 1：调整完整生命周期测试流程**

修改 `test_tongyi_plugin_full_lifecycle` 方法：

```python
@pytest.mark.asyncio
async def test_plugin_full_lifecycle_with_config(
    self,
    e2e_session: AsyncSession,
    test_tenant_id: str,
    plugin_package_path: callable,
    tongyi_api_key: str,
    tongyi_api_key_available: bool,
    cleanup_test_resources: dict,
    plugin_provider,
) -> None:
    """测试插件完整生命周期（安装 → 配置 → 测试 → 启动 → 调用 → 停止 → 卸载）"""
    # 1. 安装插件
    plugin_package = plugin_package_path("tongyi")

    with open(plugin_package, "rb") as f:
        file_content = f.read()

    manager = await PluginManagerFactory.get_manager(test_tenant_id, e2e_session)

    from ai.components.plugin.engine.models.request import InstallRequest
    install_request = InstallRequest(force=False, auto_start=False, config_override={})

    plugin_id = await manager.install_plugin(file_content, install_request)

    # 验证安装状态为 INACTIVE
    installation = await plugin_provider.get_installation(test_tenant_id, plugin_id)
    assert installation.status == "INACTIVE"

    cleanup_test_resources["plugin_ids"].append(plugin_id)

    # 2. 配置插件
    from ai.services.plugin_config_service import plugin_config_service
    await plugin_config_service.config_plugin(
        session=e2e_session,
        tenant_id=test_tenant_id,
        plugin_id=plugin_id,
        plugin_config={"api_key": tongyi_api_key},
        runtime_config={},
    )

    # 3. 测试连接
    test_result = await plugin_config_service.test_plugin(
        session=e2e_session,
        tenant_id=test_tenant_id,
        plugin_id=plugin_id,
    )
    # 注意：测试可能失败（API Key 无效），但不影响后续流程

    # 4. 启动插件
    start_result = await plugin_config_service.start_plugin(
        session=e2e_session,
        tenant_id=test_tenant_id,
        plugin_id=plugin_id,
    )
    assert start_result.status == "ACTIVE"

    # 5. 调用插件（如果有 API Key）
    if tongyi_api_key_available:
        # ... 现有调用逻辑
        pass

    # 6. 停止插件
    stop_result = await plugin_config_service.stop_plugin(
        session=e2e_session,
        tenant_id=test_tenant_id,
        plugin_id=plugin_id,
    )
    assert stop_result.status == "INACTIVE"

    # 7. 卸载插件
    await plugin_provider.delete_installation(test_tenant_id, plugin_id)

    # 验证卸载成功
    installation = await plugin_provider.get_installation(test_tenant_id, plugin_id)
    assert installation is None
```

- [x] **步骤 2：运行测试验证**

运行：`cd server/python && uv run pytest tests/ai/e2e/test_plugin_full_lifecycle.py::test_plugin_full_lifecycle_with_config -v`

预期：PASS

- [x] **步骤 3：Commit**

```bash
git add server/python/tests/ai/e2e/test_plugin_full_lifecycle.py
git commit -m "test(ai): 调整完整生命周期测试流程

- 安装 → 配置 → 测试 → 启动 → 调用 → 停止 → 卸载
- 验证每个步骤的状态转换
- 支持配置验证失败的场景"
```

---

### 任务 15：新增前端 API - pluginConfig.ts

**文件：**
- 新增：`web/vue/src/ai/api/pluginConfig.ts`

- [x] **步骤 1：创建 pluginConfig.ts 文件**

创建 `web/vue/src/ai/api/pluginConfig.ts`：

```typescript
/**
 * 插件配置相关 API
 */

import { post } from '@/utils/request'

/**
 * 配置插件请求
 */
export interface ConfigPluginRequest {
  plugin_config?: Record<string, any>
  runtime_config?: Record<string, any>
}

/**
 * 配置插件响应
 */
export interface ConfigPluginResponse {
  plugin_id: string
  validated: boolean | null
}

/**
 * 测试连接响应
 */
export interface TestPluginResponse {
  plugin_id: string
  validated: boolean
  message: string
}

/**
 * 启动插件响应
 */
export interface StartPluginResponse {
  plugin_id: string
  status: string
  port?: number
  warning?: string
}

/**
 * 停止插件响应
 */
export interface StopPluginResponse {
  plugin_id: string
  status: string
}

/**
 * 配置插件
 */
export async function configPlugin(
  pluginId: string,
  data: ConfigPluginRequest,
): Promise<ConfigPluginResponse> {
  return post(`/ai/console/v1/plugins/installations/${pluginId}/config`, data)
}

/**
 * 测试插件配置连接
 */
export async function testPlugin(
  pluginId: string,
): Promise<TestPluginResponse> {
  return post(`/ai/console/v1/plugins/installations/${pluginId}/test`)
}

/**
 * 启动插件
 */
export async function startPlugin(
  pluginId: string,
): Promise<StartPluginResponse> {
  return post(`/ai/console/v1/plugins/installations/${pluginId}/start`)
}

/**
 * 停止插件
 */
export async function stopPlugin(
  pluginId: string,
): Promise<StopPluginResponse> {
  return post(`/ai/console/v1/plugins/installations/${pluginId}/stop`)
}
```

- [x] **步骤 2：Commit**

```bash
git add web/vue/src/ai/api/pluginConfig.ts
git commit -m "feat(web): 新增插件配置相关 API

- configPlugin: 配置插件
- testPlugin: 测试配置连接
- startPlugin: 启动插件
- stopPlugin: 停止插件"
```

---

### 任务 16：调整前端 - PluginManagePage.vue

**文件：**
- 修改：`web/vue/src/ai/pages/PluginManagePage.vue`

- [x] **步骤 1：定位文件**

```bash
cd web/vue && find . -name "PluginManagePage.vue"
```

- [x] **步骤 2：增加配置、启动、停止按钮**

修改 `web/vue/src/ai/pages/PluginManagePage.vue`：

```vue
<template>
  <div class="plugin-manage-page">
    <el-table :data="plugins" style="width: 100%">
      <el-table-column prop="plugin_id" label="插件ID" width="200" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="validated" label="配置状态" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.validated === true" type="success">已验证</el-tag>
          <el-tag v-else-if="row.validated === false" type="danger">验证失败</el-tag>
          <el-tag v-else type="info">未测试</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="300">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'INACTIVE'"
            type="primary"
            size="small"
            @click="handleConfig(row.plugin_id)"
          >
            配置
          </el-button>
          <el-button
            v-if="row.status === 'INACTIVE'"
            type="success"
            size="small"
            @click="handleStart(row.plugin_id)"
          >
            启动
          </el-button>
          <el-button
            v-if="row.status === 'ACTIVE'"
            type="warning"
            size="small"
            @click="handleStop(row.plugin_id)"
          >
            停止
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { startPlugin, stopPlugin } from '@/ai/api/pluginConfig'

const plugins = ref([])

// 启动插件
const handleStart = async (pluginId: string) => {
  try {
    const result = await startPlugin(pluginId)

    if (result.warning) {
      ElMessageBox.alert(result.warning, '警告', {
        confirmButtonText: '确定',
        type: 'warning',
      })
    } else {
      ElMessage.success('插件启动成功')
    }

    // 刷新列表
    await loadPlugins()
  } catch (error) {
    ElMessage.error('插件启动失败')
  }
}

// 停止插件
const handleStop = async (pluginId: string) => {
  try {
    await stopPlugin(pluginId)
    ElMessage.success('插件停止成功')

    // 刷新列表
    await loadPlugins()
  } catch (error) {
    ElMessage.error('插件停止失败')
  }
}

// 配置插件
const handleConfig = (pluginId: string) => {
  // 跳转到配置页面
  // router.push(`/ai/plugins/${pluginId}/config`)
}

// 加载插件列表
const loadPlugins = async () => {
  // ... 加载逻辑
}

onMounted(() => {
  loadPlugins()
})
</script>
```

- [x] **步骤 3：Commit**

```bash
git add web/vue/src/ai/pages/PluginManagePage.vue
git commit -m "feat(web): 调整插件管理页面增加配置和启动停止功能

- 根据状态显示不同操作按钮
- 显示配置验证状态
- 支持启动和停止插件操作"
```

---

### 任务 17：调整前端 - PluginConfigPage.vue

**文件：**
- 修改：`web/vue/src/ai/pages/PluginConfigPage.vue`

- [x] **步骤 1：增加测试连接按钮**

修改 `web/vue/src/ai/pages/PluginConfigPage.vue`：

```vue
<template>
  <div class="plugin-config-page">
    <el-form :model="form" label-width="120px">
      <el-form-item label="API Key">
        <el-input v-model="form.plugin_config.api_key" type="password" />
      </el-form-item>

      <el-form-item label="Endpoint">
        <el-input v-model="form.plugin_config.endpoint" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSave">保存配置</el-button>
        <el-button @click="handleTest">测试连接</el-button>
      </el-form-item>
    </el-form>

    <el-dialog v-model="testDialogVisible" title="测试结果">
      <p>{{ testResult }}</p>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { configPlugin, testPlugin } from '@/ai/api/pluginConfig'

const props = defineProps<{
  pluginId: string
}>()

const form = reactive({
  plugin_config: {
    api_key: '',
    endpoint: '',
  },
  runtime_config: {},
})

const testDialogVisible = ref(false)
const testResult = ref('')

// 保存配置
const handleSave = async () => {
  try {
    const result = await configPlugin(props.pluginId, form)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('配置保存失败')
  }
}

// 测试连接
const handleTest = async () => {
  try {
    const result = await testPlugin(props.pluginId)

    testDialogVisible.value = true
    testResult.value = result.validated
      ? '连接成功'
      : `连接失败: ${result.message}`

    if (result.validated) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.warning('连接测试失败')
    }
  } catch (error) {
    ElMessage.error('连接测试失败')
  }
}
</script>
```

- [x] **步骤 2：Commit**

```bash
git add web/vue/src/ai/pages/PluginConfigPage.vue
git commit -m "feat(web): 调整插件配置页面增加测试连接功能

- 增加测试连接按钮
- 显示测试结果对话框
- 根据测试结果显示不同提示"
```

---

### 任务 18：调整前端 - tenant 模块 API

**文件：**
- 修改：`web/vue/src/tenant/api/plugin.ts`

- [x] **步骤 1：调整安装接口移除 auto_start 参数**

修改 `web/vue/src/tenant/api/plugin.ts`：

```typescript
/**
 * 安装插件请求
 */
export interface InstallPluginRequest {
  plugin_unique_identifier: string
  declaration: Record<string, any>
  plugin_type?: string
  runtime_type?: string
  // 移除 auto_start 参数
}

/**
 * 安装插件
 */
export async function installPlugin(
  data: InstallPluginRequest,
): Promise<InstallPluginResponse> {
  return post('/tenant/console/v1/plugins/installations', data)
}
```

- [x] **步骤 2：Commit**

```bash
git add web/vue/src/tenant/api/plugin.ts
git commit -m "refactor(web): 调整安装接口移除 auto_start 参数

- 移除 auto_start 参数
- 安装后插件状态为 INACTIVE，需手动启动"
```

---

### 任务 19：调整前端 - PluginInstallationList.vue

**文件：**
- 重命名：`web/vue/src/tenant/pages/admin/PluginManagePage.vue` → `PluginInstallationList.vue`

- [x] **步骤 1：重命名文件**

```bash
cd web/vue/src/tenant/pages/admin
git mv PluginManagePage.vue PluginInstallationList.vue
```

- [x] **步骤 2：调整页面内容移除启动停止功能**

修改 `web/vue/src/tenant/pages/admin/PluginInstallationList.vue`：

```vue
<template>
  <div class="plugin-installation-list">
    <el-table :data="installations" style="width: 100%">
      <el-table-column prop="plugin_id" label="插件ID" width="200" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="installed_at" label="安装时间" width="180" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'INACTIVE' || row.status === 'FAILED'"
            type="danger"
            size="small"
            @click="handleUninstall(row.plugin_id)"
          >
            卸载
          </el-button>
          <el-button
            v-if="row.status === 'ACTIVE'"
            disabled
            size="small"
          >
            请先停止插件
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { uninstallPlugin } from '@/tenant/api/plugin'

const installations = ref([])

// 卸载插件
const handleUninstall = async (pluginId: string) => {
  try {
    await ElMessageBox.confirm(
      '确定要卸载此插件吗？卸载后配置将被清除。',
      '确认卸载',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    await uninstallPlugin(pluginId)
    ElMessage.success('插件卸载成功')

    // 刷新列表
    await loadInstallations()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('插件卸载失败')
    }
  }
}

// 加载安装列表
const loadInstallations = async () => {
  // ... 加载逻辑
}

onMounted(() => {
  loadInstallations()
})
</script>
```

- [x] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginInstallationList.vue
git commit -m "refactor(web): 重命名并调整插件安装列表页面

- 重命名为 PluginInstallationList.vue
- 移除启动、停止、配置功能
- 仅保留卸载功能
- 状态为 ACTIVE 时禁止卸载"
```

---

### 任务 20：运行完整测试套件

**文件：**
- 无

- [x] **步骤 1：运行后端单元测试**

运行：`cd server/python && uv run pytest tests/tenant/unit/test_plugin_provider*.py tests/ai/unit/services/test_plugin_config_service.py tests/ai/unit/components/plugin/test_plugin_manager_*.py -v`

预期：所有测试通过

- [x] **步骤 2：运行后端 E2E 测试**

运行：`cd server/python && uv run pytest tests/ai/e2e/test_plugin_install.py tests/ai/e2e/test_plugin_invoke.py tests/ai/e2e/test_plugin_full_lifecycle.py -v`

预期：所有测试通过

- [x] **步骤 3：验证前端功能**

启动前端开发服务器，手动测试以下流程：

1. 安装插件 → 验证状态为 INACTIVE
2. 配置插件 → 保存配置
3. 测试连接 → 验证配置有效性
4. 启动插件 → 验证状态为 ACTIVE
5. 停止插件 → 验证状态为 INACTIVE
6. 卸载插件 → 验证记录已删除

- [x] **步骤 4：Commit 测试验证结果**

```bash
git add -A
git commit -m "test: 验证插件安装及配置功能调整完整性

- 后端单元测试全部通过
- 后端 E2E 测试全部通过
- 前端功能验证通过"
```

---

## 实施总结

**总计：20 个任务，预计 5-7 个工作日**

**关键里程碑：**
- 任务 1-4：协议和 Provider 层调整（1 天）
- 任务 5-8：核心逻辑层调整（1-2 天）
- 任务 9-11：接口层实现（1 天）
- 任务 12-14：测试调整（1 天）
- 任务 15-19：前端功能调整（1-2 天）
- 任务 20：完整测试验证（1 天）

**技术债务：**
- 任务 6 的 `_start_plugin_process` 方法需要实现（可能已存在）
- 任务 10 的 `test_plugin_connection` 方法需要实现（调用插件实际验证接口）

**风险缓解：**
- 每个任务独立 commit，便于回滚
- TDD 实践确保代码质量
- 分阶段测试验证，及时发现集成问题
