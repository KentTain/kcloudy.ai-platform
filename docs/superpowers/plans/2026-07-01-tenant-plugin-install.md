# 租户插件安装功能 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [x]`）语法来跟踪进度。

**目标：** 从插件定义页给租户安装插件，支持单个和批量安装（一个插件→多租户），同步 AI 侧 PluginConfig 和 PluginRuntimeState 但不启动进程。

**架构：** 复用 PluginInstallationProvider 协议创建 tenant 侧安装记录，直接操作 AI 侧模型同步配置。后端在 plugin_definition_service 新增 install_to_tenants 方法，前端新增 InstallToTenantsDialog 组件。

**技术栈：** Python/FastAPI（后端），Vue 3/TypeScript（前端），SQLAlchemy（ORM），shadcn-vue（UI 组件）

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `server/python/src/tenant/schemas/plugin.py` | 修改 | 新增 InstallToTenantsRequest/Response Schema |
| `server/python/src/tenant/services/plugin_definition_service.py` | 修改 | 新增 install_to_tenants 业务方法 |
| `server/python/src/tenant/controllers/admin/plugin_controller.py` | 修改 | 新增 POST 端点 |
| `server/python/tests/tenant/integration/test_plugin_definition_api.py` | 修改 | 新增安装 API 集成测试 |
| `web/vue/src/tenant/api/plugin.ts` | 修改 | 新增 API 函数和类型定义 |
| `web/vue/src/tenant/pages/admin/InstallToTenantsDialog.vue` | 新增 | 租户选择弹窗组件 |
| `web/vue/src/tenant/pages/admin/PluginDefinitionList.vue` | 修改 | 引入 Dialog，添加操作按钮 |
| `web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue` | 修改 | 引入 Dialog，添加操作按钮 |

---

### 任务 1：后端 Schema

**文件：**
- 修改：`server/python/src/tenant/schemas/plugin.py`

- [x] **步骤 1：在 `tenant/schemas/plugin.py` 末尾追加安装 Schema**

在文件末尾（`ScanDirectoryConfirmRequest` 类之后）追加：

```python
# ─────────────────────────────────────────────────────────────────────────────
# 安装到租户 Schema
# ─────────────────────────────────────────────────────────────────────────────


class InstallToTenantsRequest(BaseModel):
    """安装插件到租户请求"""

    tenant_ids: list[str] = Field(..., min_length=1, description="目标租户ID列表")
    auto_start: bool = Field(default=False, description="是否自动启动")


class InstallSuccessItem(BaseModel):
    """安装成功项"""

    tenant_id: str = Field(..., description="租户ID")
    plugin_id: str = Field(..., description="插件ID")


class InstallFailedItem(BaseModel):
    """安装失败项"""

    tenant_id: str = Field(..., description="租户ID")
    message: str = Field(..., description="错误信息")


class InstallSkippedItem(BaseModel):
    """安装跳过项"""

    tenant_id: str = Field(..., description="租户ID")
    reason: str = Field(..., description="跳过原因")


class InstallToTenantsResponse(BaseModel):
    """安装插件到租户响应"""

    success: list[InstallSuccessItem] = Field(default_factory=list, description="成功列表")
    failed: list[InstallFailedItem] = Field(default_factory=list, description="失败列表")
    skipped: list[InstallSkippedItem] = Field(default_factory=list, description="跳过列表")
```

- [x] **步骤 2：Commit**

```bash
git add server/python/src/tenant/schemas/plugin.py
git commit -m "feat(tenant): 新增安装插件到租户的 Schema 定义"
```

---

### 任务 2：后端 Service 方法

**文件：**
- 修改：`server/python/src/tenant/services/plugin_definition_service.py`

- [x] **步骤 1：在 `PluginDefinitionService` 类中新增 `install_to_tenants` 方法**

在 `preview_parse_package` 方法之后、`# 单例实例` 行之前，新增方法：

