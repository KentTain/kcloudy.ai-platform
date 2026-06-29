# 插件定义管理功能设计规格

**日期**: 2026-06-29
**状态**: 待实现

## 概述

为插件定义列表页面实现完整的管理功能，包括详情查看、状态编辑、启用/禁用切换、扫描目录注册和上传插件注册。

## 需求确认

| 功能 | 实现方式 |
|------|----------|
| 详情 | 独立页面模式 |
| 编辑 | 仅修改推荐/启用状态 |
| 启用/禁用 | 列表页行操作按钮 |
| 扫描目录 | 预览+选择模式（需后端支持预览） |
| 上传插件 | 预览+确认模式（需后端支持预览） |

## 后端 API 设计

### 新增预览 API

#### 扫描预览 API

```
POST /tenant/admin/v1/plugin-definitions/scan/preview
```

**请求参数**:
```json
{
  "directory": "/path/to/plugins",
  "recursive": false
}
```

**响应**:
```json
{
  "code": 200,
  "data": [
    {
      "plugin_id": "author/name",
      "version": "1.0.0",
      "name": "插件名称",
      "description": "插件描述",
      "exists": false,
      "status": "ready",
      "error_message": null
    }
  ]
}
```

**字段说明**:
- `exists`: 该插件 ID 是否已在系统中注册
- `status`: `ready`（可导入）、`invalid`（解析失败）

---

#### 插件包解析 API

```
POST /tenant/admin/v1/plugin-definitions/parse
```

**请求**: `multipart/form-data`
- `file`: 插件包 .zip 文件

**响应**:
```json
{
  "code": 200,
  "data": {
    "plugin_id": "author/name",
    "version": "1.0.0",
    "name": "插件名称",
    "description": "插件描述",
    "manifest_type": "mcp",
    "declaration": { ... },
    "exists": false
  }
}
```

---

#### 现有 API 调整

**扫描确认 API** (`POST /plugin-definitions/scan`) 新增参数:
- `plugin_ids`: 指定要导入的插件 ID 列表

---

### 后端 Schema 新增

```python
# tenant/schemas/plugin.py

class ScannedPluginPreview(BaseModel):
    """扫描预览结果"""
    plugin_id: str
    version: str
    name: str
    description: str
    exists: bool
    status: Literal["ready", "invalid"]
    error_message: str | None = None


class ParsedPluginInfo(BaseModel):
    """解析插件结果"""
    plugin_id: str
    version: str
    name: str
    description: str
    manifest_type: str | None
    declaration: dict
    exists: bool


class ScanDirectoryConfirmRequest(BaseModel):
    """扫描确认请求"""
    directory: str
    recursive: bool = False
    plugin_ids: list[str]  # 指定要导入的插件ID
```

---

## 前端页面结构

### 页面文件

```
src/tenant/pages/admin/
├── PluginDefinitionList.vue          # 列表页（修改）
├── PluginDefinitionDetailPage.vue    # 详情页（新增）
├── PluginDefinitionEditPage.vue      # 编辑页（新增）
├── PluginScanPage.vue                # 扫描目录页（新增）
└── PluginUploadPage.vue              # 上传插件页（新增）
```

### 路由配置

