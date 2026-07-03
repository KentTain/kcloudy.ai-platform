# 插件安装及配置使用功能调整设计

**日期**: 2026-07-03
**版本**: 1.0
**状态**: 已批准

## 一、背景与目标

### 1.1 当前架构问题

当前插件系统存在以下问题：

1. **职责不清**：tenant 和 ai 模块都涉及安装和启动逻辑，边界模糊
2. **状态混淆**：PENDING 直接变为 ACTIVE，跳过了"安装完成但未启动"的中间状态
3. **配置缺失**：没有明确的配置步骤，配置验证状态未记录

### 1.2 调整目标

- **职责清晰化**：tenant 模块负责"有什么"（插件定义、安装记录），ai 模块负责"怎么用"（配置、启动、停止）
- **状态流转明确**：PENDING → INACTIVE → ACTIVE，每个状态有明确的触发条件
- **配置步骤显式化**：增加配置验证步骤，记录配置有效性状态
- **最小化数据模型改动**：不修改表结构，只调整服务、接口及功能

## 二、状态流转设计

### 2.1 状态流转图

```
                    tenant 模块                      ai 模块
                   (安装/卸载)                    (配置/启动/停止)

注册插件定义  →  [已存在于 tenant.plugin_definitions]
                    ↓
安装插件      →  PENDING (创建安装记录)
                    ↓ 安装成功
               INACTIVE (安装完成，未启动) ─────────→ 配置插件
                    ↓                                  ↓ 保存配置
                    │                              INACTIVE (已配置)
                    │                                  ↓ 测试配置（可选）
                    │                              INACTIVE (已验证/无效)
                    │                                  ↓ 启动插件
                    │                              ACTIVE (运行中)
                    │                                  ↓ 停止插件
                    │                              INACTIVE (已停止)
                    ↓ 卸载
               删除 INACTIVE 记录 + 清理 AI 配置
                    ↓
               INSTALL_FAILED
                    ↓ 卸载
               删除 FAILED 记录
```

### 2.2 状态定义

| 状态 | 含义 | 触发条件 | 负责模块 |
|------|------|---------|---------|
| PENDING | 待安装 | 创建安装记录时 | tenant |
| INACTIVE | 已安装未启动 | 安装成功 / 停止插件 | tenant / ai |
| ACTIVE | 运行中 | 启动插件成功 | ai |
| FAILED | 安装失败 | 安装过程出错 | tenant |

### 2.3 关键设计决策

1. **安装失败处理**：PENDING → FAILED，不创建 INACTIVE 记录
2. **配置是启动前置步骤**：用户必须先配置，然后才能启动插件
3. **配置验证方式**：提供独立的"测试连接"按钮，用户可选择测试
4. **配置验证状态**：存储在 `plugin_configs.plugin_config.validated` 字段（JSON 内部）
5. **无效配置启动**：允许 is_valid=false 的配置启动，但给出警告
6. **停止插件**：由 AI 模块负责（停止进程 + 更新 runtime_state + 通知 tenant 更新状态）
7. **卸载插件**：由 Tenant 模块负责（删除 installation + 减少引用计数 + 通知 ai 清理）

## 三、后端服务及接口设计

### 3.1 tenant 模块接口

#### 3.1.1 保留接口（无需修改）

```
POST   /tenant/admin/v1/plugin-definitions/scan     # 扫描注册插件
POST   /tenant/admin/v1/plugin-definitions/upload   # 上传注册插件
GET    /tenant/admin/v1/plugin-definitions          # 插件定义列表
GET    /tenant/admin/v1/plugin-definitions/{id}     # 插件定义详情
PATCH  /tenant/admin/v1/plugin-definitions/{id}     # 更新插件定义
DELETE /tenant/admin/v1/plugin-definitions/{id}     # 删除插件定义
```

#### 3.1.2 调整接口

**安装插件**
```
POST /tenant/console/v1/plugins/installations

请求体：
{
  "plugin_unique_identifier": "author/name:version@checksum",
  "declaration": {...},  // 完整声明内容
  "plugin_type": "local",  // 可选
  "runtime_type": "python"  // 可选
}

响应：
{
  "code": 200,
  "data": {
    "plugin_id": "author/name",
    "status": "INACTIVE",  // 成功时为 INACTIVE，失败时为 FAILED
    "installed_at": "2026-07-03T10:00:00Z"
  }
}
```

**变更点：**
- 移除 `auto_start` 参数（启动由 ai 模块负责）
- 返回安装结果（成功返回 INACTIVE，失败返回 FAILED）