```python
    @staticmethod
    async def install_to_tenants(
        session: AsyncSession,
        plugin_id: str,
        request: "InstallToTenantsRequest",
    ) -> "InstallToTenantsResponse":
        """
        安装插件到指定租户

        流程：
        1. 查询插件定义，校验存在且启用
        2. 遍历租户列表，逐个安装
        3. 同步创建 AI 侧 PluginConfig 和 PluginRuntimeState

        Args:
            session: 数据库会话
            plugin_id: 插件ID
            request: 安装请求

        Returns:
            InstallToTenantsResponse: 批量安装结果
        """
        from tenant.schemas.plugin import (
            InstallFailedItem,
            InstallSkippedItem,
            InstallSuccessItem,
            InstallToTenantsResponse,
        )
        from tenant.models.plugin_installation import TenantPluginInstallation
        from tenant.models.tenant import Tenant
        from ai.models.plugin_config import PluginConfig as AIPluginConfig
        from ai.models.plugin_runtime_state import PluginRuntimeState
        from framework.tenant.plugin_protocols import (
            PluginInstallationDTO,
            get_plugin_installation_provider,
        )

        # 1. 查询插件定义
        stmt = select(TenantPluginDefinition).where(
            TenantPluginDefinition.plugin_id == plugin_id
        )
        result = await session.execute(stmt)
        definition = result.scalar_one_or_none()

        if not definition:
            raise NotFoundError(message=f"插件定义不存在: {plugin_id}")

        if not definition.is_enabled:
            raise ValueError(f"插件定义已禁用: {plugin_id}")

        success: list[InstallSuccessItem] = []
        failed: list[InstallFailedItem] = []
        skipped: list[InstallSkippedItem] = []

        provider = get_plugin_installation_provider()

        for tenant_id in request.tenant_ids:
            try:
                # 校验租户存在
                tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
                tenant_result = await session.execute(tenant_stmt)
                tenant = tenant_result.scalar_one_or_none()
                if not tenant:
                    failed.append(InstallFailedItem(
                        tenant_id=tenant_id,
                        message="租户不存在",
                    ))
                    continue

                # 检查是否已安装
                existing_stmt = select(TenantPluginInstallation).where(
                    TenantPluginInstallation.tenant_id == tenant_id,
                    TenantPluginInstallation.plugin_id == plugin_id,
                )
                existing_result = await session.execute(existing_stmt)
                existing_installation = existing_result.scalar_one_or_none()
                if existing_installation:
                    skipped.append(InstallSkippedItem(
                        tenant_id=tenant_id,
                        reason="already_installed",
                    ))
                    continue

                # 通过 Provider 创建安装记录（自动处理引用计数）
                dto = PluginInstallationDTO(
                    tenant_id=tenant_id,
                    plugin_id=definition.plugin_id,
                    plugin_unique_identifier=definition.plugin_unique_identifier,
                    declaration=definition.declaration or {},
                    status="PENDING",
                    auto_start=request.auto_start,
                    plugin_type=definition.install_type,
                )
                await provider.create_installation(tenant_id, dto)

                # 同步 AI 侧：创建 PluginConfig
                existing_config_stmt = select(AIPluginConfig).where(
                    AIPluginConfig.tenant_id == tenant_id,
                    AIPluginConfig.plugin_id == plugin_id,
                )
                existing_config_result = await session.execute(existing_config_stmt)
                if not existing_config_result.scalar_one_or_none():
                    ai_config = AIPluginConfig(
                        tenant_id=tenant_id,
                        plugin_id=definition.plugin_id,
                        plugin_unique_identifier=definition.plugin_unique_identifier,
                        plugin_config=definition.declaration,
                        runtime_config={},
                    )
                    session.add(ai_config)

                # 同步 AI 侧：创建 PluginRuntimeState
                existing_runtime_stmt = select(PluginRuntimeState).where(
                    PluginRuntimeState.tenant_id == tenant_id,
                    PluginRuntimeState.plugin_id == plugin_id,
                )
                existing_runtime_result = await session.execute(existing_runtime_stmt)
                if not existing_runtime_result.scalar_one_or_none():
                    runtime_state = PluginRuntimeState(
                        tenant_id=tenant_id,
                        plugin_id=definition.plugin_id,
                        status="inactive",
                    )
                    session.add(runtime_state)

                # 更新安装记录状态为 INACTIVE
                await provider.update_installation(
                    tenant_id, plugin_id, {"status": "INACTIVE"}
                )

                success.append(InstallSuccessItem(
                    tenant_id=tenant_id,
                    plugin_id=plugin_id,
                ))

            except Exception as e:
                _logger.error(f"安装插件到租户失败: tenant_id={tenant_id}, plugin_id={plugin_id}, error={e}")
                failed.append(InstallFailedItem(
                    tenant_id=tenant_id,
                    message=str(e),
                ))

        _logger.info(
            f"安装插件到租户完成: plugin_id={plugin_id}, "
            f"success={len(success)}, failed={len(failed)}, skipped={len(skipped)}"
        )

        return InstallToTenantsResponse(
            success=success,
            failed=failed,
            skipped=skipped,
        )
```