```typescript
// web/vue/src/tenant/router/index.ts

// 在 adminRoutes 的 children 数组中添加/修改以下路由
// 注意：/scan 和 /upload 需放在 /:id 之前，避免被动态路由匹配

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

---

## 详情页设计

### 页面布局

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回列表    插件详情                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 基本信息                                             │ │
│ │ 插件ID: author/name                                  │ │
│ │ 唯一标识: author/name:1.0.0@abc123                   │ │
│ │ 安装类型: local                                      │ │
│ │ 引用次数: 5                                          │ │
│ │ 是否推荐: 是 [编辑]                                   │ │
│ │ 启用状态: 启用 [编辑]                                 │ │
│ │ 创建时间: 2026-06-29 10:00:00                        │ │
│ │ 更新时间: 2026-06-29 12:00:00                        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 声明内容 (declaration)                               │ │
│ │ ┌─────────────────────────────────────────────────┐ │ │
│ │ │ {                                                │ │ │
│ │ │   "configuration": { ... },                     │ │ │
│ │ │   "tools_configuration": [ ... ],               │ │ │
│ │ │   "models_configuration": [ ... ]               │ │ │
│ │ │ }                                                │ │ │
│ │ └─────────────────────────────────────────────────┘ │ │
│ │                                    [复制] [折叠/展开] │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 功能说明

| 区域 | 功能 |
|------|------|
| 顶部导航 | 返回列表按钮 |
| 基本信息卡 | 展示插件元信息，推荐/启用状态旁有编辑按钮 |
| 声明内容卡 | JSON 格式展示 declaration 字段，支持复制和折叠 |
| 编辑状态 | 点击编辑按钮跳转到编辑页 |

---

## 列表页修改设计

### 行操作按钮调整

现有按钮：详情、编辑、删除

调整为：详情、启用/禁用、编辑、删除

```
┌─────────────────────────────────────────────────────────────────────┐
│ 操作                                                                │
├─────────────────────────────────────────────────────────────────────┤
│ [详情] [禁用] [编辑] [删除]    ← 启用状态时显示"禁用"按钮            │
│ [详情] [启用] [编辑] [删除]    ← 禁用状态时显示"启用"按钮            │
└─────────────────────────────────────────────────────────────────────┘
```

### 功能变更

| 按钮 | 现状 | 修改后 |
|------|------|--------|
| 详情 | 跳转错误路由 | 跳转到详情页 `/admin/plugin-definitions/:pluginId` |
| 启用/禁用 | 不存在 | 新增，点击后调用 API 切换状态 |
| 编辑 | 弹出"开发中"提示 | 跳转到编辑页 `/admin/plugin-definitions/:pluginId/edit` |
| 删除 | 已实现 | 保持不变 |

---

## 编辑页设计

### 页面布局

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回详情    编辑插件状态                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 基本信息                                             │ │
│ │                                                     │ │
│ │ 插件ID        author/name                           │ │
│ │ 唯一标识      author/name:1.0.0@abc123               │ │
│ │ 安装类型      local                                  │ │
│ │ 引用次数      5                                      │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 状态设置                                             │ │
│ │                                                     │ │
│ │ ☑ 是否推荐                                          │ │
│ │   将插件标记为推荐，在市场中优先展示                 │ │
│ │                                                     │ │
│ │ ☑ 启用状态                                          │ │
│ │   禁用后租户将无法安装此插件                         │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│                              [取消]  [保存]             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 扫描目录页设计

### 第一步：输入路径

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回列表    扫描目录注册插件                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ① 输入路径  ──→  ② 预览选择  ──→  ③ 导入结果        │
│      ●●●           ○○○            ○○○                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 服务器目录路径 *                                        │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ /path/to/plugins                                    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ☐ 递归扫描子目录                                        │
│                                                         │
│                              [取消]  [下一步]           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 第二步：预览选择

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回列表    扫描目录注册插件                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ① 输入路径  ──→  ② 预览选择  ──→  ③ 导入结果        │
│      ○○○           ●●●            ○○○                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ 目录: /path/to/plugins                                  │
│                                                         │
│ 找到 5 个插件，其中 2 个已存在                           │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ☑ author/plugin-a  v1.0.0  [可导入]                 │ │
│ │ ☑ author/plugin-b  v2.0.0  [可导入]                 │ │
│ │ ☐ author/plugin-c  v1.5.0  [已存在]                 │ │
│ │ ☑ author/plugin-d  v0.9.0  [可导入]                 │ │
│ │ ☐ author/plugin-e  v0.1.0  [解析失败]               │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ 已选择 3 个插件                                         │
│                                                         │
│              [上一步]  [取消]  [确认导入]               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 第三步：导入结果

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回列表    扫描目录注册插件                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ① 输入路径  ──→  ② 预览选择  ──→  ③ 导入结果        │
│      ○○○           ○○○            ●●●                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 导入完成                                                │
│                                                         │
│ ✓ 成功: 2                                               │
│ ⊘ 跳过: 0                                               │
│ ✗ 失败: 1                                               │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ author/plugin-a  v1.0.0  ✓ 成功                     │ │
│ │ author/plugin-b  v2.0.0  ✓ 成功                     │ │
│ │ author/plugin-d  v0.9.0  ✗ 解析失败: 缺少配置       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│                              [返回列表]                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 上传插件页设计

### 第一步：上传文件

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回列表    上传插件包                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ① 上传文件  ──→  ② 预览确认  ──→  ③ 注册结果        │
│      ●●●           ○○○            ○○○                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │                                                     │ │
│ │         拖拽 .zip 文件到此处                        │ │
│ │              或 [点击选择文件]                       │ │
│ │                                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ☐ 覆盖已存在的插件定义                                  │
│                                                         │
│                              [取消]  [下一步]           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 第二步：预览确认

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回列表    上传插件包                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ① 上传文件  ──→  ② 预览确认  ──→  ③ 注册结果        │
│      ○○○           ●●●            ○○○                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 文件: plugin-package.zip                                │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 插件ID:    author/name                              │ │
│ │ 版本:      1.0.0                                    │ │
│ │ 名称:      插件名称                                 │ │
│ │ 描述:      插件描述文字                             │ │
│ │ 类型:      mcp                                      │ │
│ │ 状态:      ⚠ 该插件ID已存在                        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ℹ 插件已存在，勾选"覆盖"后将更新现有定义                │
│                                                         │
│              [上一步]  [取消]  [确认注册]               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 第三步：注册结果

```
┌─────────────────────────────────────────────────────────┐
│ ← 返回列表    上传插件包                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ① 上传文件  ──→  ② 预览确认  ──→  ③ 注册结果        │
│      ○○○           ○○○            ●●●                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│         ✓ 插件注册成功                                  │
│                                                         │
│ 插件ID: author/name                                     │
│ 版本:   1.0.0                                           │
│ 唯一标识: author/name:1.0.0@abc123                       │
│                                                         │
│                              [返回列表]                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 数据流与状态管理

