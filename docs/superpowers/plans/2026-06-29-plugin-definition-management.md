# 插件定义管理功能实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为插件定义列表页面实现详情查看、状态编辑、启用/禁用切换、扫描目录注册和上传插件注册功能。

**架构：** 后端新增 2 个预览 API（扫描预览、插件包解析），前端新增 4 个独立页面（详情、编辑、扫描、上传）+ 修改列表页行操作。

**技术栈：** Python FastAPI + Pydantic（后端），Vue 3 + TypeScript + shadcn-vue（前端）

---

## 文件结构

### 后端

| 文件 | 变更类型 | 职责 |
|------|----------|------|
| `server/python/src/tenant/schemas/plugin.py` | 修改 | 新增预览相关 Schema 类型 |
| `server/python/src/tenant/services/plugin_definition_service.py` | 修改 | 新增预览服务方法 |
| `server/python/src/tenant/controllers/admin/plugin_controller.py` | 修改 | 新增预览 API 端点 |

### 前端

| 文件 | 变更类型 | 职责 |
|------|----------|------|
| `web/vue/src/tenant/api/plugin.ts` | 修改 | 新增 API 函数和类型 |
| `web/vue/src/tenant/router/index.ts` | 修改 | 新增路由配置 |
| `web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue` | 新增 | 详情页 |
| `web/vue/src/tenant/pages/admin/PluginDefinitionEditPage.vue` | 新增 | 编辑页 |
| `web/vue/src/tenant/pages/admin/PluginScanPage.vue` | 新增 | 扫描目录页 |
| `web/vue/src/tenant/pages/admin/PluginUploadPage.vue` | 新增 | 上传插件页 |
| `web/vue/src/tenant/pages/admin/PluginDefinitionList.vue` | 修改 | 调整行操作按钮 |

---

## 任务 1：后端 Schema 类型定义

**文件：**
- 修改：`server/python/src/tenant/schemas/plugin.py`

- [ ] **步骤 1：添加预览相关 Schema 类型**

在 `server/python/src/tenant/schemas/plugin.py` 文件末尾添加：

```python
# ─────────────────────────────────────────────────────────────────────────────
# 预览功能 Schema
# ─────────────────────────────────────────────────────────────────────────────


from typing import Literal


class ScannedPluginPreview(BaseModel):
    """扫描预览结果"""

    plugin_id: str = Field(..., description="插件ID")
    version: str = Field(..., description="版本号")
    name: str = Field(..., description="插件名称")
    description: str = Field(default="", description="插件描述")
    exists: bool = Field(default=False, description="是否已存在")
    status: Literal["ready", "invalid"] = Field(default="ready", description="状态：ready=可导入，invalid=解析失败")
    error_message: str | None = Field(None, description="错误信息")


class ParsedPluginInfo(BaseModel):
    """解析插件结果"""

    plugin_id: str = Field(..., description="插件ID")
    version: str = Field(..., description="版本号")
    name: str = Field(..., description="插件名称")
    description: str = Field(default="", description="插件描述")
    manifest_type: str | None = Field(None, description="清单类型")
    declaration: dict[str, Any] = Field(default_factory=dict, description="完整声明内容")
    exists: bool = Field(default=False, description="是否已存在")


class ScanDirectoryConfirmRequest(BaseModel):
    """扫描确认请求"""

    directory: str = Field(..., description="服务器目录路径")
    recursive: bool = Field(default=False, description="是否递归扫描子目录")
    plugin_ids: list[str] = Field(default_factory=list, description="指定要导入的插件ID列表")
```

- [ ] **步骤 2：运行类型检查验证**

运行：`cd server/python && uv run python -c "from tenant.schemas.plugin import ScannedPluginPreview, ParsedPluginInfo, ScanDirectoryConfirmRequest; print('Schema 导入成功')"`

预期：输出 "Schema 导入成功"

- [ ] **步骤 3：Commit**

```bash
git add server/python/src/tenant/schemas/plugin.py
git commit -m "feat(tenant): 新增插件预览 Schema 类型"
```

---

## 任务 2：后端 Service 预览方法

**文件：**
- 修改：`server/python/src/tenant/services/plugin_definition_service.py`

- [ ] **步骤 1：添加扫描预览方法**

在 `PluginDefinitionService` 类中添加方法：

```python
@staticmethod
async def preview_scan_directory(
    session: AsyncSession,
    directory: str,
    recursive: bool = False,
) -> list[dict[str, Any]]:
    """
    预览扫描目录中的插件

    Args:
        session: 数据库会话
        directory: 服务器目录路径
        recursive: 是否递归扫描子目录

    Returns:
        list[dict]: 预览结果列表
    """
    from pathlib import Path

    dir_path = Path(directory)

    if not dir_path.exists():
        raise ValueError(f"目录不存在: {directory}")

    if not dir_path.is_dir():
        raise ValueError(f"路径不是目录: {directory}")

    # 收集所有 .zip 文件
    if recursive:
        zip_files = list(dir_path.rglob("*.zip"))
    else:
        zip_files = list(dir_path.glob("*.zip"))

    if not zip_files:
        return []

    results: list[dict[str, Any]] = []

    # 查询已存在的插件ID
    existing_stmt = select(TenantPluginDefinition.plugin_id)
    existing_result = await session.execute(existing_stmt)
    existing_ids = {row[0] for row in existing_result.fetchall()}

    for zip_file in zip_files:
        try:
            # 解析插件包
            package_info = plugin_package_service.parse_package_from_path(zip_file)

            # 从 declaration 中获取名称和描述
            manifest = package_info.declaration.get("_manifest", {})
            name = manifest.get("name", package_info.name)
            description = manifest.get("description", "")

            results.append({
                "plugin_id": package_info.plugin_id,
                "version": package_info.version,
                "name": name,
                "description": description,
                "exists": package_info.plugin_id in existing_ids,
                "status": "ready",
                "error_message": None,
            })
        except Exception as e:
            # 解析失败
            results.append({
                "plugin_id": zip_file.name,
                "version": "unknown",
                "name": zip_file.stem,
                "description": "",
                "exists": False,
                "status": "invalid",
                "error_message": str(e),
            })

    return results
```

- [ ] **步骤 2：添加解析插件包预览方法**

在 `PluginDefinitionService` 类中添加方法：

```python
@staticmethod
async def preview_parse_package(
    session: AsyncSession,
    package_data: bytes,
) -> dict[str, Any]:
    """
    预览解析插件包

    Args:
        session: 数据库会话
        package_data: 插件包二进制数据

    Returns:
        dict: 解析结果

    Raises:
        ValueError: 插件包解析失败
    """
    # 解析插件包
    package_info = plugin_package_service.parse_package_from_bytes(package_data)

    # 检查是否已存在
    existing_stmt = select(TenantPluginDefinition).where(
        TenantPluginDefinition.plugin_id == package_info.plugin_id
    )
    existing_result = await session.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()

    # 从 declaration 中获取名称和描述
    manifest = package_info.declaration.get("_manifest", {})
    name = manifest.get("name", package_info.name)
    description = manifest.get("description", "")

    return {
        "plugin_id": package_info.plugin_id,
        "version": package_info.version,
        "name": name,
        "description": description,
        "manifest_type": package_info.manifest_type,
        "declaration": package_info.declaration,
        "exists": existing is not None,
    }
```

