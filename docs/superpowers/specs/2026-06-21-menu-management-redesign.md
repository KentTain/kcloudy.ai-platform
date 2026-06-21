# 菜单管理页面改造设计

## 概述

参照 `OrganizationPage.vue` 的左右布局设计，改造 `MenuList.vue` 页面，右侧增加 Tabs 结构，支持展示菜单基本信息和关联权限列表。

## 目标

- 调整页面布局为左右结构：左侧菜单树 + 右侧详情 Tabs
- 右侧 Tabs 包含：菜单基本信息、权限列表
- 新增后端 API 支持获取菜单关联权限

## 功能范围

| 功能 | 说明 |
|------|------|
| 菜单树 | 保持现有功能，支持搜索、选中高亮 |
| 菜单信息 Tab | 使用 DescriptionList 展示菜单属性 |
| 权限列表 Tab | 使用 DataTable 展示关联权限（只读） |
| 菜单权限 API | 新增后端接口获取单个菜单的权限列表 |

## 架构设计

### 前端组件结构

```
MenuList.vue
├── 左侧：菜单树（Card 容器）
│   ├── 搜索框
│   └── MenuTree 组件
└── 右侧：详情区（Card 容器）
    ├── 头部：菜单名称 + 编码
    └── Tabs
        ├── Tab 1：菜单信息（DescriptionList）
        └── Tab 2：权限列表（DataTable）
```

### 后端 API

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 获取菜单权限 | GET | `/iam/admin/v1/menus/{menu_id}/permissions` | 返回该菜单关联的权限列表 |

### 数据流

```
用户选择菜单节点
    ↓
更新 selectedMenuId
    ↓
并行加载：
  ├── 菜单详情（已有，从树数据获取）
  └── 权限列表（调用新 API）
    ↓
渲染右侧 Tabs
```

## 详细设计

### 1. 前端改造

#### 1.1 MenuList.vue 结构调整

**当前结构：**
```vue
<Card> 左侧菜单树 </Card>
<Card> 右侧菜单详情（静态卡片）</Card>
```

**改造后结构：**
```vue
<div class="flex gap-4 h-[calc(100vh-200px)]">
  <!-- 左侧：菜单树 -->
  <Card class="w-[300px] shrink-0">
    <div class="p-3 border-b">
      <Input v-model="searchKeyword" placeholder="搜索菜单..." />
    </div>
    <ScrollArea class="flex-1">
      <MenuTree :menus="filteredMenus" @select="handleMenuSelect" />
    </ScrollArea>
  </Card>

  <!-- 右侧：详情 + Tabs -->
  <Card class="flex-1 flex flex-col">
    <template v-if="selectedMenu">
      <!-- 头部信息 -->
      <div class="p-4 border-b">
        <h2>{{ selectedMenu.name }}</h2>
        <p>编码：{{ selectedMenu.code }}</p>
      </div>

      <!-- Tabs -->
      <Tabs v-model="activeTab" class="flex-1 flex flex-col">
        <TabsList>
          <TabsTrigger value="info">菜单信息</TabsTrigger>
          <TabsTrigger value="permissions">权限列表</TabsTrigger>
        </TabsList>

        <ScrollArea class="flex-1">
          <TabsContent value="info">
            <DescriptionList :items="infoItems" :columns="2" bordered />
          </TabsContent>
          <TabsContent value="permissions">
            <DataTable :data-table="permissionTable" />
          </TabsContent>
        </ScrollArea>
      </Tabs>
    </template>

    <!-- 未选中状态 -->
    <div v-else class="flex-1 flex items-center justify-center">
      <div class="text-center text-muted-foreground">
        <FolderOpen class="h-12 w-12 mx-auto mb-2" />
        <p>请选择左侧菜单查看详情</p>
      </div>
    </div>
  </Card>
</div>
```

#### 1.2 新增状态和方法

```typescript
// Tab 状态
const activeTab = ref('info')

// 权限列表
const permissions = ref<Permission[]>([])
const permissionsLoading = ref(false)

// 加载菜单权限
async function loadMenuPermissions(menuId: string) {
  permissionsLoading.value = true
  try {
    const res = await getMenuPermissions(menuId)
    permissions.value = res.data || []
  } catch (error) {
    notifyError(getErrorMessage(error, '加载权限列表失败'))
    permissions.value = []
  } finally {
    permissionsLoading.value = false
  }
}

// 菜单信息描述项
const infoItems = computed<DescriptionItem[]>(() => {
  const menu = selectedMenu.value
  if (!menu) return []
  return [
    { label: '菜单名称', value: menu.name },
    { label: '菜单编码', value: menu.code },
    { label: '路由路径', value: menu.path || '--' },
    { label: '所属模块', value: menu.module },
    { label: '图标', value: menu.icon || '未设置' },
    { label: '是否可见', value: menu.is_visible ? '可见' : '隐藏' },
    { label: '排序号', value: String(menu.tree_sort) },
    { label: '层级', value: `第 ${menu.tree_level} 级` },
  ]
})
```