**卸载插件**
```
DELETE /tenant/console/v1/plugins/installations/{plugin_id}

前置条件：
- 插件状态为 INACTIVE 或 FAILED
- 如果状态为 ACTIVE，返回错误"请先停止插件"

响应：
{
  "code": 200,
  "message": "卸载成功"
}
```

### 3.2 ai 模块接口

#### 3.2.1 新增接口

**配置插件**
```
POST /ai/console/v1/plugins/installations/{plugin_id}/config

请求体：
{
  "plugin_config": {
    "api_key": "xxx",
    "endpoint": "https://api.example.com"
  },
  "runtime_config": {
    "timeout": 30
  }
}

响应：
{
  "code": 200,
  "data": {
    "plugin_id": "author/name",
    "validated": null  // null=未测试, true=验证通过, false=验证失败
  }
}
```

**测试配置连接**
```
POST /ai/console/v1/plugins/installations/{plugin_id}/test

请求体：无

响应：
{
  "code": 200,
  "data": {
    "plugin_id": "author/name",
    "validated": true,  // 或 false
    "message": "连接成功"  // 或错误信息
  }
}
```

**启动插件**
```
POST /ai/console/v1/plugins/installations/{plugin_id}/start

请求体：无

响应（配置已验证）：
{
  "code": 200,
  "data": {
    "plugin_id": "author/name",
    "status": "ACTIVE",
    "port": 50001
  }
}

响应（配置未验证或无效，给出警告）：
{
  "code": 200,
  "data": {
    "plugin_id": "author/name",
    "status": "ACTIVE",
    "port": 50001,
    "warning": "配置未验证，可能无法正常工作"
  }
}
```

**停止插件**
```
POST /ai/console/v1/plugins/installations/{plugin_id}/stop

请求体：无

响应：
{
  "code": 200,
  "data": {
    "plugin_id": "author/name",
    "status": "INACTIVE"
  }
}
```

#### 3.2.2 保留接口（无需修改）

```
GET  /ai/console/v1/plugins/installations/{plugin_id}/runtime-state  # 获取运行时状态
GET  /ai/console/v1/plugins/runtime-states                           # 批量获取运行时状态
GET  /ai/console/v1/plugins/statistics                               # 获取插件统计数据
```

## 四、核心组件调整

### 4.1 plugin_protocols.py

**文件位置**: `server/python/src/framework/tenant/plugin_protocols.py`

#### 4.1.1 PluginInstallationDTO 调整

```python
@dataclass
class PluginInstallationDTO:
    """安装记录 DTO"""

    tenant_id: str
    plugin_id: str
    plugin_unique_identifier: str
    declaration: dict
    status: str = "PENDING"  # PENDING / ACTIVE / INACTIVE / FAILED
    installed_at: datetime | None = None  # 新增：安装完成时间
    freeze_threshold_hours: int = 24
    plugin_type: str | None = None
    runtime_type: str | None = None
    install_config: dict | None = None
    source: str | None = None
    meta: dict | None = None
```

**变更点：**
- 新增 `installed_at` 字段
- 移除 `auto_start` 字段（不再需要）

#### 4.1.2 PluginInstallationProvider 新增方法

```python
class PluginInstallationProvider(Protocol):
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

### 4.2 plugin_provider.py (tenant)

**文件位置**: `server/python/src/tenant/services/plugin_provider.py`

#### 4.2.1 实现 update_installation_status

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

#### 4.2.2 调整 create_installation

```python
async def create_installation(
    self, tenant_id: str, data: PluginInstallationDTO
) -> PluginInstallationDTO:
    """创建插件安装记录"""
    async with get_task_session() as session:
        # 确保插件定义已存在
        await self._ensure_plugin_definition(session, data)

        # 创建安装记录，初始状态 PENDING
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

**变更点：**
- 移除 `auto_start` 参数处理
- 初始状态固定为 `PENDING`

#### 4.2.3 调整 start_installation 和 stop_installation

这两个方法保持不变，但需要确保：
- `start_installation` 调用 AI inner API 后，更新状态为 `ACTIVE`
- `stop_installation` 调用 AI inner API 后，更新状态为 `INACTIVE`

### 4.3 plugin_manager.py (ai)

**文件位置**: `server/python/src/ai/components/plugin/engine/core/plugin_manager.py`

#### 4.3.1 install_plugin 方法调整