- [ ] **步骤 3：运行类型检查验证**

运行：`cd server/python && uv run python -c "from tenant.services.plugin_definition_service import plugin_definition_service; print('Service 导入成功')"`

预期：输出 "Service 导入成功"

- [ ] **步骤 4：Commit**

```bash
git add server/python/src/tenant/services/plugin_definition_service.py
git commit -m "feat(tenant): 新增插件预览 Service 方法"
```

---

## 任务 3：后端 Controller 预览 API 端点

**文件：**
- 修改：`server/python/src/tenant/controllers/admin/plugin_controller.py`

- [ ] **步骤 1：添加扫描预览 API 端点**

在 `plugin_controller.py` 中添加导入和端点：

```python
# 在文件开头的导入部分添加
from tenant.schemas.plugin import (
    # ... 现有导入 ...
    ScannedPluginPreview,
    ParsedPluginInfo,
    ScanDirectoryConfirmRequest,
)

# 在 scan_directory_for_plugins 函数之前添加

@router.post("/plugin-definitions/scan/preview")
async def preview_scan_directory(
    request: ScanDirectoryRequest,
    _perm: None = Depends(require_admin_permission("tenant:plugin:read")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    预览扫描服务器目录中的插件

    场景：平台管理员预览目录中的插件列表
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-definitions/scan/preview
    THEN 返回目录中所有插件的预览信息，包含是否已存在标记
    """
    try:
        results = await plugin_definition_service.preview_scan_directory(
            session=session,
            directory=request.directory,
            recursive=request.recursive,
        )
        return ApiResponse.success(data=results)
    except ValueError as e:
        return ApiResponse.fail(message=str(e))
```

- [ ] **步骤 2：添加解析插件包 API 端点**

```python
@router.post("/plugin-definitions/parse")
async def parse_plugin_package_preview(
    _perm: None = Depends(require_admin_permission("tenant:plugin:read")),
    session: AsyncSession = Depends(get_db_session),
    file: UploadFile = File(..., description="插件包文件（.zip）"),
) -> ApiResponse:
    """
    解析插件包预览

    场景：平台管理员上传插件包预览解析结果
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-definitions/parse
    THEN 返回插件包解析结果，包含是否已存在标记
    """
    # 验证文件格式
    if not file.filename or not file.filename.endswith(".zip"):
        return ApiResponse.fail(message="请上传 .zip 格式的插件包")

    # 读取文件内容
    package_data = await file.read()

    try:
        result = await plugin_definition_service.preview_parse_package(
            session=session,
            package_data=package_data,
        )
        return ApiResponse.success(data=result)
    except ValueError as e:
        return ApiResponse.fail(message=f"插件包解析失败: {str(e)}")
```

- [ ] **步骤 3：修改现有扫描 API 支持 plugin_ids 参数**

修改 `scan_directory_for_plugins` 函数：

```python
@router.post("/plugin-definitions/scan")
async def scan_directory_for_plugins(
    request: ScanDirectoryConfirmRequest,  # 修改类型
    _perm: None = Depends(require_admin_permission("tenant:plugin:write")),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    """
    扫描服务器目录注册插件定义

    场景：平台管理员扫描服务器目录批量注册插件定义
    WHEN 管理员请求 POST /tenant/admin/v1/plugin-definitions/scan
    THEN 扫描目录中的所有 .zip 文件，解析 manifest，上传到 MinIO，注册到 plugin_definitions 表
    """
    directory = Path(request.directory)

    if not directory.exists():
        return ApiResponse.fail(message=f"目录不存在: {request.directory}")

    if not directory.is_dir():
        return ApiResponse.fail(message=f"路径不是目录: {request.directory}")

    # 收集所有 .zip 文件
    if request.recursive:
        zip_files = list(directory.rglob("*.zip"))
    else:
        zip_files = list(directory.glob("*.zip"))

    if not zip_files:
        return ApiResponse.success(
            data=ScanDirectoryResponse(
                total_count=0,
                success_count=0,
                skipped_count=0,
                failed_count=0,
                results=[],
            ).model_dump()
        )

    results: list[ScannedPluginResult] = []
    success_count = 0
    skipped_count = 0
    failed_count = 0

    for zip_file in zip_files:
        try:
            # 解析插件包
            package_info = plugin_package_service.parse_package_from_path(zip_file)

            # 如果指定了 plugin_ids，只处理选中的插件
            if request.plugin_ids and package_info.plugin_id not in request.plugin_ids:
                continue

            package_data = zip_file.read_bytes()

            # 注册插件定义
            try:
                response = await plugin_definition_service.register_definition(
                    session=session,
                    package_info=package_info,
                    package_data=package_data,
                    overwrite=False,
                )
                results.append(
                    ScannedPluginResult(
                        plugin_id=package_info.plugin_id,
                        version=package_info.version,
                        status="success",
                        message="注册成功",
                    )
                )
                success_count += 1
            except Exception as e:
                error_msg = str(e)
                if "已存在" in error_msg:
                    results.append(
                        ScannedPluginResult(
                            plugin_id=package_info.plugin_id,
                            version=package_info.version,
                            status="skipped",
                            message="插件定义已存在",
                        )
                    )
                    skipped_count += 1
                else:
                    results.append(
                        ScannedPluginResult(
                            plugin_id=package_info.plugin_id,
                            version=package_info.version,
                            status="failed",
                            message=error_msg,
                        )
                    )
                    failed_count += 1

        except Exception as e:
            # 解析失败
            results.append(
                ScannedPluginResult(
                    plugin_id=zip_file.name,
                    version="unknown",
                    status="failed",
                    message=f"解析失败: {str(e)}",
                )
            )
            failed_count += 1

    # 提交事务
    await session.commit()

    return ApiResponse.success(
        data=ScanDirectoryResponse(
            total_count=len(zip_files),
            success_count=success_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            results=results,
        ).model_dump()
    )
```

- [ ] **步骤 4：启动后端验证 API**

运行：`cd server/python && uv run python manage.py runserver`

预期：服务启动成功，无报错

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/controllers/admin/plugin_controller.py
git commit -m "feat(tenant): 新增插件预览 API 端点"
```

---

## 任务 4：前端 API 类型和函数

**文件：**
- 修改：`web/vue/src/tenant/api/plugin.ts`

- [ ] **步骤 1：添加类型定义**

在 `web/vue/src/tenant/api/plugin.ts` 中添加：

```typescript
// ==================== 预览功能类型 ====================

export interface ScannedPluginPreview {
  plugin_id: string;
  version: string;
  name: string;
  description: string;
  exists: boolean;
  status: 'ready' | 'invalid';
  error_message?: string;
}

