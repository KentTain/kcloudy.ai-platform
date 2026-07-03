<script setup lang="ts">
/**
 * PermissionList — 权限管理页面
 *
 * 布局：
 * - 左侧：权限列表（300px 固定宽度）
 * - 右侧：Tabs（角色列表、菜单列表）
 */

import { ref, computed, onMounted, onUnmounted, h } from "vue"
import type { ColumnDef } from "@tanstack/vue-table"
import {
  Shield,
  Users,
  Menu,
  Settings,
} from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  Skeleton,
  DataTable,
  useDataTable,
} from "@/components"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components"
import { Checkbox, Input } from "@/components"
import { notifySuccess, notifyError, getErrorMessage } from "@/framework/utils/feedback"
import type { Permission, Role, PermissionGroup, MenuTreeNode } from "@/iam/types"
import { getPermissions } from "@/iam/api/permission"
import {
  getRoles,
  getRolePermissions,
  assignRolePermissions,
} from "@/iam/api/role"
import { getMenus } from "@/iam/api/menu"

// ========== 状态 ==========

const isUnmounted = ref(false)
const loading = ref(false)
const permissions = ref<Permission[]>([])
const menus = ref<MenuTreeNode[]>([])

// 当前选中的权限
const selectedPermission = ref<Permission | null>(null)

// Tabs
const activeTab = ref("roles")

// 分配权限弹窗
const assignDialogOpen = ref(false)
const currentRole = ref<Role | null>(null)
const selectedPermissionIds = ref<string[]>([])
const assignLoading = ref(false)

// 权限搜索（弹窗内）
const permSearchKeyword = ref("")

// ========== 计算属性 ==========

// 按资源分组的权限（弹窗内使用）
const permissionGroups = computed<PermissionGroup[]>(() => {
  const groups: Map<string, Permission[]> = new Map()

  for (const p of permissions.value) {
    const resource = p.resource
    if (!groups.has(resource)) {
      groups.set(resource, [])
    }
    groups.get(resource)!.push(p)
  }

  return Array.from(groups.entries()).map(([resource, perms]) => ({
    resource,
    permissions: perms,
  }))
})

// 筛选后的权限组（弹窗内）
const filteredPermissionGroups = computed(() => {
  if (!permSearchKeyword.value.trim()) {
    return permissionGroups.value
  }

  const keyword = permSearchKeyword.value.toLowerCase()
  return permissionGroups.value
    .map((g) => ({
      ...g,
      permissions: g.permissions.filter(
        (p) =>
          p.name.toLowerCase().includes(keyword) ||
          p.code.toLowerCase().includes(keyword) ||
          p.resource.toLowerCase().includes(keyword)
      ),
    }))
    .filter((g) => g.permissions.length > 0)
})

// ========== 角色列表 DataTable ==========

const roleColumns: ColumnDef<Role>[] = [
  {
    accessorKey: "name",
    header: "角色名称",
    size: 120,
    cell: ({ row }) => h("span", { class: "font-medium" }, row.original.name),
  },
  {
    accessorKey: "code",
    header: "角色编码",
    size: 120,
    cell: ({ row }) => h("span", { class: "font-mono text-sm" }, row.original.code),
  },
  {
    accessorKey: "description",
    header: "描述",
    cell: ({ row }) => row.original.description || "--",
  },
  {
    id: "actions",
    header: "操作",
    size: 120,
    cell: ({ row }) => {
      const role = row.original
      return h(
        Button,
        {
          variant: "outline",
          size: "sm",
          onClick: () => handleAssignPermissions(role),
        },
        () => [h(Settings, { class: "mr-1 h-3.5 w-3.5" }), "分配权限"]
      )
    },
  },
]

const roleTable = useDataTable<Role>({
  columns: roleColumns,
  remoteFetchFn: async ({ page, page_size }) => {
    const response = await getRoles({ page, page_size })
    return response
  },
})

// ========== 菜单列表 DataTable ==========

interface MenuFlatItem {
  id: string
  name: string
  code: string
  path: string
  icon: string
  sort_order: number
  parent_id: string | null
  tree_level: number
}

const menuColumns: ColumnDef<MenuFlatItem>[] = [
  {
    accessorKey: "name",
    header: "菜单名称",
    size: 180,
    cell: ({ row }) => {
      const item = row.original
      const indent = item.tree_level * 20
      return h("div", { class: "flex items-center gap-2", style: { paddingLeft: `${indent}px` } }, [
        h(Menu, { class: "h-4 w-4 text-muted-foreground shrink-0" }),
        h("span", { class: "font-medium" }, item.name),
      ])
    },
  },
  {
    accessorKey: "code",
    header: "菜单编码",
    size: 120,
    cell: ({ row }) => h("span", { class: "font-mono text-sm" }, row.original.code),
  },
  {
    accessorKey: "path",
    header: "路径",
    cell: ({ row }) => h("span", { class: "text-sm text-muted-foreground" }, row.original.path || "--"),
  },
  {
    accessorKey: "sort_order",
    header: "排序",
    size: 80,
    cell: ({ row }) => row.original.sort_order,
  },
]