### 前端 API 层新增

```typescript
// src/tenant/api/plugin.ts

// 扫描预览
export const scanDirectoryPreview = (data: ScanDirectoryRequest) =>
  rawPost<ApiResponse<ScannedPluginPreview[]>>('/tenant/admin/v1/plugin-definitions/scan/preview', data);

// 插件包解析
export const parsePluginPackage = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return rawPost<ApiResponse<ParsedPluginInfo>>('/tenant/admin/v1/plugin-definitions/parse', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
```

### 类型定义新增

```typescript
// src/tenant/api/plugin.ts

// 扫描预览结果
export interface ScannedPluginPreview {
  plugin_id: string;
  version: string;
  name: string;
  description: string;
  exists: boolean;
  status: 'ready' | 'invalid';
  error_message?: string;
}

// 解析插件结果
export interface ParsedPluginInfo {
  plugin_id: string;
  version: string;
  name: string;
  description: string;
  manifest_type: string;
  declaration: Record<string, any>;
  exists: boolean;
}

// 扫描确认请求（扩展）
export interface ScanDirectoryConfirmRequest {
  directory: string;
  recursive?: boolean;
  plugin_ids: string[];
}
```

---

## 错误处理与边界情况

### 前端错误处理

| 场景 | 处理方式 |
|------|----------|
| 目录不存在 | 提示"目录不存在: xxx"，停留在第一步 |
| 目录无 .zip 文件 | 提示"未找到插件包文件"，停留在第一步 |
| 解析失败 | 在预览列表中标记"解析失败"，显示错误原因 |
| 插件已存在 | 在预览列表中标记"已存在"，默认不勾选 |
| 导入部分失败 | 第三步显示详细结果，成功/跳过/失败计数 |
| 网络错误 | 统一使用 `notifyError` 提示错误信息 |

### 后端错误处理

| 场景 | HTTP 状态码 | 错误信息 |
|------|-------------|----------|
| 目录不存在 | 400 | `"目录不存在: xxx"` |
| 路径不是目录 | 400 | `"路径不是目录: xxx"` |
| 插件包格式错误 | 400 | `"插件包解析失败: xxx"` |
| 插件定义已存在 | 409 | `"插件定义已存在: xxx"` |
| 插件被引用无法删除 | 409 | `"无法删除，有 N 个租户正在使用此插件"` |

### 交互细节

**扫描目录页面：**
- 第一步：点击"下一步"时验证目录路径不为空
- 第二步：至少选择一个插件才能点击"确认导入"
- 已存在的插件默认不勾选，不可更改为勾选状态
- 解析失败的插件不显示复选框

**上传插件页面：**
- 第一步：必须选择 .zip 文件才能点击"下一步"
- 第二步：如果插件已存在且未勾选"覆盖"，点击"确认注册"时提示错误

**编辑页面：**
- 至少修改一个字段才能点击"保存"
- 保存成功后返回详情页

---

## 实现范围

### 后端

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `tenant/controllers/admin/plugin_controller.py` | 修改 | 新增预览 API 端点 |
| `tenant/services/plugin_definition_service.py` | 修改 | 新增预览服务方法 |
| `tenant/schemas/plugin.py` | 修改 | 新增 Schema 类型 |
| `tenant/services/plugin_package_service.py` | 修改 | 新增解析方法（如需要） |

### 前端

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `web/vue/src/tenant/pages/admin/PluginDefinitionList.vue` | 修改 | 调整行操作按钮 |
| `web/vue/src/tenant/pages/admin/PluginDefinitionDetailPage.vue` | 新增 | 详情页 |
| `web/vue/src/tenant/pages/admin/PluginDefinitionEditPage.vue` | 新增 | 编辑页 |
| `web/vue/src/tenant/pages/admin/PluginScanPage.vue` | 新增 | 扫描目录页 |
| `web/vue/src/tenant/pages/admin/PluginUploadPage.vue` | 新增 | 上传插件页 |
| `web/vue/src/tenant/router/index.ts` | 修改 | 新增路由 |
| `web/vue/src/tenant/api/plugin.ts` | 修改 | 新增 API 函数和类型 |