- [x] **步骤 2：Commit**

```bash
git add server/python/src/tenant/services/plugin_definition_service.py
git commit -m "feat(tenant): 新增 install_to_tenants 服务方法"
```

---

### 任务 3：后端 API 端点

**文件：**
- 修改：`server/python/src/tenant/controllers/admin/plugin_controller.py`

- [x] **步骤 1：在 controller 中新增端点**

首先在文件顶部的 import 块中追加 import：

在 `from tenant.schemas.plugin import (` 块中追加：
```python
    InstallToTenantsRequest,
    InstallToTenantsResponse,
```

然后在 `delete_plugin_definition` 函数之后追加新端点：

```python
@router.post("/plugin-definitions/{plugin_id:path}/install")
async def install_plugin_to_tenants(
    plugin_id: str,
    request: InstallToTenantsRequest,
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    安装插件到指定租户

    场景：平台管理员将插件安装到多个租户
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-definitions/{plugin_id}/install
    THEN 为每个目标租户创建安装记录，同步 AI 侧配置，不启动插件进程
    """
    try:
        result = await plugin_definition_service.install_to_tenants(
            session, plugin_id, request
        )
        return ApiResponse.success(data=result.model_dump())
    except ValueError as e:
        return ApiResponse.fail(message=str(e))
    except NotFoundError as e:
        return ApiResponse.fail(message=str(e))
```

- [x] **步骤 2：Commit**

```bash
git add server/python/src/tenant/controllers/admin/plugin_controller.py
git commit -m "feat(tenant): 新增安装插件到租户的 API 端点"
```

---

### 任务 4：后端集成测试

**文件：**
- 修改：`server/python/tests/tenant/integration/test_plugin_definition_api.py`

- [x] **步骤 1：新增安装 API 测试**

在文件末尾追加测试函数：

```python
class TestInstallPluginToTenants:
    """安装插件到租户 API 测试"""

    async def test_install_to_single_tenant(self, client, db_session, admin_headers):
        """测试安装插件到单个租户"""
        # 先创建插件定义
        definition = TenantPluginDefinition(
            plugin_id="test/install-plugin",
            plugin_unique_identifier="test/install-plugin:1.0.0@test",
            declaration={"configuration": {"label": {"en_US": "Test Plugin"}}},
            refers=0,
            install_type="local",
            is_enabled=True,
        )
        db_session.add(definition)

        # 创建租户
        tenant = Tenant(
            name="测试租户",
            code="test-install-tenant",
            status="active",
        )
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 调用安装 API
        response = client.post(
            f"/tenant/admin/v1/plugin-definitions/test/install-plugin/install",
            json={"tenant_ids": [str(tenant.id)]},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["success"]) == 1
        assert data["success"][0]["tenant_id"] == str(tenant.id)
        assert data["success"][0]["plugin_id"] == "test/install-plugin"
        assert len(data["failed"]) == 0
        assert len(data["skipped"]) == 0

    async def test_install_to_already_installed_tenant(self, client, db_session, admin_headers):
        """测试安装插件到已安装的租户应跳过"""
        definition = TenantPluginDefinition(
            plugin_id="test/install-dup",
            plugin_unique_identifier="test/install-dup:1.0.0@test",
            declaration={},
            refers=1,
            install_type="local",
            is_enabled=True,
        )
        db_session.add(definition)

        tenant = Tenant(
            name="重复安装租户",
            code="test-dup-tenant",
            status="active",
        )
        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        # 先安装一次
        installation = TenantPluginInstallation(
            tenant_id=str(tenant.id),
            plugin_id="test/install-dup",
            plugin_unique_identifier="test/install-dup:1.0.0@test",
            status="ACTIVE",
        )
        db_session.add(installation)
        await db_session.commit()

        # 再次安装应被跳过
        response = client.post(
            f"/tenant/admin/v1/plugin-definitions/test/install-dup/install",
            json={"tenant_ids": [str(tenant.id)]},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["skipped"]) == 1
        assert data["skipped"][0]["reason"] == "already_installed"

    async def test_install_disabled_plugin(self, client, db_session, admin_headers):
        """测试安装已禁用的插件应失败"""
        definition = TenantPluginDefinition(
            plugin_id="test/install-disabled",
            plugin_unique_identifier="test/install-disabled:1.0.0@test",
            declaration={},
            refers=0,
            install_type="local",
            is_enabled=False,
        )
        db_session.add(definition)
        await db_session.commit()

        response = client.post(
            f"/tenant/admin/v1/plugin-definitions/test/install-disabled/install",
            json={"tenant_ids": ["some-tenant-id"]},
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json()["code"] != 200

    async def test_install_nonexistent_tenant(self, client, db_session, admin_headers):
        """测试安装到不存在的租户应记录失败"""
        definition = TenantPluginDefinition(
            plugin_id="test/install-no-tenant",
            plugin_unique_identifier="test/install-no-tenant:1.0.0@test",
            declaration={},
            refers=0,
            install_type="local",
            is_enabled=True,
        )
        db_session.add(definition)
        await db_session.commit()

        response = client.post(
            f"/tenant/admin/v1/plugin-definitions/test/install-no-tenant/install",
            json={"tenant_ids": ["00000000-0000-0000-0000-000000000000"]},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["failed"]) == 1
        assert data["failed"][0]["message"] == "租户不存在"
```

