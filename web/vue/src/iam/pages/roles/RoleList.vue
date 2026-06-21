<script setup lang="ts">
/**
 * RoleList — 角色管理页面
 *
 * 布局：
 * - 左侧：角色列表（300px 固定宽度）
 * - 右侧：Tabs（角色成员、权限列表）
 */

import { ref, computed, onMounted, onUnmounted, h } from "vue"
import type { ColumnDef } from "@tanstack/vue-table"
import {
  Shield,
  Users,
  Plus,
  Pencil,
  Trash2,
  Settings,
  UserPlus,
  X,
  ChevronRight,
  ChevronDown,
  Menu,
  Package,
} from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  Skeleton,
  Checkbox,
  DataTable,
  useDataTable,
  PeopleSelectDialog,
  Input,
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
import { confirmAction, notifySuccess, notifyError, getErrorMessage } from "@/framework/utils/feedback"
import type { Role, Permission, PermissionGroup, RoleMember, MenuTreeNode } from "@/iam/types"
import type { OrgTreeNode, PeopleItem } from "@/components/common/feedback/people-select"
import {
  getRoles,
  getRolePermissions,
  getRoleMembers,
  addRoleMembers,
  removeRoleMember,
  assignRolePermissions,
  createRole,
  updateRole,
  deleteRole,
} from "@/iam/api/role"
import { getPermissions } from "@/iam/api/permission"
import { getMenus } from "@/iam/api/menu"
import { getOrganizationTree, getOrganizationMembers } from "@/iam/api/organization"
import { getUsers } from "@/iam/api/user"

// ========== 类型定义 ==========

/** 权限树节点 - 模块级 */
interface PermissionModule {
  name: string
  label: string
  resources: PermissionResource[]
  expanded: boolean
}

/** 权限树节点 - 资源级 */
interface PermissionResource {
  name: string
  permissions: Permission[]
  expanded: boolean
}

// ========== 状态 ==========

const isUnmounted = ref(false)
const loading = ref(false)
const roles = ref<Role[]>([])
const selectedRole = ref<Role | null>(null)
const activeTab = ref("members")

// 角色权限
const allPermissions = ref<Permission[]>([])
const rolePermissions = ref<Permission[]>([])
const menus = ref<MenuTreeNode[]>([])

// 权限树展开状态
const moduleExpandState = ref<Map<string, boolean>>(new Map())
const resourceExpandState = ref<Map<string, boolean>>(new Map())

// 弹窗
const addMemberDialogOpen = ref(false)
const assignPermDialogOpen = ref(false)
const selectedPermIds = ref<string[]>([])

// 创建/编辑弹窗
const formDialogOpen = ref(false)
const formDialogMode = ref<"create" | "edit">("create")
const formValues = ref({ code: "", name: "", description: "" })
const formSubmitting = ref(false)

// 权限搜索
const permSearchKeyword = ref("")

// ========== 计算属性 ==========

/** 构建三级权限树：模块 → 资源 → 权限 */
const permissionTree = computed<PermissionModule[]>(() => {
  // 如果没有权限数据，返回空数组
  if (allPermissions.value.length === 0) {
    return []
  }

  // 模块标签映射
  const moduleLabels: Record<string, string> = {
    iam: "身份认证",
    ai: "AI 服务",
    tenant: "租户管理",
    通用: "通用权限",
  }

  // 推断资源所属模块
  function inferModule(resource: string): string {
    const r = resource.toLowerCase()
    if (r.includes("user") || r.includes("role") || r.includes("permission") || r.includes("org") || r.includes("menu")) {
      return "iam"
    }
    if (r.includes("chat") || r.includes("conversation") || r.includes("model") || r.includes("message")) {
      return "ai"
    }
    if (r.includes("tenant") || r.includes("module") || r.includes("config") || r.includes("resource")) {
      return "tenant"
    }
    return "通用"
  }

  // 按资源分组权限
  const resourceMap = new Map<string, Permission[]>()
  for (const perm of allPermissions.value) {
    const resource = perm.resource
    if (!resourceMap.has(resource)) {
      resourceMap.set(resource, [])
    }
    resourceMap.get(resource)!.push(perm)
  }

  // 按模块组织资源
  const moduleMap = new Map<string, PermissionResource[]>()
  for (const [resourceName, perms] of resourceMap) {
    const moduleName = inferModule(resourceName)
    if (!moduleMap.has(moduleName)) {
      moduleMap.set(moduleName, [])
    }
    moduleMap.get(moduleName)!.push({
      name: resourceName,
      permissions: perms,
      expanded: resourceExpandState.value.get(resourceName) ?? false,
    })
  }

  // 构建树结构
  const modules: PermissionModule[] = []
  for (const [moduleName, resources] of moduleMap) {
    modules.push({
      name: moduleName,
      label: moduleLabels[moduleName] || moduleName,
      resources,
      expanded: moduleExpandState.value.get(moduleName) ?? false,
    })
  }

  return modules
})