export interface ParsedPluginInfo {
  plugin_id: string;
  version: string;
  name: string;
  description: string;
  manifest_type: string;
  declaration: Record<string, any>;
  exists: boolean;
}

export interface ScanDirectoryConfirmRequest {
  directory: string;
  recursive?: boolean;
  plugin_ids: string[];
}
```

- [ ] **步骤 2：添加 API 函数**

在 `web/vue/src/tenant/api/plugin.ts` 中添加：

```typescript
// ==================== 预览功能 API ====================

export const scanDirectoryPreview = (data: ScanDirectoryRequest) =>
  rawPost<ApiResponse<ScannedPluginPreview[]>>('/tenant/admin/v1/plugin-definitions/scan/preview', data);

export const parsePluginPackage = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return rawPost<ApiResponse<ParsedPluginInfo>>('/tenant/admin/v1/plugin-definitions/parse', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
```

- [ ] **步骤 3：修改 scanDirectoryForPlugins 函数参数类型**

将现有的 `scanDirectoryForPlugins` 函数修改为：

```typescript
export const scanDirectoryForPlugins = (data: ScanDirectoryConfirmRequest) =>
  rawPost<ApiResponse<ScanDirectoryResponse>>('/tenant/admin/v1/plugin-definitions/scan', data);
```

- [ ] **步骤 4：运行 TypeScript 检查**

运行：`cd web/vue && pnpm check`

预期：无 TypeScript 错误

- [ ] **步骤 5：Commit**

```bash
git add web/vue/src/tenant/api/plugin.ts
git commit -m "feat(web): 新增插件预览 API 类型和函数"
```

---

## 任务 5：前端路由配置

**文件：**
- 修改：`web/vue/src/tenant/router/index.ts`

- [ ] **步骤 1：更新插件定义相关路由**

将现有的 `plugin-definitions` 路由部分替换为：

```typescript
{
  path: "plugin-definitions",
  name: "AdminPluginDefinitions",
  component: () => import("@/tenant/pages/admin/PluginDefinitionList.vue"),
  meta: { title: "插件定义", requiresAdminAuth: true, permissions: ["tenant:plugin:read"] },
},
{
  path: "plugin-definitions/scan",
  name: "AdminPluginDefinitionScan",
  component: () => import("@/tenant/pages/admin/PluginScanPage.vue"),
  meta: { title: "扫描目录注册插件", hidden: true, requiresAdminAuth: true, permissions: ["tenant:plugin:write"] },
},
{
  path: "plugin-definitions/upload",
  name: "AdminPluginDefinitionUpload",
  component: () => import("@/tenant/pages/admin/PluginUploadPage.vue"),
  meta: { title: "上传插件包", hidden: true, requiresAdminAuth: true, permissions: ["tenant:plugin:write"] },
},
{
  path: "plugin-definitions/:id",
  name: "AdminPluginDefinitionDetail",
  component: () => import("@/tenant/pages/admin/PluginDefinitionDetailPage.vue"),
  meta: { title: "插件详情", hidden: true, requiresAdminAuth: true, permissions: ["tenant:plugin:read"] },
},
{
  path: "plugin-definitions/:id/edit",
  name: "AdminPluginDefinitionEdit",
  component: () => import("@/tenant/pages/admin/PluginDefinitionEditPage.vue"),
  meta: { title: "编辑插件状态", hidden: true, requiresAdminAuth: true, permissions: ["tenant:plugin:write"] },
},
```

**注意**：`/scan` 和 `/upload` 必须放在 `/:id` 之前，避免被动态路由匹配。

- [ ] **步骤 2：运行 TypeScript 检查**

运行：`cd web/vue && pnpm check`

预期：无 TypeScript 错误

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/router/index.ts
git commit -m "feat(web): 新增插件定义管理路由配置"
```

---

## 任务 6：前端详情页

**文件：**
- 新增：`web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue`

- [ ] **步骤 1：创建详情页组件**

创建文件 `web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue`：

```vue
<script setup lang="ts">
import { ArrowLeft, Copy, Pencil, Check, X } from "@lucide/vue";
import { computed, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Button, Card, Badge } from "@/components";
import { notifyError, notifySuccess } from "@/framework/utils/feedback";
import { getPluginDefinition } from "@/tenant/api/plugin";
import type { PluginDefinitionDetail } from "@/tenant/api/plugin";

const route = useRoute();
const router = useRouter();
const pluginId = route.params.id as string;

const loading = ref(true);
const plugin = ref<PluginDefinitionDetail | null>(null);
const isJsonExpanded = ref(true);

const loadPlugin = async () => {
  loading.value = true;
  try {
    const response = await getPluginDefinition(pluginId);
    if (response.data) {
      plugin.value = response.data;
    }
  } catch (error: any) {
    console.error("加载插件详情失败:", error);
    notifyError(error?.response?.data?.msg || "加载插件详情失败");
  } finally {
    loading.value = false;
  }
};

const handleBack = () => {
  router.push("/admin/plugin-definitions");
};

const handleEdit = () => {
  router.push(`/admin/plugin-definitions/${pluginId}/edit`);
};

const copyJson = async () => {
  if (!plugin.value) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(plugin.value.declaration, null, 2));
    notifySuccess("已复制到剪贴板");
  } catch {
    notifyError("复制失败");
  }
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
};

const jsonDisplay = computed(() => {
  if (!plugin.value) return "";
  return JSON.stringify(plugin.value.declaration, null, 2);
});

onMounted(() => {
  loadPlugin();
});
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-detail-page">
    <!-- 页面标题区 -->
    <div class="flex items-center gap-3">
      <Button variant="ghost" size="sm" @click="handleBack">
        <ArrowLeft class="mr-1 h-4 w-4" />
        返回列表
      </Button>
      <h2 class="text-xl font-semibold">插件详情</h2>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <div class="text-muted-foreground">加载中...</div>
    </div>

    <!-- 详情内容 -->
    <template v-else-if="plugin">
      <!-- 基本信息卡 -->
      <Card class="p-5">
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="font-medium">基本信息</h3>
          </div>
          <div class="grid gap-3 text-sm">
            <div class="flex">
              <span class="w-28 text-muted-foreground">插件ID</span>
              <span class="font-mono">{{ plugin.plugin_id }}</span>
            </div>
            <div class="flex">
              <span class="w-28 text-muted-foreground">唯一标识</span>
              <span class="font-mono text-xs">{{ plugin.plugin_unique_identifier }}</span>
            </div>
            <div class="flex">
              <span class="w-28 text-muted-foreground">安装类型</span>
              <Badge :variant="plugin.install_type === 'local' ? 'default' : 'secondary'">
                {{ plugin.install_type }}
              </Badge>
            </div>
            <div class="flex">
              <span class="w-28 text-muted-foreground">引用次数</span>
              <span>{{ plugin.refers }}</span>
            </div>
            <div class="flex items-center">
              <span class="w-28 text-muted-foreground">是否推荐</span>
              <div class="flex items-center gap-2">
                <Badge :variant="plugin.is_recommended ? 'default' : 'outline'">
                  {{ plugin.is_recommended ? "是" : "否" }}
                </Badge>
                <Button variant="ghost" size="sm" @click="handleEdit">
                  <Pencil class="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
            <div class="flex items-center">
              <span class="w-28 text-muted-foreground">启用状态</span>
              <div class="flex items-center gap-2">
                <Badge :variant="plugin.is_enabled ? 'default' : 'secondary'">
                  {{ plugin.is_enabled ? "启用" : "禁用" }}
                </Badge>
                <Button variant="ghost" size="sm" @click="handleEdit">
                  <Pencil class="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
            <div class="flex">
              <span class="w-28 text-muted-foreground">创建时间</span>
              <span>{{ formatDate(plugin.created_at) }}</span>
            </div>
            <div class="flex">
              <span class="w-28 text-muted-foreground">更新时间</span>
              <span>{{ formatDate(plugin.updated_at) }}</span>
            </div>
          </div>
        </div>
      </Card>

      <!-- 声明内容卡 -->
      <Card class="flex min-h-0 flex-1 flex-col overflow-hidden p-5">
        <div class="flex items-center justify-between pb-3">
          <h3 class="font-medium">声明内容 (declaration)</h3>
          <div class="flex gap-2">
            <Button variant="outline" size="sm" @click="copyJson">
              <Copy class="mr-1 h-3.5 w-3.5" />
              复制
            </Button>
            <Button variant="outline" size="sm" @click="isJsonExpanded = !isJsonExpanded">
              {{ isJsonExpanded ? "折叠" : "展开" }}
            </Button>
          </div>
        </div>
        <div v-if="isJsonExpanded" class="min-h-0 flex-1 overflow-auto">
          <pre class="bg-muted/50 rounded-md p-4 text-xs font-mono whitespace-pre-wrap break-all">{{ jsonDisplay }}</pre>
        </div>
      </Card>
    </template>

    <!-- 空状态 -->
    <div v-else class="flex flex-1 items-center justify-center">
      <div class="text-muted-foreground">插件不存在</div>
    </div>
  </div>
</template>
```

- [ ] **步骤 2：运行 TypeScript 检查**

运行：`cd web/vue && pnpm check`

预期：无 TypeScript 错误

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue
git commit -m "feat(web): 新增插件定义详情页"
```

---

## 任务 7：前端编辑页

**文件：**
- 新增：`web/vue/src/tenant/pages/admin/PluginDefinitionEditPage.vue`

- [ ] **步骤 1：创建编辑页组件**

创建文件 `web/vue/src/tenant/pages/admin/PluginDefinitionEditPage.vue`：

```vue
<script setup lang="ts">
import { ArrowLeft } from "@lucide/vue";
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Button, Card, Badge } from "@/components";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { notifyError, notifySuccess } from "@/framework/utils/feedback";
import { getPluginDefinition, updatePluginDefinition } from "@/tenant/api/plugin";
import type { PluginDefinitionDetail } from "@/tenant/api/plugin";