#### 1.3 DataTable 列定义

```typescript
const permissionColumns: ColumnDef<Permission>[] = [
  {
    accessorKey: 'name',
    header: '权限名称',
    size: 160,
    cell: ({ row }) => h('span', { class: 'font-medium' }, row.original.name),
  },
  {
    accessorKey: 'code',
    header: '权限编码',
    size: 140,
    cell: ({ row }) => h('span', { class: 'font-mono text-sm' }, row.original.code),
  },
  {
    accessorKey: 'resource',
    header: '资源',
    size: 100,
  },
  {
    accessorKey: 'action',
    header: '操作',
    size: 80,
  },
  {
    accessorKey: 'description',
    header: '描述',
    size: 200,
    cell: ({ row }) => row.original.description || '--',
  },
]
```

### 2. 前端 API 封装

**文件：** `web/vue/src/iam/api/menu.ts`

```typescript
/**
 * 获取菜单关联的权限列表
 */
export const getMenuPermissions = (menuId: string) =>
  get<ApiResponse<Permission[]>>(`/iam/admin/v1/menus/${menuId}/permissions`)
```

### 3. 后端 API 实现

#### 3.1 路由定义

**文件：** `server/python/src/iam/controllers/admin/menu_controller.py`

```python
@router.get("/menus/{menu_id}/permissions")
async def get_menu_permissions(
    menu_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    获取菜单关联的权限列表

    Args:
        menu_id: 菜单 ID

    Returns:
        权限列表
    """
    permissions = await menu_service.get_menu_permissions(session, menu_id)
    return ApiResponse.success(data=permissions)
```

#### 3.2 服务层实现

**文件：** `server/python/src/iam/services/menu_service.py`

```python
async def get_menu_permissions(
    self, session: AsyncSession, menu_id: str
) -> list[Permission]:
    """
    获取菜单关联的权限列表

    Args:
        session: 数据库会话
        menu_id: 菜单 ID

    Returns:
        权限列表
    """
    # 查询菜单权限关联
    stmt = (
        select(PermissionModel)
        .join(MenuPermission, PermissionModel.id == MenuPermission.permission_id)
        .where(MenuPermission.menu_id == menu_id)
        .order_by(PermissionModel.resource, PermissionModel.action)
    )
    result = await session.execute(stmt)
    permissions = result.scalars().all()

    # 转换为 Schema
    return [Permission.model_validate(p) for p in permissions]
```

#### 3.3 Schema 定义

**文件：** `server/python/src/iam/schemas/permission.py`（已存在）

```python
class Permission(BaseModel):
    """权限信息"""
    id: str
    code: str
    name: str
    resource: str
    action: str
    description: Optional[str] = None
    created_at: str
```

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 菜单无关联权限 | 显示空状态提示「该菜单暂无关联权限」 |
| API 请求失败 | 显示错误提示，权限列表置空 |
| 菜单不存在 | 返回 404 错误 |

## 测试计划

### 单元测试

| 测试项 | 文件位置 |
|--------|---------|
| 前端 API 调用 | `tests/iam/unit/api/menu.test.ts` |
| DataTable 列定义 | `tests/iam/unit/pages/MenuList.test.ts` |

### 集成测试

| 测试项 | 文件位置 |
|--------|---------|
| 后端 API 端点 | `tests/iam/unit/controllers/menu_controller.test.ts` |
| 服务层查询 | `tests/iam/unit/services/menu_service.test.ts` |

### E2E 测试

| 测试项 | 文件位置 |
|--------|---------|
| 页面交互流程 | `tests/iam/e2e/menu-list.spec.ts` |

## 实现顺序

1. **后端 API** — 新增 `get_menu_permissions` 端点
2. **前端 API 封装** — 在 `menu.ts` 添加函数
3. **页面改造** — 重构 `MenuList.vue` 布局和 Tabs
4. **测试** — 编写单元测试和 E2E 测试

## 参考文件

- 参照页面：`web/vue/src/iam/pages/organizations/OrganizationPage.vue`
- 当前实现：`web/vue/src/iam/pages/menus/MenuList.vue`
- 后端控制器：`server/python/src/iam/controllers/admin/menu_controller.py`
- 后端服务：`server/python/src/iam/services/menu_service.py`