/** 筛选后的权限树 */
const filteredPermissionTree = computed(() => {
  if (!permSearchKeyword.value.trim()) {
    return permissionTree.value
  }

  const keyword = permSearchKeyword.value.toLowerCase()

  return permissionTree.value
    .map((module) => {
      const filteredResources = module.resources
        .map((resource) => {
          const filteredPerms = resource.permissions.filter(
            (p) =>
              p.name.toLowerCase().includes(keyword) ||
              p.code.toLowerCase().includes(keyword) ||
              p.resource.toLowerCase().includes(keyword)
          )
          if (filteredPerms.length === 0) return null
          return { ...resource, permissions: filteredPerms }
        })
        .filter((r): r is PermissionResource => r !== null)

      if (filteredResources.length === 0) return null
      return { ...module, resources: filteredResources }
    })
    .filter((m): m is PermissionModule => m !== null)
})

/** 角色权限 ID 集合 */
const rolePermissionIds = computed(() => new Set(rolePermissions.value.map((p) => p.id)))

/** 角色权限树（只包含角色拥有的权限） */
const rolePermissionTree = computed<PermissionModule[]>(() => {
  if (rolePermissions.value.length === 0) return []

  const rolePermIds = rolePermissionIds.value

  return permissionTree.value
    .map(module => {
      const resources = module.resources
        .map(resource => {
          const permissions = resource.permissions.filter(p => rolePermIds.has(p.id))
          if (permissions.length === 0) return null
          return { ...resource, permissions }
        })
        .filter((r): r is PermissionResource => r !== null)

      if (resources.length === 0) return null
      return { ...module, resources }
    })
    .filter((m): m is PermissionModule => m !== null)
})

// ========== 旧的计算属性（兼容弹窗搜索）==========