const route = useRoute();
const router = useRouter();
const pluginId = route.params.id as string;

const loading = ref(true);
const saving = ref(false);
const plugin = ref<PluginDefinitionDetail | null>(null);

// 表单数据
const form = ref({
  is_recommended: false,
  is_enabled: true,
});

// 原始数据（用于比较是否修改）
const originalForm = ref({
  is_recommended: false,
  is_enabled: true,
});

// 是否有修改
const hasChanges = computed(() => {
  return (
    form.value.is_recommended !== originalForm.value.is_recommended ||
    form.value.is_enabled !== originalForm.value.is_enabled
  );
});

const loadPlugin = async () => {
  loading.value = true;
  try {
    const response = await getPluginDefinition(pluginId);
    if (response.data) {
      plugin.value = response.data;
      form.value.is_recommended = response.data.is_recommended;
      form.value.is_enabled = response.data.is_enabled;
      originalForm.value = { ...form.value };
    }
  } catch (error: any) {
    console.error("加载插件详情失败:", error);
    notifyError(error?.response?.data?.msg || "加载插件详情失败");
  } finally {
    loading.value = false;
  }
};

const handleBack = () => {
  router.push(`/admin/plugin-definitions/${pluginId}`);
};

const handleCancel = () => {
  router.push(`/admin/plugin-definitions/${pluginId}`);
};

const handleSave = async () => {
  if (!hasChanges.value) {
    notifyError("未修改任何内容");
    return;
  }

  saving.value = true;
  try {
    await updatePluginDefinition(pluginId, {
      is_recommended: form.value.is_recommended,
      is_enabled: form.value.is_enabled,
    });
    notifySuccess("保存成功");
    router.push(`/admin/plugin-definitions/${pluginId}`);
  } catch (error: any) {
    console.error("保存失败:", error);
    notifyError(error?.response?.data?.msg || "保存失败");
  } finally {
    saving.value = false;
  }
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleString();
};

onMounted(() => {
  loadPlugin();
});
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-edit-page">
    <!-- 页面标题区 -->
    <div class="flex items-center gap-3">
      <Button variant="ghost" size="sm" @click="handleBack">
        <ArrowLeft class="mr-1 h-4 w-4" />
        返回详情
      </Button>
      <h2 class="text-xl font-semibold">编辑插件状态</h2>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex flex-1 items-center justify-center">
      <div class="text-muted-foreground">加载中...</div>
    </div>

    <!-- 编辑表单 -->
    <template v-else-if="plugin">
      <!-- 基本信息卡 -->
      <Card class="p-5">
        <div class="space-y-4">
          <h3 class="font-medium">基本信息</h3>
          <div class="grid gap-3 text-sm">
            <div class="flex">
              <span class="w-28 text-muted-foreground">插件ID</span>
              <span class="font-mono">{{ plugin.plugin_id }}</span>
            </div>
            <div class="flex">
              <span class="w-28 text-muted-foreground">唯一标识</span>
              <span class="font-mono text-xs">{{ plugin.plugin_unique_identifier }}</span>
            </div>
            <div class="flex">
              <span class="w-28 text-muted-foreground">安装类型</span>
              <Badge :variant="plugin.install_type === 'local' ? 'default' : 'secondary'">
                {{ plugin.install_type }}
              </Badge>
            </div>
            <div class="flex">
              <span class="w-28 text-muted-foreground">引用次数</span>
              <span>{{ plugin.refers }}</span>
            </div>
          </div>
        </div>
      </Card>

      <!-- 状态设置卡 -->
      <Card class="p-5">
        <div class="space-y-4">
          <h3 class="font-medium">状态设置</h3>
          <div class="space-y-4">
            <div class="flex items-start gap-3">
              <Checkbox
                id="is_recommended"
                v-model:checked="form.is_recommended"
              />
              <div class="grid gap-1.5 leading-none">
                <Label for="is_recommended" class="cursor-pointer">是否推荐</Label>
                <p class="text-muted-foreground text-xs">将插件标记为推荐，在市场中优先展示</p>
              </div>
            </div>
            <div class="flex items-start gap-3">
              <Checkbox
                id="is_enabled"
                v-model:checked="form.is_enabled"
              />
              <div class="grid gap-1.5 leading-none">
                <Label for="is_enabled" class="cursor-pointer">启用状态</Label>
                <p class="text-muted-foreground text-xs">禁用后租户将无法安装此插件</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-2">
        <Button variant="outline" @click="handleCancel">取消</Button>
        <Button :disabled="!hasChanges || saving" @click="handleSave">
          {{ saving ? "保存中..." : "保存" }}
        </Button>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-else class="flex flex-1 items-center justify-center">
      <div class="text-muted-foreground">插件不存在</div>
    </div>
  </div>
