# 插件启动/停止功能设计

## 目标

在 tenant 模块和 AI 模块实现插件的启动/停止功能，真正启动/停止插件进程，支持单个操作和批量操作（一个插件 → 多租户）。

## 架构

扩展 `PluginInstallationProvider` 协议新增 `start_installation` / `stop_installation` 方法，由 `PluginInstallationProviderImpl` 实现，内部直接调用 AI 模块的 `PluginManagementService` 管理进程。tenant admin API 提供管理和批量操作入口，AI console API 保持现有不变。

## 协议扩展

### PluginInstallationProvider 新增方法

文件：`server/python/src/framework/tenant/plugin_protocols.py`

```python
def start_installation(self, tenant_id: str, plugin_id: str) -> PluginInstallationDTO:
    """启动租户插件（管理状态 + 启动进程）"""

def stop_installation(self, tenant_id: str, plugin_id: str) -> PluginInstallationDTO:
    """停止租户插件（管理状态 + 停止进程）"""
```

### PluginInstallationProviderImpl 实现

文件：`server/python/src/tenant/services/plugin_provider.py`

- `start_installation`：设置 TenantContext → 获取 AI 的 `PluginManagementService` → 调用 `start_plugin_with_response(session, plugin_id)` → 更新 tenant 侧安装状态为 `ACTIVE` → 返回 DTO
- `stop_installation`：设置 TenantContext → 获取 AI 的 `PluginManagementService` → 调用 `stop_plugin_with_response(session, plugin_id)` → 更新 tenant 侧安装状态为 `INACTIVE` → 返回 DTO

AI 侧 `PluginRuntimeState` 由 `PluginManagementService` 内部自动更新（现有逻辑已处理 `status="active"` / `"inactive"`、`process_id`、`port`、`last_started_at`、`last_stopped_at`）。

## API 端点

### Tenant Admin API

文件：`server/python/src/tenant/controllers/admin/plugin_controller.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/start` | 单个启动 |
| POST | `/tenant/admin/v1/plugin-installations/{tenant_id}/{plugin_id}/stop` | 单个停止 |
| POST | `/tenant/admin/v1/plugin-installations/start/batch` | 批量启动 |
| POST | `/tenant/admin/v1/plugin-installations/stop/batch` | 批量停止 |

### AI Console API（已有，保持不变）

- `POST /ai/console/v1/plugins/installations/start?plugin_id=xxx`
- `POST /ai/console/v1/plugins/installations/stop?plugin_id=xxx`

## Schema 定义

文件：`server/python/src/tenant/schemas/plugin.py`

```python
class BatchStartStopRequest(BaseModel):
    plugin_id: str
    tenant_ids: list[str]

class BatchOperationItem(BaseModel):
    tenant_id: str
    plugin_id: str
    status: str

class BatchOperationFailedItem(BaseModel):
    tenant_id: str
    plugin_id: str
    error: str

class BatchStartStopResponse(BaseModel):
    success: list[BatchOperationItem]
    failed: list[BatchOperationFailedItem]
```

## Service 层

文件：`server/python/src/tenant/services/plugin_installation_service.py`（新建）

```python
class PluginInstallationService:
    async def start_plugin(self, session, tenant_id: str, plugin_id: str) -> PluginInstallationDTO:
        # 1. 校验安装记录存在且状态为 INACTIVE
        # 2. 校验插件定义为启用状态
        # 3. 调用 provider.start_installation(tenant_id, plugin_id)
        # 4. 返回 DTO

    async def stop_plugin(self, session, tenant_id: str, plugin_id: str) -> PluginInstallationDTO:
        # 1. 校验安装记录存在且状态为 ACTIVE
        # 2. 调用 provider.stop_installation(tenant_id, plugin_id)
        # 3. 返回 DTO

    async def batch_start_plugins(self, session, plugin_id: str, tenant_ids: list[str]) -> BatchStartStopResponse:
        # 循环调用 start_plugin，收集 success/failed

    async def batch_stop_plugins(self, session, plugin_id: str, tenant_ids: list[str]) -> BatchStartStopResponse:
        # 循环调用 stop_plugin，收集 success/failed
```

## 前端

### API 函数

文件：`web/vue/src/tenant/api/plugin.ts`

新增 `startPlugin`、`stopPlugin`、`batchStartPlugins`、`batchStopPlugins` 函数及对应类型定义。

### UI 入口

- **插件安装列表页**：操作列添加"启动"/"停止"按钮
- **插件安装详情页**：添加"启动"/"停止"按钮
- **批量操作**：列表页支持多选后批量启动/停止（一个插件的多租户场景，在插件定义页操作）

## 前置校验

- 安装记录必须存在
- 启动前状态须为 INACTIVE，停止前状态须为 ACTIVE
- 插件定义须为启用状态

## 错误处理

- 进程启动失败：AI 侧回滚 RuntimeState，tenant 侧状态保持 INACTIVE，返回错误信息
- 部分失败（批量）：成功的不回滚，失败的记入 failed 列表
- 不存在的租户或安装记录：记入 failed 列表

## 文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `server/python/src/framework/tenant/plugin_protocols.py` | 扩展 Provider 协议 |
| 修改 | `server/python/src/tenant/services/plugin_provider.py` | 实现 start/stop |
| 修改 | `server/python/src/tenant/schemas/plugin.py` | 新增请求/响应 Schema |
| 新建 | `server/python/src/tenant/services/plugin_installation_service.py` | 安装 Service |
| 修改 | `server/python/src/tenant/controllers/admin/plugin_controller.py` | 新增 API 端点 |
| 修改 | `web/vue/src/tenant/api/plugin.ts` | 新增前端 API |
| 修改 | `web/vue/src/tenant/pages/admin/PluginDefinitionList.vue` | 批量启停按钮 |
| 修改 | `web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue` | 启停按钮 |