// 按资源分组权限
const permissionGroups = computed<PermissionGroup[]>(() => {
  const groups: Map<string, Permission[]> = new Map()

  for (const p of allPermissions.value) {
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

// 筛选后的权限组
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

// ========== 角色成员 DataTable ==========

// 列定义
const memberColumns: ColumnDef<RoleMember>[] = [
  {
    accessorKey: "nickname",
    header: "姓名",
    size: 120,
    cell: ({ row }) => h("span", { class: "font-medium" }, row.original.nickname || row.original.username),
  },
  {
    accessorKey: "username",
    header: "账号",
    size: 120,
    cell: ({ row }) => h("span", { class: "font-mono text-sm" }, row.original.username),
  },
  {
    accessorKey: "email",
    header: "邮箱",
    cell: ({ row }) => row.original.email || "--",
  },
  {
    accessorKey: "phone",
    header: "手机",
    size: 120,
    cell: ({ row }) => row.original.phone || "--",
  },
  {
    accessorKey: "status",
    header: "状态",
    size: 80,
    cell: ({ row }) => {
      const status = row.original.status
      return h(
        Badge,
        { variant: status === "active" ? "default" : "secondary" },
        () => status === "active" ? "启用" : "停用"
      )
    },
  },
  {
    id: "actions",
    header: "操作",
    size: 100,
    cell: ({ row }) => {
      const member = row.original
      return h(
        Button,
        {
          variant: "ghost",
          size: "sm",
          class: "text-destructive hover:text-destructive",
          onClick: () => handleRemoveMember(member),
        },
        () => [h(X, { class: "h-3.5 w-3.5 mr-1" }), "移除"]
      )
    },
  },
]

// DataTable 初始化
const memberTable = useDataTable<RoleMember>({
  columns: memberColumns,
  remoteFetchFn: async () => {
    if (!selectedRole.value) {
      return { code: 200, msg: "ok", data: [], total: 0, page: 1, page_size: 10 }
    }
    const res = await getRoleMembers(selectedRole.value.id)
    const items = res.data ?? []
    return {
      ...res,
      data: items,
      total: res.total ?? items.length,
      page: res.page ?? 1,
      page_size: res.page_size ?? (items.length || 10),
    }
  },
  enabled: () => !!selectedRole.value && activeTab.value === "members",
})

// ========== 方法 ==========

/** 加载角色列表 */
async function loadRoles() {
  loading.value = true
  try {
    const res = await getRoles({ page: 1, page_size: 100 })
    if (isUnmounted.value) return
    roles.value = res.data || []
    // 默认选中第一个角色
    if (roles.value.length > 0 && !selectedRole.value) {
      await selectRole(roles.value[0])
    }
  } catch (error) {
    if (isUnmounted.value) return
    notifyError(getErrorMessage(error, "加载角色列表失败"))
  } finally {
    loading.value = false
  }
}

/** 选择角色 */
async function selectRole(role: Role) {
  selectedRole.value = role
  activeTab.value = "members"
  // 成员列表由 DataTable 自动加载（enabled 条件触发）
  if (isUnmounted.value) return
  // 同时加载权限数据和菜单数据（权限列表 Tab 需要）
  await Promise.all([loadRolePermissions(), loadAllPermissions(), loadMenus()])
}

/** 加载角色权限 */
async function loadRolePermissions() {
  if (!selectedRole.value) return
  try {
    const res = await getRolePermissions(selectedRole.value.id)
    if (isUnmounted.value) return
    rolePermissions.value = res.data || []
  } catch {
    rolePermissions.value = []
  }
}

/** 加载所有权限 */
async function loadAllPermissions() {
  try {
    const res = await getPermissions({ page: 1, page_size: 1000 })
    // 权限 API 直接返回数组
    allPermissions.value = res.data || []
  } catch {
    allPermissions.value = []
  }
}

/** 加载菜单 */
async function loadMenus() {
  if (menus.value.length > 0) return
  try {
    const res = await getMenus()
    menus.value = res.data?.menus || []
  } catch {
    menus.value = []
  }
}

/** 切换模块展开 */
function toggleModule(moduleName: string) {
  const currentState = moduleExpandState.value.get(moduleName) ?? false
  moduleExpandState.value.set(moduleName, !currentState)
}

/** 切换资源展开 */
function toggleResource(resourceName: string) {
  const currentState = resourceExpandState.value.get(resourceName) ?? false
  resourceExpandState.value.set(resourceName, !currentState)
}

/** 添加成员 */
async function handleAddMembers(userIds: string[]) {
  if (!selectedRole.value || userIds.length === 0) return
  try {
    const res = await addRoleMembers(selectedRole.value.id, userIds)
    notifySuccess(`成功添加 ${res.data?.added || 0} 个成员`)
    addMemberDialogOpen.value = false
    await memberTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "添加成员失败"))
  }
}

/** 移除成员 */
async function handleRemoveMember(user: { user_id: string; username: string; nickname?: string }) {
  if (!selectedRole.value) return
  if (!await confirmAction(`确定要移除成员「${user.nickname || user.username}」吗？`)) return
  try {
    await removeRoleMember(selectedRole.value.id, user.user_id)
    notifySuccess("已移除成员")
    await memberTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "移除成员失败"))
  }
}