</template>
```

- [ ] **步骤 2：运行 TypeScript 检查**

运行：`cd web/vue && pnpm check`

预期：无 TypeScript 错误

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginDefinitionEditPage.vue
git commit -m "feat(web): 新增插件定义编辑页"
```

---

## 任务 8：前端扫描目录页

**文件：**
- 新增：`web/vue/src/tenant/pages/admin/PluginScanPage.vue`

- [ ] **步骤 1：创建扫描目录页组件**

创建文件 `web/vue/src/tenant/pages/admin/PluginScanPage.vue`，实现三步骤流程：

```vue
<script setup lang="ts">
import { ArrowLeft, Check, X, Circle } from "@lucide/vue";
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { Button, Card, Input, Checkbox, Badge } from "@/components";
import { notifyError, notifySuccess } from "@/framework/utils/feedback";
import { scanDirectoryPreview, scanDirectoryForPlugins } from "@/tenant/api/plugin";
import type { ScannedPluginPreview } from "@/tenant/api/plugin";

const router = useRouter();

// 步骤状态
const currentStep = ref(0); // 0: 输入路径, 1: 预览选择, 2: 导入结果

// 第一步：输入路径
const directoryPath = ref("");
const recursive = ref(false);
const previewing = ref(false);

// 第二步：预览选择
const scannedPlugins = ref<ScannedPluginPreview[]>([]);
const selectedPluginIds = ref<Set<string>>(new Set());

// 第三步：导入结果
const importResults = ref<{
  success_count: number;
  skipped_count: number;
  failed_count: number;
  results: { plugin_id: string; version: string; status: string; message: string }[];
} | null>(null);

const importing = ref(false);

// 统计信息
const readyCount = computed(() => scannedPlugins.value.filter(p => p.status === "ready" && !p.exists).length);
const existsCount = computed(() => scannedPlugins.value.filter(p => p.exists).length);
const invalidCount = computed(() => scannedPlugins.value.filter(p => p.status === "invalid").length);

// 步骤配置
const steps = [
  { title: "输入路径", description: "输入服务器目录路径" },
  { title: "预览选择", description: "选择要导入的插件" },
  { title: "导入结果", description: "查看导入结果" },
];

const handleBack = () => {
  if (currentStep.value > 0) {
    currentStep.value--;
  } else {
    router.push("/admin/plugin-definitions");
  }
};

const handleNext = async () => {
  if (currentStep.value === 0) {
    // 第一步：验证并预览
    if (!directoryPath.value.trim()) {
      notifyError("请输入服务器目录路径");
      return;
    }

    previewing.value = true;
    try {
      const response = await scanDirectoryPreview({
        directory: directoryPath.value,
        recursive: recursive.value,
      });
      
      if (response.data) {
        scannedPlugins.value = response.data;
        // 默认选中所有可导入的插件
        selectedPluginIds.value = new Set(
          response.data.filter(p => p.status === "ready" && !p.exists).map(p => p.plugin_id)
        );
        currentStep.value = 1;
      }
    } catch (error: any) {
      console.error("预览失败:", error);
      notifyError(error?.response?.data?.msg || "预览失败");
    } finally {
      previewing.value = false;
    }
  }
};

const togglePlugin = (pluginId: string, exists: boolean, status: string) => {
  if (exists || status === "invalid") return;
  
  if (selectedPluginIds.value.has(pluginId)) {
    selectedPluginIds.value.delete(pluginId);
  } else {
    selectedPluginIds.value.add(pluginId);
  }
};

const handleConfirmImport = async () => {
  if (selectedPluginIds.value.size === 0) {
    notifyError("请至少选择一个插件");
    return;
  }

  importing.value = true;
  try {
    const response = await scanDirectoryForPlugins({
      directory: directoryPath.value,
      recursive: recursive.value,
      plugin_ids: Array.from(selectedPluginIds.value),
    });

    if (response.data) {
      importResults.value = {
        success_count: response.data.success_count,
        skipped_count: response.data.skipped_count,
        failed_count: response.data.failed_count,
        results: response.data.results,
      };
      currentStep.value = 2;
      notifySuccess("导入完成");
    }
  } catch (error: any) {
    console.error("导入失败:", error);
    notifyError(error?.response?.data?.msg || "导入失败");
  } finally {
    importing.value = false;
  }
};

const handleFinish = () => {
  router.push("/admin/plugin-definitions");
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-scan-page">
    <!-- 页面标题区 -->
    <div class="flex items-center gap-3">
      <Button variant="ghost" size="sm" @click="handleBack">
        <ArrowLeft class="mr-1 h-4 w-4" />
        返回列表
      </Button>
      <h2 class="text-xl font-semibold">扫描目录注册插件</h2>
    </div>

    <!-- 步骤指示器 -->
    <div class="flex items-center justify-center gap-2">
      <template v-for="(step, index) in steps" :key="index">
        <div class="flex items-center gap-2">
          <div
            :class="[
              'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium',
              currentStep === index
                ? 'bg-primary text-primary-foreground'
                : currentStep > index
                ? 'bg-primary/20 text-primary'
                : 'bg-muted text-muted-foreground'
            ]"
          >
            {{ index + 1 }}
          </div>
          <span :class="currentStep === index ? 'font-medium' : 'text-muted-foreground'">
            {{ step.title }}
          </span>
        </div>
        <div v-if="index < steps.length - 1" class="text-muted-foreground mx-2">──→</div>
      </template>
    </div>

    <!-- 第一步：输入路径 -->
    <Card v-if="currentStep === 0" class="flex-1 p-5">
      <div class="space-y-4">
        <div class="space-y-2">
          <label class="text-sm font-medium">服务器目录路径 *</label>
          <Input
            v-model="directoryPath"
            placeholder="例如：/path/to/plugins"
          />
        </div>
        <div class="flex items-center gap-2">
          <Checkbox id="recursive" v-model:checked="recursive" />
          <label for="recursive" class="text-sm cursor-pointer">递归扫描子目录</label>
        </div>
      </div>
    </Card>

    <!-- 第二步：预览选择 -->
    <Card v-else-if="currentStep === 1" class="flex min-h-0 flex-1 flex-col overflow-hidden p-5">
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <span class="text-muted-foreground text-sm">目录：</span>
            <span class="font-mono text-sm">{{ directoryPath }}</span>
          </div>
          <div class="text-sm">
            找到 {{ scannedPlugins.length }} 个插件，其中 {{ existsCount }} 个已存在
          </div>
        </div>

        <div class="text-sm">
          <span class="text-green-600">可导入: {{ readyCount }}</span>
          <span class="text-muted-foreground mx-2">|</span>
          <span class="text-amber-600">已存在: {{ existsCount }}</span>
          <span class="text-muted-foreground mx-2">|</span>
          <span class="text-red-600">解析失败: {{ invalidCount }}</span>
        </div>

        <div class="min-h-0 flex-1 overflow-auto border rounded-md">
          <table class="w-full text-sm">
            <thead class="bg-muted/50 sticky top-0">
              <tr>
                <th class="w-10 px-3 py-2"></th>
                <th class="px-3 py-2 text-left">插件ID</th>
                <th class="px-3 py-2 text-left">版本</th>
                <th class="px-3 py-2 text-left">名称</th>
                <th class="px-3 py-2 text-left">状态</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="plugin in scannedPlugins"
                :key="plugin.plugin_id"
                class="border-t hover:bg-muted/30 cursor-pointer"
                @click="togglePlugin(plugin.plugin_id, plugin.exists, plugin.status)"
              >
                <td class="px-3 py-2">
                  <Checkbox
                    v-if="!plugin.exists && plugin.status === 'ready'"
                    :checked="selectedPluginIds.has(plugin.plugin_id)"
                    @click.stop
                    @update:checked="togglePlugin(plugin.plugin_id, plugin.exists, plugin.status)"
                  />
                </td>
                <td class="px-3 py-2 font-mono">{{ plugin.plugin_id }}</td>
                <td class="px-3 py-2">{{ plugin.version }}</td>
                <td class="px-3 py-2">{{ plugin.name }}</td>
                <td class="px-3 py-2">
                  <Badge v-if="plugin.status === 'ready' && !plugin.exists" variant="default">可导入</Badge>
                  <Badge v-else-if="plugin.exists" variant="secondary">已存在</Badge>
                  <Badge v-else variant="destructive">解析失败</Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="text-sm text-muted-foreground">
          已选择 {{ selectedPluginIds.size }} 个插件
        </div>
      </div>
    </Card>

    <!-- 第三步：导入结果 -->
    <Card v-else-if="currentStep === 2" class="flex-1 p-5">
      <div v-if="importResults" class="space-y-4">
        <div class="text-lg font-medium">导入完成</div>
        
        <div class="flex gap-6 text-sm">
          <div><Check class="inline h-4 w-4 text-green-600 mr-1" />成功: {{ importResults.success_count }}</div>
          <div><Circle class="inline h-4 w-4 text-amber-600 mr-1" />跳过: {{ importResults.skipped_count }}</div>
          <div><X class="inline h-4 w-4 text-red-600 mr-1" />失败: {{ importResults.failed_count }}</div>
        </div>

        <div class="border rounded-md overflow-auto max-h-60">
          <table class="w-full text-sm">
            <thead class="bg-muted/50">
              <tr>
                <th class="px-3 py-2 text-left">插件ID</th>
                <th class="px-3 py-2 text-left">版本</th>
                <th class="px-3 py-2 text-left">状态</th>
                <th class="px-3 py-2 text-left">说明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="result in importResults.results" :key="result.plugin_id" class="border-t">
                <td class="px-3 py-2 font-mono">{{ result.plugin_id }}</td>
                <td class="px-3 py-2">{{ result.version }}</td>
                <td class="px-3 py-2">
                  <Badge v-if="result.status === 'success'" variant="default">成功</Badge>
                  <Badge v-else-if="result.status === 'skipped'" variant="secondary">跳过</Badge>
                  <Badge v-else variant="destructive">失败</Badge>
                </td>
                <td class="px-3 py-2 text-muted-foreground">{{ result.message }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Card>

    <!-- 操作按钮 -->
    <div class="flex justify-end gap-2">
      <template v-if="currentStep === 0">
        <Button variant="outline" @click="router.push('/admin/plugin-definitions')">取消</Button>
        <Button :disabled="previewing" @click="handleNext">
          {{ previewing ? "预览中..." : "下一步" }}
        </Button>
      </template>
      <template v-else-if="currentStep === 1">
        <Button variant="outline" @click="currentStep = 0">上一步</Button>
        <Button variant="outline" @click="router.push('/admin/plugin-definitions')">取消</Button>
        <Button :disabled="importing || selectedPluginIds.size === 0" @click="handleConfirmImport">
          {{ importing ? "导入中..." : "确认导入" }}
        </Button>
      </template>
      <template v-else>
        <Button @click="handleFinish">返回列表</Button>
      </template>
    </div>
  </div>
</template>
```