- [x] **步骤 2：在文件顶部补充必要的 import**

确保文件顶部有：
```python
from tenant.models.plugin_definition import TenantPluginDefinition
from tenant.models.plugin_installation import TenantPluginInstallation
from tenant.models.tenant import Tenant
```

- [x] **步骤 3：运行测试验证**

运行：`cd server/python && python -m pytest tests/tenant/integration/test_plugin_definition_api.py -v -k "TestInstallPluginToTenants"`
预期：测试通过

- [x] **步骤 4：Commit**

```bash
git add server/python/tests/tenant/integration/test_plugin_definition_api.py
git commit -m "test(tenant): 新增安装插件到租户的集成测试"
```

---

### 任务 5：前端 API 类型和函数

**文件：**
- 修改：`web/vue/src/tenant/api/plugin.ts`

- [x] **步骤 1：在类型定义区域追加安装相关类型**

在 `PluginStatistics` 接口之后、`// ==================== API 函数 ====================` 注释之前追加：

```typescript
// ==================== 安装到租户 ====================

export interface InstallToTenantsRequest {
  tenant_ids: string[];
  auto_start?: boolean;
}

export interface InstallSuccessItem {
  tenant_id: string;
  plugin_id: string;
}

export interface InstallFailedItem {
  tenant_id: string;
  message: string;
}

export interface InstallSkippedItem {
  tenant_id: string;
  reason: string;
}

export interface InstallToTenantsResponse {
  success: InstallSuccessItem[];
  failed: InstallFailedItem[];
  skipped: InstallSkippedItem[];
}
```

- [x] **步骤 2：在 API 函数区域追加安装函数**

在 `getPluginStatistics` 函数之后追加：

```typescript
export const installPluginToTenants = (pluginId: string, data: InstallToTenantsRequest) =>
  rawPost<ApiResponse<InstallToTenantsResponse>>(`/tenant/admin/v1/plugin-definitions/${pluginId}/install`, data);
```

- [x] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/api/plugin.ts
git commit -m "feat(tenant): 新增安装插件到租户的前端 API 函数和类型"
```

---

### 任务 6：InstallToTenantsDialog 组件

**文件：**
- 新增：`web/vue/src/tenant/pages/admin/InstallToTenantsDialog.vue`

- [x] **步骤 1：创建弹窗组件**

参考 `iam/components/PermissionAssignDialog.vue` 的 Dialog 模式，创建租户选择弹窗：

```vue
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Button, Badge, Checkbox, Input } from '@/components'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components'
import { notifyError, notifySuccess } from '@/framework/utils/feedback'
import { installPluginToTenants } from '@/tenant/api/plugin'
import { getTenants } from '@/tenant/api/tenant'
import type { PluginDefinition } from '@/tenant/api/plugin'
import type { Tenant } from '@/tenant/types'

const props = defineProps<{
  plugin: PluginDefinition | null
  open: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  installed: []
}>()

const loading = ref(false)
const installing = ref(false)
const tenants = ref<Tenant[]>([])
const selectedIds = ref<string[]>([])
const searchKeyword = ref('')