/** 打开分配权限弹窗 */
async function handleOpenAssignPerm() {
  if (!selectedRole.value) return

  // 确保权限数据已加载
  await Promise.all([loadAllPermissions(), loadMenus()])

  // 确保角色权限已加载
  if (rolePermissions.value.length === 0) {
    await loadRolePermissions()
  }

  // 设置已选权限（确保类型一致）
  selectedPermIds.value = rolePermissions.value.map((p) => String(p.id))

  // 自动展开包含已选权限的模块和资源
  const rolePermIds = new Set(selectedPermIds.value)

  for (const module of permissionTree.value) {
    for (const resource of module.resources) {
      if (resource.permissions.some(p => rolePermIds.has(String(p.id)))) {
        moduleExpandState.value.set(module.name, true)
        resourceExpandState.value.set(resource.name, true)
      }
    }
  }

  assignPermDialogOpen.value = true
}

/** 切换权限选中 */
function togglePermission(permId: string | number) {
  const id = String(permId)
  const index = selectedPermIds.value.indexOf(id)
  if (index > -1) {
    selectedPermIds.value.splice(index, 1)
  } else {
    selectedPermIds.value.push(id)
  }
}

/** 提交权限分配 */
async function handleAssignPermSubmit() {
  if (!selectedRole.value) return
  try {
    await assignRolePermissions(selectedRole.value.id, { permission_ids: selectedPermIds.value })
    notifySuccess("权限分配成功")
    assignPermDialogOpen.value = false
    await loadRolePermissions()
  } catch (error) {
    notifyError(getErrorMessage(error, "权限分配失败"))
  }
}

/** 创建角色 */
function handleCreate() {
  formDialogMode.value = "create"
  formValues.value = { code: "", name: "", description: "" }
  formDialogOpen.value = true
}

/** 编辑角色 */
function handleEdit() {
  if (!selectedRole.value) return
  formDialogMode.value = "edit"
  formValues.value = {
    code: selectedRole.value.code,
    name: selectedRole.value.name,
    description: selectedRole.value.description || "",
  }
  formDialogOpen.value = true
}

/** 提交表单 */
async function handleFormSubmit() {
  if (!formValues.value.name || !formValues.value.code) {
    notifyError("角色名称和编码不能为空")
    return
  }

  formSubmitting.value = true
  try {
    if (formDialogMode.value === "edit" && selectedRole.value) {
      await updateRole(selectedRole.value.id, {
        name: formValues.value.name,
        description: formValues.value.description,
      })
      notifySuccess("更新成功")
    } else {
      await createRole({
        code: formValues.value.code,
        name: formValues.value.name,
        description: formValues.value.description,
      })
      notifySuccess("创建成功")
    }
    formDialogOpen.value = false
    await loadRoles()
  } catch (error) {
    notifyError(getErrorMessage(error, "操作失败"))
  } finally {
    formSubmitting.value = false
  }
}

/** 删除角色 */
async function handleDelete() {
  if (!selectedRole.value) return
  if (selectedRole.value.is_system) {
    notifyError("系统内置角色无法删除")
    return
  }
  if (!await confirmAction(`确定要删除角色「${selectedRole.value.name}」吗？`)) return
  try {
    await deleteRole(selectedRole.value.id)
    notifySuccess("删除成功")
    selectedRole.value = null
    await loadRoles()
  } catch (error) {
    notifyError(getErrorMessage(error, "删除失败"))
  }
}

// PeopleSelect 回调函数
async function loadOrgNodesCallback(): Promise<OrgTreeNode[]> {
  try {
    const res = await getOrganizationTree()
    function toNodes(depts: any[]): OrgTreeNode[] {
      return depts.map((d) => ({
        id: d.id,
        name: d.name,
        code: d.code,
        parent_id: d.parent_id,
        has_user_num: d.direct_member_count || 0,
        has_org_num: d.children?.length || 0,
        tree_leaf: !d.children || d.children.length === 0,
        children: d.children ? toNodes(d.children) : undefined,
      }))
    }
    return toNodes(res.data || [])
  } catch {
    return []
  }
}