- [ ] **步骤 2：运行 TypeScript 检查**

运行：`cd web/vue && pnpm check`

预期：无 TypeScript 错误

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginScanPage.vue
git commit -m "feat(web): 新增插件扫描目录页"
```

---

## 任务 9：前端上传插件页

**文件：**
- 新增：`web/vue/src/tenant/pages/admin/PluginUploadPage.vue`

- [ ] **步骤 1：创建上传插件页组件**

创建文件 `web/vue/src/tenant/pages/admin/PluginUploadPage.vue`：

```vue
<script setup lang="ts">
import { ArrowLeft, Upload, Check, AlertCircle, Info } from "@lucide/vue";
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { Button, Card, Checkbox, Badge } from "@/components";
import { notifyError, notifySuccess } from "@/framework/utils/feedback";
import { parsePluginPackage, uploadPluginPackage } from "@/tenant/api/plugin";
import type { ParsedPluginInfo } from "@/tenant/api/plugin";

const router = useRouter();

// 步骤状态
const currentStep = ref(0); // 0: 上传文件, 1: 预览确认, 2: 注册结果

// 第一步：上传文件
const selectedFile = ref<File | null>(null);
const overwrite = ref(false);
const parsing = ref(false);

// 第二步：预览确认
const parsedInfo = ref<ParsedPluginInfo | null>(null);

// 第三步：注册结果
const registerResult = ref<{
  plugin_id: string;
  version: string;
  plugin_unique_identifier: string;
} | null>(null);

const registering = ref(false);

// 步骤配置
const steps = [
  { title: "上传文件", description: "选择插件包文件" },
  { title: "预览确认", description: "确认插件信息" },
  { title: "注册结果", description: "查看注册结果" },
];

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0];
  }
};

const handleDrop = (event: DragEvent) => {
  event.preventDefault();
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    const file = event.dataTransfer.files[0];
    if (file.name.endsWith(".zip")) {
      selectedFile.value = file;
    } else {
      notifyError("请上传 .zip 格式的插件包");
    }
  }
};