```python
async def install_plugin(
    self,
    plugin_package: bytes,
    install_request: InstallRequest,
) -> str:
    """
    安装插件

    变更点：
    - 移除 auto_start 参数处理
    - 安装成功后只更新状态为 INACTIVE，不启动插件
    """
    # 1. 解析插件包
    # 2. 验证插件配置
    # 3. 保存插件文件
    # 4. 创建 PENDING 记录
    # 5. 安装成功，更新状态为 INACTIVE
    # 6. 返回 plugin_id

    # ... 现有逻辑保留

    # 安装成功，更新状态为 INACTIVE
    provider = get_plugin_installation_provider()
    await provider.update_installation_status(
        self.tenant_id, plugin_id, "INACTIVE"
    )

    return plugin_id
```

#### 4.3.2 新增 start_plugin 方法

```python
async def start_plugin(self, plugin_id: str) -> dict:
    """
    启动插件（独立方法）

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

    return {
        "plugin_id": plugin_id,
        "status": "ACTIVE",
        "port": runtime.port,
        "warning": warning,
    }
```

#### 4.3.3 新增 stop_plugin 方法

```python
async def stop_plugin(self, plugin_id: str) -> dict:
    """
    停止插件（独立方法）

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

    return {
        "plugin_id": plugin_id,
        "status": "INACTIVE",
    }
```

### 4.4 install_task_manager.py (ai)

**文件位置**: `server/python/src/ai/components/plugin/engine/core/install_task_manager.py`

#### 4.4.1 调整 _install_plugin_item 方法

```python
async def _install_plugin_item(
    self, item: InstallationItem, task_type: TaskType
) -> bool:
    """安装单个插件项"""
    try:
        plugin_manager = await self.get_plugin_manager()

        if task_type == TaskType.INSTALL:
            # ... 现有逻辑

            # 从任务元数据中获取配置参数
            task = self._find_task_by_item(item)
            force = False
            if task and task.metadata:
                force = task.metadata.get("force", False)

            install_request = InstallRequest(
                force=force,
                auto_start=False,  # 固定为 False
                config_override={}
            )

            # 调用插件管理器安装
            plugin_name = await plugin_manager.install_plugin(
                plugin_package, install_request
            )

            # ... 更新进度

            return True

    except Exception as e:
        logger.error(f"安装插件项失败: {item.identifier}, 错误: {e}")
        item.error_message = str(e)
        return False
```

**变更点：**
- 移除 `auto_start` 参数获取逻辑
- `auto_start` 固定为 `False`

## 五、前端功能调整

### 5.1 tenant 模块前端页面

**职责：插件定义管理 + 安装/卸载**

#### 5.1.1 保留页面（无需修改）

- `PluginDefinitionList.vue` — 插件定义列表
- `PluginDefinitionDetailPage.vue` — 插件定义详情
- `PluginScanPage.vue` — 插件扫描
- `PluginUploadPage.vue` — 插件上传
- `RemotePluginBrowsePage.vue` — 远程插件浏览

#### 5.1.2 调整页面

**PluginManagePage.vue → PluginInstallationList.vue**

**功能：**
- 显示租户已安装的插件列表
- 显示插件状态（PENDING / INACTIVE / ACTIVE / FAILED）
- 提供"安装"按钮（跳转到插件定义页面）
- 提供"卸载"按钮（仅 INACTIVE / FAILED 状态可用）
- 移除"启动/停止/配置"相关功能

**API 调用：**
```typescript
// tenant/api/plugin.ts
export const pluginApi = {
  // 安装插件
  installPlugin: (data: InstallRequest) =>
    post('/tenant/console/v1/plugins/installations', data),

  // 卸载插件
  uninstallPlugin: (pluginId: string) =>
    del(`/tenant/console/v1/plugins/installations/${pluginId}`),
}
```

### 5.2 ai 模块前端页面

**职责：插件使用管理（配置/测试/启动/停止）**

#### 5.2.1 PluginManagePage.vue

**功能：**
- 显示 INACTIVE / ACTIVE 状态的插件
- 根据状态显示不同操作按钮：
  - INACTIVE：配置、启动
  - ACTIVE：停止、查看运行时状态
- 显示配置状态（未配置 / 已配置 / 已验证 / 验证失败）

#### 5.2.2 PluginConfigPage.vue

**功能：**
- 配置表单（plugin_config、runtime_config）
- "测试连接"按钮
- "保存配置"按钮
- 显示配置验证状态

**API 调用：**
```typescript
// ai/api/plugin.ts
export const pluginApi = {
  // 配置插件
  configPlugin: (pluginId: string, data: ConfigRequest) =>
    post(`/ai/console/v1/plugins/installations/${pluginId}/config`, data),

  // 测试配置
  testConfig: (pluginId: string) =>
    post(`/ai/console/v1/plugins/installations/${pluginId}/test`),

  // 启动插件
  startPlugin: (pluginId: string) =>
    post(`/ai/console/v1/plugins/installations/${pluginId}/start`),

  // 停止插件
  stopPlugin: (pluginId: string) =>
    post(`/ai/console/v1/plugins/installations/${pluginId}/stop`),
}
```