async function searchPeopleCallback(keyword: string): Promise<PeopleItem[]> {
  try {
    const res = await getUsers({ keyword, page: 1, page_size: 100 })
    return (res.data || []).map((u) => ({
      user_id: u.id,
      username: u.username,
      nickname: u.nickname,
      email: u.email,
      phone: u.phone,
      status: u.status,
    }))
  } catch {
    return []
  }
}

async function loadOrgPeopleCallback(orgId: string): Promise<PeopleItem[]> {
  try {
    const res = await getOrganizationMembers(orgId)
    return (res.data || []) as unknown as PeopleItem[]
  } catch {
    return []
  }
}

// 初始化
onMounted(() => {
  loadRoles()
  loadMenus()
})

// 清理
onUnmounted(() => {
  isUnmounted.value = true
})
</script>

<template>
  <AppPage title="角色管理" variant="workbench" description="管理系统角色、成员和权限">
    <div class="flex gap-4 flex-1 min-h-0">
      <!-- 左侧：角色列表 -->
      <div class="w-[300px] shrink-0 flex flex-col border rounded-lg overflow-hidden bg-card">
        <div class="p-3 border-b bg-muted/30 flex items-center justify-between">
          <span class="text-sm font-medium">角色列表</span>
          <Button size="sm" @click="handleCreate">
            <Plus class="h-3.5 w-3.5 mr-1" />
            新建
          </Button>
        </div>

        <ScrollArea class="flex-1">
          <div v-if="loading" class="p-3 space-y-2">
            <Skeleton v-for="i in 5" :key="i" class="h-10 w-full" />
          </div>

          <div v-else-if="roles.length === 0" class="p-4 text-center text-muted-foreground text-sm">
            暂无角色数据
          </div>

          <div v-else class="py-1">
            <button
              v-for="role in roles"
              :key="role.id"
              class="flex items-center w-full px-3 py-2.5 text-sm hover:bg-accent transition-colors text-left"
              :class="{ 'bg-accent': selectedRole?.id === role.id }"
              @click="selectRole(role)"
            >
              <Shield class="h-4 w-4 mr-2 shrink-0 text-blue-500" />
              <div class="flex-1 min-w-0">
                <div class="font-medium truncate">{{ role.name }}</div>
                <div class="text-xs text-muted-foreground">{{ role.code }}</div>
              </div>
              <Badge v-if="role.is_system" variant="secondary" class="ml-2 shrink-0 text-xs">
                系统
              </Badge>
            </button>
          </div>
        </ScrollArea>
      </div>

      <!-- 右侧：Tabs -->
      <div class="flex-1 flex flex-col border rounded-lg overflow-hidden bg-card">
        <template v-if="!selectedRole">
          <div class="flex-1 flex items-center justify-center text-muted-foreground">
            <div class="text-center">
              <Shield class="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>请从左侧选择一个角色</p>
            </div>
          </div>
        </template>

        <template v-else>
          <!-- 角色详情头部 -->
          <div class="p-4 border-b bg-muted/30">
            <div class="flex items-start justify-between">
              <div>
                <h2 class="text-lg font-semibold">{{ selectedRole.name }}</h2>
                <div class="text-sm text-muted-foreground mt-1">
                  <span class="font-mono">{{ selectedRole.code }}</span>
                  <span v-if="selectedRole.description" class="mx-2">·</span>
                  <span v-if="selectedRole.description">{{ selectedRole.description }}</span>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <Button size="sm" variant="outline" @click="handleEdit">
                  <Pencil class="h-3.5 w-3.5 mr-1" />
                  编辑
                </Button>
                <Button
                  v-if="!selectedRole.is_system"
                  size="sm"
                  variant="outline"
                  class="text-destructive hover:text-destructive"
                  @click="handleDelete"
                >
                  <Trash2 class="h-3.5 w-3.5 mr-1" />
                  删除
                </Button>
              </div>
            </div>
          </div>

          <!-- Tabs 内容 -->
          <Tabs v-model="activeTab" class="flex-1 flex flex-col">
            <div class="px-4 pt-2 border-b">
              <TabsList>
                <TabsTrigger value="members">
                  <Users class="h-4 w-4 mr-1" />
                  角色成员
                </TabsTrigger>
                <TabsTrigger value="permissions">
                  <Shield class="h-4 w-4 mr-1" />
                  权限列表
                </TabsTrigger>
              </TabsList>
            </div>
            <!-- 角色成员 Tab -->
            <TabsContent value="members" class="p-4 m-0">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm text-muted-foreground">
                  共 {{ memberTable.table.getRowCount() }} 个成员
                </span>
                <Button size="sm" @click="addMemberDialogOpen = true">
                  <UserPlus class="h-3.5 w-3.5 mr-1" />
                  添加成员
                </Button>
              </div>

              <!-- 成员表格 -->
              <DataTable :data-table="memberTable" :fixed-layout="true" />
            </TabsContent>

            <!-- 权限列表 Tab -->
            <TabsContent value="permissions" class="p-4 m-0 flex-none!">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm text-muted-foreground">
                  共 {{ rolePermissions.length }} 个权限
                </span>
                <Button size="sm" @click="handleOpenAssignPerm">
                  <Settings class="h-3.5 w-3.5 mr-1" />
                  分配权限
                </Button>
              </div>
              <ScrollArea class="h-[400px]">
                <div v-if="rolePermissions.length === 0" class="py-8 text-center text-muted-foreground">
                  <Shield class="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>暂无权限</p>
                </div>

                <div v-else class="space-y-2">
                  <div v-for="module in rolePermissionTree" :key="module.name" class="mb-2">
                    <!-- 模块级 -->
                    <button
                      class="flex items-center w-full py-2 px-2 text-sm font-medium hover:bg-accent rounded transition-colors text-left"
                      @click="toggleModule(module.name)"
                    >
                      <ChevronRight
                        :class="['h-4 w-4 mr-1 shrink-0 transition-transform', module.expanded && 'rotate-90']"
                      />
                      <Package class="h-4 w-4 mr-2 shrink-0 text-primary" />
                      <span>{{ module.label }}</span>
                      <Badge variant="secondary" class="ml-2 text-xs">
                        {{ module.resources.reduce((sum, r) => sum + r.permissions.length, 0) }}
                      </Badge>
                    </button>

                    <!-- 资源级 -->
                    <div v-show="module.expanded" class="ml-4">
                      <div v-for="resource in module.resources" :key="resource.name" class="mb-1">
                        <button
                          class="flex items-center w-full py-1.5 px-2 text-sm hover:bg-accent rounded transition-colors text-left"
                          @click="toggleResource(resource.name)"
                        >
                          <ChevronRight
                            :class="['h-3.5 w-3.5 mr-1 shrink-0 transition-transform', resource.expanded && 'rotate-90']"
                          />
                          <Menu class="h-4 w-4 mr-2 shrink-0 text-muted-foreground" />
                          <span>{{ resource.name }}</span>
                          <Badge variant="outline" class="ml-2 text-xs">
                            {{ resource.permissions.length }}
                          </Badge>
                        </button>

                        <!-- 权限级 -->
                        <div v-show="resource.expanded" class="ml-6 grid grid-cols-2 gap-x-4 gap-y-1">
                          <div
                            v-for="perm in resource.permissions"
                            :key="perm.id"
                            class="flex items-center gap-2 py-1.5 px-2 rounded hover:bg-accent"
                          >
                            <Shield class="h-4 w-4 text-blue-500 shrink-0" />
                            <div class="flex-1 min-w-0">
                              <div class="text-sm truncate">{{ perm.name }}</div>
                              <div class="text-xs text-muted-foreground truncate">{{ perm.code }}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </template>
      </div>
    </div>

    <!-- 添加成员弹窗 -->
    <PeopleSelectDialog
      v-model:open="addMemberDialogOpen"
      title="添加成员"
      description="选择要添加到角色的成员"
      :multiple="true"
      :load-org-nodes="loadOrgNodesCallback"
      :search-people="searchPeopleCallback"
      :load-org-people="loadOrgPeopleCallback"
      @confirm="handleAddMembers"
    />

    <!-- 分配权限弹窗 -->
    <Dialog v-model:open="assignPermDialogOpen">
      <DialogContent class="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle>分配权限</DialogTitle>
          <DialogDescription>
            为角色「{{ selectedRole?.name }}」分配权限
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
          <div v-for="module in filteredPermissionTree" :key="module.name" class="mb-2">
            <!-- 模块级 -->
            <button
              class="flex items-center w-full py-2 px-2 text-sm font-medium hover:bg-accent rounded transition-colors text-left"
              @click="toggleModule(module.name)"
            >
              <ChevronRight
                :class="['h-4 w-4 mr-1 shrink-0 transition-transform', module.expanded && 'rotate-90']"
              />
              <Package class="h-4 w-4 mr-2 shrink-0 text-primary" />
              <span>{{ module.label }}</span>
              <Badge variant="secondary" class="ml-2 text-xs">
                {{ module.resources.reduce((sum, r) => sum + r.permissions.length, 0) }}
              </Badge>
            </button>

            <!-- 资源级 -->
            <div v-show="module.expanded" class="ml-4">
              <div v-for="resource in module.resources" :key="resource.name" class="mb-1">
                <button
                  class="flex items-center w-full py-1.5 px-2 text-sm hover:bg-accent rounded transition-colors text-left"
                  @click="toggleResource(resource.name)"
                >
                  <ChevronRight
                    :class="['h-3.5 w-3.5 mr-1 shrink-0 transition-transform', resource.expanded && 'rotate-90']"
                  />
                  <Menu class="h-4 w-4 mr-2 shrink-0 text-muted-foreground" />
                  <span>{{ resource.name }}</span>
                  <Badge variant="outline" class="ml-2 text-xs">
                    {{ resource.permissions.length }}
                  </Badge>
                </button>

                <!-- 权限级 -->
                <div v-show="resource.expanded" class="ml-6 grid grid-cols-2 gap-x-4 gap-y-1">
                  <div
                    v-for="perm in resource.permissions"
                    :key="perm.id"
                    class="flex items-center gap-2 py-1.5"
                  >
                    <Checkbox
                      :model-value="selectedPermIds.includes(String(perm.id))"
                      @update:model-value="togglePermission(perm.id)"
                    />
                    <div class="flex-1 min-w-0">
                      <div class="text-sm truncate">{{ perm.name }}</div>
                      <div class="text-xs text-muted-foreground truncate">{{ perm.code }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" @click="assignPermDialogOpen = false">
            取消
          </Button>
          <Button @click="handleAssignPermSubmit">
            确定
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 创建/编辑角色弹窗 -->
    <Dialog v-model:open="formDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>
            {{ formDialogMode === "create" ? "新建角色" : "编辑角色" }}
          </DialogTitle>
          <DialogDescription v-if="formDialogMode === 'create'">
            创建一个新的角色
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4">
          <div class="space-y-2">
            <label class="text-sm font-medium">
              角色编码 <span class="text-destructive">*</span>
            </label>
            <Input
              v-model="formValues.code"
              placeholder="请输入角色编码"
              :disabled="formDialogMode === 'edit'"
            />
            <p class="text-xs text-muted-foreground">
              角色编码创建后不可修改
            </p>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium">
              角色名称 <span class="text-destructive">*</span>
            </label>
            <Input
              v-model="formValues.name"
              placeholder="请输入角色名称"
            />
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium">描述</label>
            <Input
              v-model="formValues.description"
              placeholder="请输入描述（可选）"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="formDialogOpen = false">
            取消
          </Button>
          <Button :disabled="formSubmitting" @click="handleFormSubmit">
            {{ formSubmitting ? "保存中..." : "确定" }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>