const menuTable = useDataTable<MenuFlatItem>({
  columns: menuColumns,
  remoteFetchFn: async () => {
    const items = flattenMenus(menus.value)
    return {
      code: 200,
      msg: "ok",
      data: items,
      total: items.length,
      page: 1,
      page_size: items.length || 10,
    }
  },
  enabled: () => activeTab.value === "menus",
})

/** 扁平化菜单树 */
function flattenMenus(menuList: MenuTreeNode[], level = 0): MenuFlatItem[] {
  const result: MenuFlatItem[] = []
  for (const menu of menuList) {
    result.push({
      id: menu.id,
      name: menu.name,
      code: menu.code || "",
      path: menu.path || "",
      icon: menu.icon || "",
      sort_order: menu.tree_sort || 0,
      parent_id: menu.parent_id,
      tree_level: level,
    })
    if (menu.children && menu.children.length > 0) {
      result.push(...flattenMenus(menu.children, level + 1))
    }
  }
  return result
}

// ========== 方法 ==========

/** 加载数据 */
async function loadData() {
  loading.value = true
  try {
    const [permRes, menusRes] = await Promise.all([
      getPermissions({ page: 1, page_size: 1000 }),
      getMenus(),
    ])
    if (isUnmounted.value) return
    // 权限 API 直接返回数组
    permissions.value = permRes.data || []
    menus.value = menusRes.data?.menus || []
    // 默认选中第一个权限
    if (permissions.value.length > 0 && !selectedPermission.value) {
      selectedPermission.value = permissions.value[0]
    }
    // 角色列表由 DataTable 自动加载
    await roleTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "加载数据失败"))
  } finally {
    loading.value = false
  }
}

/** 选择权限 */
function selectPermission(perm: Permission) {
  selectedPermission.value = perm
}

/** 打开分配权限弹窗 */
async function handleAssignPermissions(role: Role) {
  currentRole.value = role
  assignDialogOpen.value = true

  // 加载角色已有权限
  try {
    const res = await getRolePermissions(role.id)
    selectedPermissionIds.value = (res.data || []).map((p: Permission) => p.id)
  } catch {
    selectedPermissionIds.value = []
  }
}

/** 切换权限选中 */
function togglePermission(permId: string) {
  const index = selectedPermissionIds.value.indexOf(permId)
  if (index > -1) {
    selectedPermissionIds.value.splice(index, 1)
  } else {
    selectedPermissionIds.value.push(permId)
  }
}

/** 提交权限分配 */
async function handleAssignSubmit() {
  if (!currentRole.value) return

  assignLoading.value = true
  try {
    await assignRolePermissions(currentRole.value.id, { permission_ids: selectedPermissionIds.value })
    notifySuccess("权限分配成功")
    assignDialogOpen.value = false
  } catch (error) {
    notifyError(getErrorMessage(error, "权限分配失败"))
  } finally {
    assignLoading.value = false
  }
}

// 初始化
onMounted(() => {
  loadData()
})

// 清理
onUnmounted(() => {
  isUnmounted.value = true
})
</script>