## 六、测试影响分析

### 6.1 后端测试影响

#### 6.1.1 需要调整的测试

| 测试文件 | 影响范围 | 调整内容 |
|---------|---------|---------|
| `tests/ai/e2e/test_plugin_install.py` | 安装流程 | 移除 `auto_start` 参数验证，验证最终状态为 INACTIVE |
| `tests/ai/e2e/test_plugin_invoke.py` | 调用流程 | 先执行配置和启动，再测试调用 |
| `tests/ai/e2e/test_plugin_full_lifecycle.py` | 完整生命周期 | 调整流程顺序：安装 → 配置 → 测试 → 启动 → 调用 → 停止 → 卸载 |
| `tests/tenant/unit/test_plugin_provider.py` | Provider 实现 | 验证 `update_installation_status` 方法 |
| `tests/ai/unit/services/test_plugin_management_service.py` | 服务层 | 调整安装和启动逻辑 |

#### 6.1.2 需要新增的测试

- **配置插件测试**
  - 有效配置
  - 无效配置
  - 空配置

- **测试连接测试**
  - 连接成功
  - 连接失败
  - 未配置时测试

- **启动警告测试**
  - 未验证配置启动
  - 无效配置启动
  - 有效配置启动

### 6.2 前端测试影响

#### 6.2.1 需要调整的测试

- 插件管理页面测试（移除启动/停止逻辑）
- 插件配置页面测试（新增配置、测试连接逻辑）

## 七、实施计划

### 7.1 阶段一：后端核心逻辑调整（优先）

**预计工期：3 天**

1. 调整 `plugin_protocols.py` 协议定义
2. 实现 `plugin_provider.py` 的 `update_installation_status` 方法
3. 调整 `plugin_manager.py` 的安装和启动逻辑
4. 调整 `install_task_manager.py` 的安装流程
5. 新增 ai 模块的配置、测试、启动、停止接口

### 7.2 阶段二：测试调整

**预计工期：2 天**

1. 调整现有 e2e 测试
2. 新增配置和启动相关测试
3. 运行完整测试套件验证

### 7.3 阶段三：前端功能调整

**预计工期：3 天**

1. 调整 tenant 模块前端页面
2. 调整 ai 模块前端页面
3. 新增前端 API 调用

### 7.4 阶段四：集成测试

**预计工期：1 天**

1. 端到端流程测试
2. 跨模块交互测试

**总计：9 天**

## 八、风险评估

### 8.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 状态同步失败 | tenant 和 ai 状态不一致 | 使用事务补偿机制，记录日志便于排查 |
| 配置验证超时 | 影响用户体验 | 设置合理的超时时间，提供异步验证选项 |
| 启动失败处理 | 状态卡在 INACTIVE | 提供重试机制，记录失败原因 |

### 8.2 兼容性风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 现有插件数据迁移 | 历史数据状态需要调整 | 编写迁移脚本，将 ACTIVE 状态改为 INACTIVE |
| API 接口变更 | 前端需要同步调整 | 保持向后兼容，版本化接口 |

## 九、附录

### 9.1 配置验证状态定义

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| `null` | 未测试 | 保存配置后，未执行测试连接 |
| `true` | 验证通过 | 测试连接成功 |
| `false` | 验证失败 | 测试连接失败 |

### 9.2 状态机完整定义

```
状态转换表：

当前状态 | 操作 | 目标状态 | 负责模块
---------|------|---------|----------
PENDING  | 安装成功 | INACTIVE | tenant
PENDING  | 安装失败 | FAILED | tenant
INACTIVE | 启动 | ACTIVE | ai
ACTIVE   | 停止 | INACTIVE | ai
INACTIVE | 卸载 | (删除) | tenant
FAILED   | 卸载 | (删除) | tenant
```

### 9.3 错误码定义

| 错误码 | 含义 | 场景 |
|--------|------|------|
| `PLUGIN_ALREADY_INSTALLED` | 插件已安装 | 重复安装 |
| `PLUGIN_NOT_INACTIVE` | 插件状态不是 INACTIVE | 启动前置检查失败 |
| `PLUGIN_NOT_ACTIVE` | 插件状态不是 ACTIVE | 停止前置检查失败 |
| `PLUGIN_CONFIG_REQUIRED` | 插件未配置 | 启动时未找到配置 |
| `PLUGIN_UNINSTALL_FAILED` | 卸载失败 | 插件状态为 ACTIVE 时卸载 |