const handleDragOver = (event: DragEvent) => {
  event.preventDefault();
};

const handleBack = () => {
  if (currentStep.value > 0) {
    currentStep.value--;
    if (currentStep.value === 0) {
      // 重置状态
      selectedFile.value = null;
      parsedInfo.value = null;
    }
  } else {
    router.push("/admin/plugin-definitions");
  }
};

const handleNext = async () => {
  if (currentStep.value === 0) {
    // 第一步：解析插件包
    if (!selectedFile.value) {
      notifyError("请选择插件包文件");
      return;
    }

    parsing.value = true;
    try {
      const response = await parsePluginPackage(selectedFile.value);
      if (response.data) {
        parsedInfo.value = response.data;
        currentStep.value = 1;
      }
    } catch (error: any) {
      console.error("解析失败:", error);
      notifyError(error?.response?.data?.msg || "插件包解析失败");
    } finally {
      parsing.value = false;
    }
  }
};

const handleConfirmRegister = async () => {
  if (!selectedFile.value) return;

  // 检查是否已存在且未勾选覆盖
  if (parsedInfo.value?.exists && !overwrite.value) {
    notifyError("插件已存在，如需覆盖请勾选覆盖选项");
    return;
  }

  registering.value = true;
  try {
    const response = await uploadPluginPackage(selectedFile.value, overwrite.value);
    if (response.data) {
      registerResult.value = {
        plugin_id: response.data.plugin_id,
        version: response.data.version,
        plugin_unique_identifier: response.data.plugin_unique_identifier,
      };
      currentStep.value = 2;
      notifySuccess("插件注册成功");
    }
  } catch (error: any) {
    console.error("注册失败:", error);
    notifyError(error?.response?.data?.msg || "插件注册失败");
  } finally {
    registering.value = false;
  }
};