<template>
  <AppPage title="权限管理" variant="workbench" description="管理系统权限、角色和菜单">
    <div class="flex gap-4 flex-1 min-h-0">
      <!-- 左侧：权限列表 -->
      <div
        class="w-[300px] min-h-0 shrink-0 flex flex-col border rounded-lg overflow-hidden bg-card"
        data-testid="permission-list"
      >
        <div class="p-3 border-b bg-muted/30">
          <span class="text-sm font-medium">权限列表</span>
        </div>

        <ScrollArea class="min-h-0 flex-1">
          <div v-if="loading" class="p-3 space-y-2" data-testid="permission-loading">
            <Skeleton v-for="i in 6" :key="i" class="h-10 w-full" />
          </div>

          <div v-else-if="permissions.length === 0" class="p-4 text-center text-muted-foreground text-sm" data-testid="permission-empty">
            暂无权限数据
          </div>

          <div v-else class="py-1" data-testid="permission-items">
            <button
              v-for="perm in permissions"
              :key="perm.id"
              class="flex items-center w-full px-3 py-2.5 text-sm hover:bg-accent transition-colors text-left"
              :class="{ 'bg-accent': selectedPermission?.id === perm.id }"
              :data-testid="`permission-item-${perm.id}`"
              @click="selectPermission(perm)"
            >
              <Shield class="h-4 w-4 mr-2 shrink-0 text-blue-500" />
              <div class="flex-1 min-w-0">
                <div class="font-medium truncate" data-testid="permission-item-name">{{ perm.name }}</div>
                <div class="text-xs text-muted-foreground" data-testid="permission-item-code">{{ perm.code }}</div>
              </div>
            </button>
          </div>
        </ScrollArea>
      </div>

      <!-- 右侧：Tabs -->
      <div class="flex-1 flex flex-col border rounded-lg overflow-hidden bg-card">
        <template v-if="!selectedPermission">
          <div class="flex-1 flex items-center justify-center text-muted-foreground">
            <div class="text-center">
              <Shield class="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>请从左侧选择一个权限</p>
            </div>
          </div>
        </template>

        <template v-else>
          <!-- 权限详情头部 -->
          <div class="p-4 border-b bg-muted/30" data-testid="permission-detail">
            <div class="flex items-start justify-between">
              <div>
                <h2 class="text-lg font-semibold" data-testid="permission-detail-name">{{ selectedPermission.name }}</h2>
                <div class="text-sm text-muted-foreground mt-1">
                  <span class="font-mono" data-testid="permission-detail-code">{{ selectedPermission.code }}</span>
                  <span class="mx-2">·</span>
                  <span data-testid="permission-detail-resource">{{ selectedPermission.resource }}</span>
                  <span class="mx-2">·</span>
                  <Badge variant="outline" class="text-xs" data-testid="permission-detail-action">{{ selectedPermission.action }}</Badge>
                </div>
              </div>
            </div>
          </div>

          <!-- Tabs 内容 -->
          <Tabs v-model="activeTab" class="flex-1 flex flex-col" data-testid="permission-tabs">
            <div class="px-4 pt-2 border-b">
              <TabsList>
                <TabsTrigger value="roles" data-testid="permission-tab-roles">
                  <Users class="h-4 w-4 mr-1" />
                  角色列表
                </TabsTrigger>
                <TabsTrigger value="menus" data-testid="permission-tab-menus">
                  <Menu class="h-4 w-4 mr-1" />
                  菜单列表
                </TabsTrigger>
              </TabsList>
            </div>

            <ScrollArea class="flex-1">
              <!-- 角色列表 Tab -->
              <TabsContent value="roles" class="p-4 m-0" data-testid="permission-roles-content">
                <div class="mb-3 flex items-center justify-between">
                  <span class="text-sm text-muted-foreground" data-testid="permission-roles-count">
                    共 {{ roleTable.table.getRowCount() }} 个角色
                  </span>
                </div>
                <DataTable :data-table="roleTable" :fixed-layout="true" />
              </TabsContent>

              <!-- 菜单列表 Tab -->
              <TabsContent value="menus" class="p-4 m-0" data-testid="permission-menus-content">
                <div class="mb-3 flex items-center justify-between">
                  <span class="text-sm text-muted-foreground" data-testid="permission-menus-count">
                    共 {{ menuTable.table.getRowCount() }} 个菜单
                  </span>
                </div>
                <DataTable :data-table="menuTable" :fixed-layout="true" />
              </TabsContent>
            </ScrollArea>
          </Tabs>
        </template>
      </div>
    </div>

    <!-- 分配权限弹窗 -->
    <Dialog v-model:open="assignDialogOpen">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>分配权限</DialogTitle>
          <DialogDescription>
            为角色「{{ currentRole?.name }}」分配权限
          </DialogDescription>
        </DialogHeader>

        <div class="mb-3">
          <div class="relative">
            <Shield class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              v-model="permSearchKeyword"
              placeholder="搜索权限..."
              class="pl-8"
            />
          </div>
        </div>

        <ScrollArea class="h-[400px] pr-4">
          <div v-for="group in filteredPermissionGroups" :key="group.resource" class="mb-4">
            <h4 class="font-medium text-sm mb-2 flex items-center gap-2">
              <Shield class="h-4 w-4" />
              {{ group.resource }}
            </h4>
            <div class="space-y-1 pl-6">
              <div
                v-for="perm in group.permissions"
                :key="perm.id"
                class="flex items-center gap-2 py-1"
              >
                <Checkbox
                  :checked="selectedPermissionIds.includes(perm.id)"
                  @update:checked="togglePermission(perm.id)"
                />
                <div class="flex-1 min-w-0">
                  <span class="text-sm">{{ perm.name }}</span>
                  <Badge variant="outline" class="ml-2 text-xs">{{ perm.action }}</Badge>
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" @click="assignDialogOpen = false">
            取消
          </Button>
          <Button :disabled="assignLoading" @click="handleAssignSubmit">
            {{ assignLoading ? "保存中..." : "确定" }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>