const filteredTenants = computed(() => {
  if (!searchKeyword.value) return tenants.value
  const kw = searchKeyword.value.toLowerCase()
  return tenants.value.filter(
    (t) => t.name.toLowerCase().includes(kw) || t.code.toLowerCase().includes(kw)
  )
})

const selectedCount = computed(() => selectedIds.value.length)

const toggleSelectAll = () => {
  if (selectedCount.value === filteredTenants.value.length && filteredTenants.value.length > 0) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredTenants.value.map((t) => t.id)
  }
}

const toggleTenant = (id: string) => {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) {
    selectedIds.value = [...selectedIds.value, id]
  } else {
    selectedIds.value = selectedIds.value.filter((i) => i !== id)
  }
}

const isSelected = (id: string) => selectedIds.value.includes(id)

const loadTenants = async () => {
  loading.value = true
  try {
    const res = await getTenants({ page: 1, page_size: 200, status: 'active' })
    if (res.data) {
      tenants.value = res.data
    }
  } catch {
    notifyError('加载租户列表失败')
  } finally {
    loading.value = false
  }
}

const handleInstall = async () => {
  if (selectedIds.value.length === 0) {
    notifyError('请选择至少一个租户')
    return
  }
  if (!props.plugin) return

  installing.value = true
  try {
    const res = await installPluginToTenants(props.plugin.plugin_id, {
      tenant_ids: selectedIds.value,
    })
    if (res.data) {
      const { success, failed, skipped } = res.data
      const parts: string[] = []
      if (success.length > 0) parts.push(`成功 ${success.length} 个`)
      if (skipped.length > 0) parts.push(`跳过 ${skipped.length} 个`)
      if (failed.length > 0) parts.push(`失败 ${failed.length} 个`)
      notifySuccess(`安装完成：${parts.join('，')}`)
    }
    emit('update:open', false)
    emit('installed')
  } catch {
    notifyError('安装失败')
  } finally {
    installing.value = false
  }
}

watch(
  () => props.open,
  (val) => {
    if (val) {
      selectedIds.value = []
      searchKeyword.value = ''
      loadTenants()
    }
  }
)
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[520px]">
      <DialogHeader>
        <DialogTitle>安装到租户</DialogTitle>
        <DialogDescription>
          将插件「{{ plugin?.plugin_id }}」安装到选定的租户
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-3">
        <!-- 搜索 -->
        <Input
          v-model="searchKeyword"
          placeholder="搜索租户名称或编码"
        />

        <!-- 操作栏 -->
        <div class="flex items-center justify-between text-sm">
          <span class="text-muted-foreground">
            已选 {{ selectedCount }} 个租户
          </span>
          <Button variant="ghost" size="sm" @click="toggleSelectAll">
            {{ selectedCount === filteredTenants.length && filteredTenants.length > 0 ? '取消全选' : '全选' }}
          </Button>
        </div>

        <!-- 租户列表 -->
        <ScrollArea class="h-[300px] rounded-md border">
          <div v-if="loading" class="flex items-center justify-center py-8 text-muted-foreground">
            加载中...
          </div>
          <div v-else-if="filteredTenants.length === 0" class="flex items-center justify-center py-8 text-muted-foreground">
            无匹配租户
          </div>
          <div v-else class="p-2 space-y-1">
            <div
              v-for="tenant in filteredTenants"
              :key="tenant.id"
              class="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted cursor-pointer"
              @click="toggleTenant(tenant.id)"
            >
              <Checkbox :checked="isSelected(tenant.id)" />
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium truncate">{{ tenant.name }}</div>
                <div class="text-xs text-muted-foreground">{{ tenant.code }}</div>
              </div>
              <Badge :variant="tenant.status === 'active' ? 'default' : 'secondary'" class="shrink-0">
                {{ tenant.status === 'active' ? '活跃' : '停用' }}
              </Badge>
            </div>
          </div>
        </ScrollArea>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="emit('update:open', false)">取消</Button>
        <Button :disabled="selectedCount === 0 || installing" @click="handleInstall">
          {{ installing ? '安装中...' : `确认安装（${selectedCount} 个租户）` }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
```

- [x] **步骤 2：Commit**

```bash
git add web/vue/src/tenant/pages/admin/InstallToTenantsDialog.vue
git commit -m "feat(tenant): 新增 InstallToTenantsDialog 组件"
```

---

### 任务 7：PluginDefinitionList 集成 Dialog

**文件：**
- 修改：`web/vue/src/tenant/pages/admin/PluginDefinitionList.vue`

- [x] **步骤 1：添加 import 和状态**
```typescript
import {
  Eye,
  Package,
  Pencil,
  RefreshCw,
  RotateCcw,
  Search,
  Trash2,
  CheckCircle,
  Star,
  Users,
  Upload,
  FolderSearch,
  Download,
} from "@lucide/vue";
```

2. 在 import 区域追加 Dialog 组件：
```typescript
import InstallToTenantsDialog from "./InstallToTenantsDialog.vue";
```

3. 在 `const router = useRouter();` 之后追加状态：
```typescript
const installDialogOpen = ref(false);
const installTargetPlugin = ref<PluginDefinition | null>(null);
```

4. 在 `handleDelete` 函数之后追加：
```typescript
const handleInstallToTenants = (row: PluginDefinition) => {
  installTargetPlugin.value = row;
  installDialogOpen.value = true;
};

const handleInstalled = () => {
  dataTable.refresh();
  loadStats();
};
```

- [x] **步骤 2：在操作列中添加按钮**

在 columns 定义的操作列 `cell` 函数中，在"编辑"按钮之前添加"安装"按钮：

```typescript
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleInstallToTenants(plugin) },
          () => [h(Download, { class: "mr-1 h-3.5 w-3.5" }), "安装"]
        ),