const handleFinish = () => {
  router.push("/admin/plugin-definitions");
};
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4" data-testid="plugin-upload-page">
    <!-- 页面标题区 -->
    <div class="flex items-center gap-3">
      <Button variant="ghost" size="sm" @click="handleBack">
        <ArrowLeft class="mr-1 h-4 w-4" />
        返回列表
      </Button>
      <h2 class="text-xl font-semibold">上传插件包</h2>
    </div>

    <!-- 步骤指示器 -->
    <div class="flex items-center justify-center gap-2">
      <template v-for="(step, index) in steps" :key="index">
        <div class="flex items-center gap-2">
          <div
            :class="[
              'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium',
              currentStep === index
                ? 'bg-primary text-primary-foreground'
                : currentStep > index
                ? 'bg-primary/20 text-primary'
                : 'bg-muted text-muted-foreground'
            ]"
          >
            {{ index + 1 }}
          </div>
          <span :class="currentStep === index ? 'font-medium' : 'text-muted-foreground'">
            {{ step.title }}
          </span>
        </div>
        <div v-if="index < steps.length - 1" class="text-muted-foreground mx-2">──→</div>
      </template>
    </div>

    <!-- 第一步：上传文件 -->
    <Card v-if="currentStep === 0" class="flex-1 p-5">
      <div class="space-y-4">
        <div
          class="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer hover:border-primary/50 transition-colors"
          @drop="handleDrop"
          @dragover="handleDragOver"
          @click="($refs.fileInput as HTMLInputElement).click()"
        >
          <Upload class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p class="text-muted-foreground mb-2">拖拽 .zip 文件到此处</p>
          <p class="text-muted-foreground text-sm">或 <span class="text-primary underline">点击选择文件</span></p>
          <input
            ref="fileInput"
            type="file"
            accept=".zip"
            class="hidden"
            @change="handleFileSelect"
          />
        </div>

        <div v-if="selectedFile" class="flex items-center gap-2 text-sm">
          <Check class="h-4 w-4 text-green-600" />
          <span>{{ selectedFile.name }}</span>
        </div>

        <div class="flex items-center gap-2">
          <Checkbox id="overwrite" v-model:checked="overwrite" />
          <label for="overwrite" class="text-sm cursor-pointer">覆盖已存在的插件定义</label>
        </div>
      </div>
    </Card>

    <!-- 第二步：预览确认 -->
    <Card v-else-if="currentStep === 1" class="flex-1 p-5">
      <div v-if="parsedInfo" class="space-y-4">
        <div class="text-muted-foreground text-sm">
          文件：<span class="font-mono">{{ selectedFile?.name }}</span>
        </div>

        <div class="border rounded-md p-4 space-y-3">
          <div class="flex">
            <span class="w-28 text-muted-foreground">插件ID</span>
            <span class="font-mono">{{ parsedInfo.plugin_id }}</span>
          </div>
          <div class="flex">
            <span class="w-28 text-muted-foreground">版本</span>
            <span>{{ parsedInfo.version }}</span>
          </div>
          <div class="flex">
            <span class="w-28 text-muted-foreground">名称</span>
            <span>{{ parsedInfo.name }}</span>
          </div>
          <div class="flex">
            <span class="w-28 text-muted-foreground">描述</span>
            <span>{{ parsedInfo.description || "--" }}</span>
          </div>
          <div class="flex">
            <span class="w-28 text-muted-foreground">类型</span>
            <span>{{ parsedInfo.manifest_type || "--" }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-28 text-muted-foreground">状态</span>
            <Badge v-if="parsedInfo.exists" variant="secondary">
              <AlertCircle class="mr-1 h-3 w-3" />
              该插件ID已存在
            </Badge>
            <Badge v-else variant="default">可注册</Badge>
          </div>
        </div>

        <div v-if="parsedInfo.exists && !overwrite" class="flex items-start gap-2 bg-amber-50 dark:bg-amber-950/20 rounded-md p-3 text-sm">
          <Info class="h-4 w-4 text-amber-600 mt-0.5" />
          <span>插件已存在，勾选"覆盖"后将更新现有定义</span>
        </div>
      </div>
    </Card>

    <!-- 第三步：注册结果 -->
    <Card v-else-if="currentStep === 2" class="flex-1 p-5">
      <div v-if="registerResult" class="space-y-4">
        <div class="flex items-center gap-2 text-lg font-medium text-green-600">
          <Check class="h-5 w-5" />
          插件注册成功
        </div>

        <div class="border rounded-md p-4 space-y-3">
          <div class="flex">
            <span class="w-28 text-muted-foreground">插件ID</span>
            <span class="font-mono">{{ registerResult.plugin_id }}</span>
          </div>
          <div class="flex">
            <span class="w-28 text-muted-foreground">版本</span>
            <span>{{ registerResult.version }}</span>
          </div>
          <div class="flex">
            <span class="w-28 text-muted-foreground">唯一标识</span>
            <span class="font-mono text-xs">{{ registerResult.plugin_unique_identifier }}</span>
          </div>
        </div>
      </div>
    </Card>

    <!-- 操作按钮 -->
    <div class="flex justify-end gap-2">
      <template v-if="currentStep === 0">
        <Button variant="outline" @click="router.push('/admin/plugin-definitions')">取消</Button>
        <Button :disabled="!selectedFile || parsing" @click="handleNext">
          {{ parsing ? "解析中..." : "下一步" }}
        </Button>
      </template>
      <template v-else-if="currentStep === 1">
        <Button variant="outline" @click="currentStep = 0">上一步</Button>
        <Button variant="outline" @click="router.push('/admin/plugin-definitions')">取消</Button>
        <Button :disabled="registering" @click="handleConfirmRegister">
          {{ registering ? "注册中..." : "确认注册" }}
        </Button>
      </template>
      <template v-else>
        <Button @click="handleFinish">返回列表</Button>
      </template>
    </div>
  </div>
</template>
```

- [ ] **步骤 2：运行 TypeScript 检查**

运行：`cd web/vue && pnpm check`

预期：无 TypeScript 错误

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginUploadPage.vue
git commit -m "feat(web): 新增插件上传页面"
```

---

## 任务 10：前端列表页修改

**文件：**
- 修改：`web/vue/src/tenant/pages/admin/PluginDefinitionList.vue`

- [ ] **步骤 1：修改行操作按钮**

将现有的 `columns` 定义中的 `actions` 列替换为：

```typescript
{
  id: "actions",
  header: "操作",
  size: 220,
  cell: ({ row }) => {
    const plugin = row.original;
    return h("div", { class: "flex items-center gap-1" }, [
      h(
        Button,
        { variant: "ghost", size: "sm", onClick: () => handleDetail(plugin) },
        () => [h(Eye, { class: "mr-1 h-3.5 w-3.5" }), "详情"]
      ),
      h(
        Button,
        {
          variant: "ghost",
          size: "sm",
          onClick: () => handleToggleEnabled(plugin),
        },
        () => [plugin.is_enabled ? "禁用" : "启用"]
      ),
      h(
        Button,
        { variant: "ghost", size: "sm", onClick: () => handleEdit(plugin) },
        () => [h(Pencil, { class: "mr-1 h-3.5 w-3.5" }), "编辑"]
      ),
      h(
        Button,
        {
          variant: "ghost",
          size: "sm",
          class: "text-destructive hover:text-destructive",
          onClick: () => handleDelete(plugin),
        },
        () => [h(Trash2, { class: "mr-1 h-3.5 w-3.5" }), "删除"]
      ),
    ]);
  },
},
```

- [ ] **步骤 2：修改事件处理函数**

将现有的处理函数修改为：

```typescript
// 查看详情
const handleDetail = (row: PluginDefinition) => {
  router.push(`/admin/plugin-definitions/${row.id}`);
};

// 编辑
const handleEdit = (row: PluginDefinition) => {
  router.push(`/admin/plugin-definitions/${row.id}/edit`);
};

// 启用/禁用切换
const handleToggleEnabled = async (row: PluginDefinition) => {
  const newStatus = !row.is_enabled;
  const action = newStatus ? "启用" : "禁用";

  if (!(await confirmAction(`确定要${action}插件 "${row.plugin_id}" 吗？`))) return;

  try {
    await updatePluginDefinition(row.id, { is_enabled: newStatus });
    notifySuccess(`插件已${action}`);
    dataTable.refresh();
    loadStats();
  } catch (error: any) {
    console.error(`${action}失败:`, error);
    const errorMessage = error?.response?.data?.msg || error?.message || `${action}失败`;
    notifyError(errorMessage);
  }
};
```

- [ ] **步骤 3：添加缺失的导入**

确保文件顶部有 `updatePluginDefinition` 导入：

```typescript
import {
  deletePluginDefinition,
  getPluginDefinitions,
  getPluginStatistics,
  updatePluginDefinition,  // 新增
} from "@/tenant/api/plugin";
```

- [ ] **步骤 4：修改顶部按钮事件**

修改"扫描目录"和"上传插件"按钮的点击事件：

```vue
<Button variant="outline" data-testid="scan-btn" @click="router.push('/admin/plugin-definitions/scan')">
  <FolderSearch class="mr-1 h-4 w-4" />
  扫描目录
</Button>
<Button variant="outline" data-testid="upload-btn" @click="router.push('/admin/plugin-definitions/upload')">
  <Upload class="mr-1 h-4 w-4" />
  上传插件
</Button>
```

- [ ] **步骤 5：运行 TypeScript 检查**

运行：`cd web/vue && pnpm check`

预期：无 TypeScript 错误

- [ ] **步骤 6：Commit**

```bash
git add web/vue/src/tenant/pages/admin/PluginDefinitionList.vue
git commit -m "feat(web): 完善插件定义列表页行操作"
```

---

## 任务 11：集成测试

- [ ] **步骤 1：启动后端服务**

运行：`cd server/python && uv run python manage.py runserver`

预期：服务启动成功

- [ ] **步骤 2：启动前端开发服务器**

运行：`cd web/vue && pnpm dev`

预期：前端启动成功

- [ ] **步骤 3：功能测试**

手动测试以下功能：

1. **列表页**：
   - 点击"详情"按钮，跳转到详情页
   - 点击"启用/禁用"按钮，切换状态
   - 点击"编辑"按钮，跳转到编辑页
   - 点击"扫描目录"按钮，跳转到扫描页
   - 点击"上传插件"按钮，跳转到上传页

2. **详情页**：
   - 显示插件基本信息
   - 显示声明内容 JSON
   - 点击"编辑"按钮，跳转到编辑页
   - 点击"返回列表"按钮，返回列表页

3. **编辑页**：
   - 修改推荐/启用状态
   - 点击"保存"按钮，保存成功后返回详情页

4. **扫描目录页**：
   - 输入目录路径，点击"下一步"
   - 预览插件列表，选择插件
   - 点击"确认导入"，查看导入结果

5. **上传插件页**：
   - 选择 .zip 文件，点击"下一步"
   - 预览插件信息，点击"确认注册"
   - 查看注册结果

- [ ] **步骤 4：最终 Commit**

```bash
git add -A
git commit -m "feat: 完成插件定义管理功能实现"
```

---

## 自检清单

**1. 规格覆盖度：**
- [x] 后端：扫描预览 API（任务 3）
- [x] 后端：插件包解析 API（任务 3）
- [x] 后端：Schema 类型（任务 1）
- [x] 后端：Service 方法（任务 2）
- [x] 前端：API 类型和函数（任务 4）
- [x] 前端：路由配置（任务 5）
- [x] 前端：详情页（任务 6）
- [x] 前端：编辑页（任务 7）
- [x] 前端：扫描目录页（任务 8）
- [x] 前端：上传插件页（任务 9）
- [x] 前端：列表页修改（任务 10）

**2. 占位符扫描：** 无"待定"、"TODO"等占位符

**3. 类型一致性：**
- 后端 Schema 与前端类型定义一致
- API 路径与函数调用一致
- 路由参数与页面使用一致
