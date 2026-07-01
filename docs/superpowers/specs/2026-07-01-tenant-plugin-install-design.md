# 租户插件安装功能设计

## 概述

在 tenant 模块的管理端（admin）添加给租户安装插件的功能，支持单个和批量安装。安装来源为已注册的 `TenantPluginDefinition`，操作入口在插件定义列表页和详情页。安装后同步创建 AI 侧 `PluginConfig` 和 `PluginRuntimeState` 记录，但不启动插件进程。

## 架构方案

复用 `PluginInstallationProvider` 协议层，在 tenant admin API 中调用 `provider.create_installation()` 创建 tenant 侧安装记录，再直接操作 AI 侧模型同步配置。

## 后端 API

### 端点

```
POST /tenant/admin/v1/plugin-definitions/{definition_id}/install
```

### 请求 Schema

```python
class InstallToTenantsRequest(BaseModel):
    tenant_ids: list[str] = Field(..., min_length=1, description="目标租户ID列表")
    auto_start: bool = Field(default=False, description="是否自动启动")
```

### 响应 Schema

```python
class InstallSuccessItem(BaseModel):
    tenant_id: str
    plugin_id: str

class InstallFailedItem(BaseModel):
    tenant_id: str
    message: str

class InstallSkippedItem(BaseModel):
    tenant_id: str
    reason: str  # 如 "already_installed"

class InstallToTenantsResponse(BaseModel):
    success: list[InstallSuccessItem]
    failed: list[InstallFailedItem]
    skipped: list[InstallSkippedItem]
```

### 处理逻辑

1. 查询 `TenantPluginDefinition` by `definition_id`，校验存在且 `is_enabled=True`
2. 遍历 `tenant_ids`，对每个租户：
   - 校验租户存在
   - 检查 `TenantPluginInstallation` 是否已存在（`tenant_id + plugin_id` 唯一约束），已存在则 skip
   - 构造 `PluginInstallationDTO`（从 definition 提取 declaration、plugin_id 等）
   - 调用 `provider.create_installation()` 创建安装记录（状态 PENDING）
   - 创建 AI 侧 `PluginConfig` 记录（tenant_id, plugin_id, plugin_config=declaration, runtime_config={}）
   - 创建 AI 侧 `PluginRuntimeState` 记录（状态 inactive）
   - 更新安装记录状态为 INACTIVE
3. 返回 `InstallToTenantsResponse`

### 错误处理

- 单个租户安装失败不影响其他租户，记录到 failed 列表继续处理
- AI 侧记录创建失败时，回滚该租户的 tenant 侧安装记录（删除已创建的 installation）

## AI 侧同步逻辑

安装到租户时，同步创建 AI 侧的 `PluginConfig` 和 `PluginRuntimeState` 记录，不启动插件进程。

**具体步骤：**
1. 从 `TenantPluginDefinition.declaration` 解析插件配置，构造 `AIPluginConfig`：
   - `tenant_id`：目标租户
   - `plugin_id`：插件 ID
   - `plugin_config`：definition.declaration（完整 JSON）
   - `runtime_config`：默认空 dict
2. 使用 `AIPluginConfig.create()` 写入 AI schema
3. 创建 `PluginRuntimeState` 记录，状态为 `inactive`
4. 更新 `TenantPluginInstallation` 状态从 PENDING → INACTIVE

## 前端交互

### 入口

- 插件定义列表页（`PluginDefinitionList`）每行新增"安装到租户"操作按钮
- 插件定义详情页（`PluginDefinitionDetailPage`）新增"安装到租户"按钮

### 交互流程

1. 点击"安装到租户"按钮，弹出 Dialog
2. Dialog 内容：
   - 顶部展示当前插件信息（plugin_id、名称、版本）— 只读
   - 租户选择区：支持搜索过滤，多选 checkbox 列表
   - 底部操作按钮：取消 / 确认安装
3. 确认后调用 API，显示 loading
4. 完成后展示结果摘要（成功 X 个 / 跳过 X 个 / 失败 X 个），关闭 Dialog 刷新列表

### 组件拆分

- 新增 `InstallToTenantsDialog.vue` 组件
- 在 `PluginDefinitionList.vue` 和 `PluginDefinitionDetailPage.vue` 中引入
- 新增 API 函数 `installPluginToTenants(definitionId, data)`

## 涉及文件

### 后端（新增/修改）

| 文件 | 操作 | 说明 |
|------|------|------|
| `server/python/src/tenant/schemas/admin/plugin_definition.py` | 新增 | InstallToTenantsRequest/Response Schema |
| `server/python/src/tenant/routers/admin/plugin_definition.py` | 修改 | 新增 install_to_tenants 端点 |

### 前端（新增/修改）

| 文件 | 操作 | 说明 |
|------|------|------|
| `web/vue/src/tenant/api/plugin.ts` | 修改 | 新增 installPluginToTenants API 函数和类型 |
| `web/vue/src/tenant/components/InstallToTenantsDialog.vue` | 新增 | 安装到租户弹窗组件 |
| `web/vue/src/tenant/pages/admin/PluginDefinitionList.vue` | 修改 | 引入 Dialog，添加操作按钮 |
| `web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue` | 修改 | 引入 Dialog，添加操作按钮 |