```

- [x] **步骤 3：在 template 末尾添加 Dialog**

在 `</template>` 之前追加：

```html
    <InstallToTenantsDialog
      :plugin="installTargetPlugin"
      :open="installDialogOpen"
      @update:open="installDialogOpen = $event"
      @installed="handleInstalled"
    />
```

- [x] **步骤 4：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginDefinitionList.vue
git commit -m "feat(tenant): 插件定义列表页集成安装到租户弹窗"
```

---

### 任务 8：PluginDefinitionDetailPage 集成 Dialog

**文件：**
- 修改：`web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue`

- [x] **步骤 1：添加 import 和状态**

1. 在 lucide icon import 中追加 `Download`：
```typescript
import {
  ArrowLeft,
  Pencil,
  Copy,
  ChevronDown,
  ChevronUp,
  Check,
  Download,
} from '@lucide/vue'
```

2. 在 import 区域追加：
```typescript
import InstallToTenantsDialog from './InstallToTenantsDialog.vue'
```

3. 在 `const copied = ref(false)` 之后追加：
```typescript
const installDialogOpen = ref(false)

const handleInstallToTenants = () => {
  installDialogOpen.value = true
}

const handleInstalled = () => {
  loadPluginDetail()
}
```

- [x] **步骤 2：在 template 操作区添加按钮**

在 `<template #actions>` 区域的"返回列表"按钮之后追加：

```html
      <Button variant="outline" @click="handleInstallToTenants" data-testid="install-to-tenants-button">
        <Download class="mr-1 h-4 w-4" />
        安装到租户
      </Button>
```

- [x] **步骤 3：在 template 末尾添加 Dialog**

在 `</AppPage>` 之前追加：

```html
    <InstallToTenantsDialog
      :plugin="plugin"
      :open="installDialogOpen"
      @update:open="installDialogOpen = $event"
      @installed="handleInstalled"
    />
```

- [x] **步骤 4：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue
git commit -m "feat(tenant): 插件定义详情页集成安装到租户弹窗"
```

---

### 任务 9：端到端验证

- [x] **步骤 1：启动后端服务，确认新端点注册成功**

运行：`cd server/python && python -c "from tenant.controllers.admin.plugin_controller import router; print([r.path for r in router.routes])"`
预期：输出中包含 `/plugin-definitions/{plugin_id:path}/install`

- [x] **步骤 2：运行后端集成测试**

运行：`cd server/python && python -m pytest tests/tenant/integration/test_plugin_definition_api.py -v -k "TestInstallPluginToTenants"`
预期：全部 PASS

- [x] **步骤 3：启动前端 dev server，验证页面交互**

运行：`cd web/vue && pnpm dev`

验证项：
1. 插件定义列表页每行有"安装"按钮
2. 点击弹出 Dialog，可搜索/选择租户
3. 确认安装后显示结果摘要
4. 插件定义详情页有"安装到租户"按钮
5. 功能正常工作

- [x] **步骤 4：最终 Commit**

```bash
git add -A
git commit -m "feat(tenant): 完成租户插件安装功能（单个+批量）"
```
