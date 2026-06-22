<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getModule, getModuleMenus, createModuleMenu, updateModuleMenu, deleteModuleMenu, getModulePermissions, createModulePermission, updateModulePermission, deleteModulePermission, getModuleRoles, createModuleRole, updateModuleRole, deleteModuleRole, updateRolePermissions } from '@/tenant/api/module'
import type { Module, ModuleMenu, ModulePermission, ModuleRole, MenuCreate, MenuUpdate, PermissionCreate, PermissionUpdate, RoleCreate, RoleUpdate } from '@/tenant/types/admin'
import { notifyError, notifySuccess, notifyWarning } from '@/framework/utils/feedback'
import { Button, Input, Label, Card, Badge, Skeleton, Checkbox, Textarea } from '@/components'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tree } from '@/components'
import type { TreeSelectNode } from '@/framework/types/tree'
import { ArrowLeft, Pencil, Package, Menu, Key, Users, Plus, Trash2, FolderOpen, FileText, Search, Shield } from '@lucide/vue'

const route = useRoute()
const router = useRouter()

const moduleId = computed(() => route.params.id as string)
const moduleData = ref<Module | null>(null)
const loading = ref(false)

// 当前激活的 Tab
const activeTab = ref('info')

// ==================== 菜单管理状态 ====================
const menus = ref<ModuleMenu[]>([])
const menusLoading = ref(false)
const selectedMenuId = ref<string | null>(null)
const expandedMenuIds = ref<string[]>([])
const menuDialogOpen = ref(false)
const menuDialogMode = ref<'create' | 'edit'>('create')
const deleteMenuDialogOpen = ref(false)

// 菜单表单
const menuForm = ref({
  name: '',
  code: '',
  path: '',
  parent_id: '',
  icon: '',
  sort: 10,
})

// ==================== 权限管理状态 ====================
const permissions = ref<ModulePermission[]>([])
const permissionsLoading = ref(false)
const selectedPermissionId = ref<string | null>(null)
const permissionDialogOpen = ref(false)
const permissionDialogMode = ref<'create' | 'edit'>('create')
const deletePermissionDialogOpen = ref(false)
const permissionSearchKeyword = ref('')

// 权限表单
const permissionForm = ref({
  name: '',
  code: '',
  resource: '',
  action: 'read' as 'read' | 'write' | 'delete',
  description: '',
})

// ==================== 角色管理状态 ====================
const roles = ref<ModuleRole[]>([])
const rolesLoading = ref(false)
const selectedRoleId = ref<string | null>(null)
const roleDialogOpen = ref(false)
const roleDialogMode = ref<'create' | 'edit'>('create')
const deleteRoleDialogOpen = ref(false)
const roleSearchKeyword = ref('')
const permissionAssignDialogOpen = ref(false)
const selectedPermissionIds = ref<string[]>([])

// 角色表单
const roleForm = ref({
  name: '',
  code: '',
  description: '',
})

// 加载模块详情
const loadModule = async () => {
  loading.value = true
  try {
    const response = await getModule(moduleId.value)
    if (response.data) {
      moduleData.value = response.data
    }
  } catch (error) {
    console.error('加载模块详情失败:', error)
    notifyError('加载模块详情失败')
  } finally {
    loading.value = false
  }
}

// 返回列表
const handleBack = () => {
  router.push('/admin/modules')
}

// 编辑模块
const handleEdit = () => {
  router.push(`/admin/modules/${moduleId.value}/edit`)
}

// 格式化日期
const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString()
}

// ==================== 菜单管理方法 ====================

// 将 ModuleMenu 转换为 TreeSelectNode
const convertToTreeSelectNode = (menuList: ModuleMenu[]): TreeSelectNode[] => {
  return menuList.map(menu => ({
    id: menu.id,
    name: menu.name,
    children: menu.children ? convertToTreeSelectNode(menu.children) : [],
  }))
}

// 菜单树数据
const menuTreeData = computed<TreeSelectNode[]>(() => convertToTreeSelectNode(menus.value))

// 选中的菜单节点值（用于 Tree 组件）
const selectedMenuValues = computed<string[]>(() => selectedMenuId.value ? [selectedMenuId.value] : [])

// 当前选中的菜单对象
const selectedMenu = computed<ModuleMenu | null>(() => {
  if (!selectedMenuId.value) return null
  return findMenuById(menus.value, selectedMenuId.value)
})

// 递归查找菜单
const findMenuById = (menuList: ModuleMenu[], id: string): ModuleMenu | null => {
  for (const menu of menuList) {
    if (menu.id === id) return menu
    if (menu.children) {
      const found = findMenuById(menu.children, id)
      if (found) return found
    }
  }
  return null
}

// 获取所有菜单的扁平列表（用于父菜单选择）
const flattenMenus = (menuList: ModuleMenu[], level = 0): Array<{ id: string; name: string; level: number }> => {
  const result: Array<{ id: string; name: string; level: number }> = []
  for (const menu of menuList) {
    result.push({ id: menu.id, name: menu.name, level })
    if (menu.children) {
      result.push(...flattenMenus(menu.children, level + 1))
    }
  }
  return result
}

// 可选的父菜单列表（编辑时排除当前菜单及其子菜单）
const parentMenuOptions = computed(() => {
  const allMenus = flattenMenus(menus.value)
  if (menuDialogMode.value === 'edit' && selectedMenuId.value) {
    // 获取当前菜单及其所有子菜单的 ID
    const excludeIds = new Set<string>()
    const collectChildren = (menu: ModuleMenu) => {
      excludeIds.add(menu.id)
      if (menu.children) {
        menu.children.forEach(collectChildren)
      }
    }
    const currentMenu = findMenuById(menus.value, selectedMenuId.value)
    if (currentMenu) collectChildren(currentMenu)
    return allMenus.filter(m => !excludeIds.has(m.id))
  }
  return allMenus
})

// 加载菜单数据
const loadMenus = async () => {
  if (!moduleId.value) return
  menusLoading.value = true
  try {
    const response = await getModuleMenus(moduleId.value)
    if (response.data?.items) {
      menus.value = response.data.items
      // 默认展开第一级
      expandedMenuIds.value = menus.value.map(m => m.id)
    }
  } catch (error) {
    console.error('加载菜单失败:', error)
    notifyError('加载菜单失败')
  } finally {
    menusLoading.value = false
  }
}

// 处理菜单树节点点击
const handleMenuNodeClick = (node: TreeSelectNode) => {
  selectedMenuId.value = node.id as string
}

// 打开新增菜单弹窗
const openCreateMenuDialog = () => {
  menuDialogMode.value = 'create'
  menuForm.value = {
    name: '',
    code: '',
    path: '',
    parent_id: selectedMenuId.value || '',
    icon: '',
    sort: 10,
  }
  menuDialogOpen.value = true
}

// 打开编辑菜单弹窗
const openEditMenuDialog = () => {
  if (!selectedMenu.value) return
  menuDialogMode.value = 'edit'
  menuForm.value = {
    name: selectedMenu.value.name,
    code: selectedMenu.value.code,
    path: selectedMenu.value.path,
    parent_id: selectedMenu.value.parent_id || '',
    icon: selectedMenu.value.icon || '',
    sort: selectedMenu.value.sort,
  }
  menuDialogOpen.value = true
}

// 检查菜单是否有子菜单
const hasChildren = (menu: ModuleMenu): boolean => {
  return !!(menu.children && menu.children.length > 0)
}

// 打开删除确认弹窗
const openDeleteMenuDialog = () => {
  if (!selectedMenu.value) return
  if (hasChildren(selectedMenu.value)) {
    notifyWarning('该菜单存在子菜单，无法删除')
    return
  }
  deleteMenuDialogOpen.value = true
}

// 保存菜单
const saveMenu = async () => {
  if (!menuForm.value.name.trim()) {
    notifyWarning('请输入菜单名称')
    return
  }
  if (!menuForm.value.code.trim()) {
    notifyWarning('请输入菜单编码')
    return
  }
  if (!menuForm.value.path.trim()) {
    notifyWarning('请输入菜单路径')
    return
  }

  try {
    const params: MenuCreate | MenuUpdate = {
      name: menuForm.value.name.trim(),
      code: menuForm.value.code.trim(),
      path: menuForm.value.path.trim(),
      parent_id: menuForm.value.parent_id === 'none' ? undefined : menuForm.value.parent_id || undefined,
      icon: menuForm.value.icon.trim() || undefined,
      sort: menuForm.value.sort,
    }

    if (menuDialogMode.value === 'create') {
      await createModuleMenu(moduleId.value, params as MenuCreate)
      notifySuccess('菜单创建成功')
    } else if (selectedMenuId.value) {
      // 编辑模式下不修改 code
      delete params.code
      await updateModuleMenu(moduleId.value, selectedMenuId.value, params as MenuUpdate)
      notifySuccess('菜单更新成功')
    }

    menuDialogOpen.value = false
    await loadMenus()
  } catch (error) {
    console.error('保存菜单失败:', error)
    notifyError('保存菜单失败')
  }
}

// 删除菜单
const deleteMenu = async () => {
  if (!selectedMenuId.value) return
  try {
    await deleteModuleMenu(moduleId.value, selectedMenuId.value)
    notifySuccess('菜单删除成功')
    deleteMenuDialogOpen.value = false
    selectedMenuId.value = null
    await loadMenus()
  } catch (error) {
    console.error('删除菜单失败:', error)
    notifyError('删除菜单失败')
  }
}

// ==================== 权限管理方法 ====================

// 筛选后的权限列表
const filteredPermissions = computed(() => {
  if (!permissionSearchKeyword.value.trim()) {
    return permissions.value
  }
  const keyword = permissionSearchKeyword.value.toLowerCase()
  return permissions.value.filter(p =>
    p.name.toLowerCase().includes(keyword) ||
    p.code.toLowerCase().includes(keyword) ||
    p.resource.toLowerCase().includes(keyword)
  )
})

// 当前选中的权限对象
const selectedPermission = computed<ModulePermission | null>(() => {
  if (!selectedPermissionId.value) return null
  return permissions.value.find(p => p.id === selectedPermissionId.value) || null
})

// 加载权限数据
const loadPermissions = async () => {
  if (!moduleId.value) return
  permissionsLoading.value = true
  try {
    const response = await getModulePermissions(moduleId.value)
    if (response.data) {
      permissions.value = response.data
    }
  } catch (error) {
    console.error('加载权限失败:', error)
    notifyError('加载权限失败')
  } finally {
    permissionsLoading.value = false
  }
}

// 操作类型标签颜色
const getActionBadgeVariant = (action: string) => {
  switch (action) {
    case 'read':
      return 'default'
    case 'write':
      return 'secondary'
    case 'delete':
      return 'destructive'
    default:
      return 'outline'
  }
}

// 打开新增权限弹窗
const openCreatePermissionDialog = () => {
  permissionDialogMode.value = 'create'
  permissionForm.value = {
    name: '',
    code: '',
    resource: '',
    action: 'read',
    description: '',
  }
  permissionDialogOpen.value = true
}

// 打开编辑权限弹窗
const openEditPermissionDialog = (permission: ModulePermission) => {
  permissionDialogMode.value = 'edit'
  selectedPermissionId.value = permission.id
  permissionForm.value = {
    name: permission.name,
    code: permission.code,
    resource: permission.resource,
    action: permission.action,
    description: permission.description || '',
  }
  permissionDialogOpen.value = true
}

// 打开删除确认弹窗
const openDeletePermissionDialog = (permission: ModulePermission) => {
  selectedPermissionId.value = permission.id
  deletePermissionDialogOpen.value = true
}

// 验证权限编码格式
const validatePermissionCode = (code: string): boolean => {
  const pattern = /^[a-zA-Z][a-zA-Z0-9_-]*:[a-zA-Z][a-zA-Z0-9_-]*:(read|write|delete)$/
  return pattern.test(code)
}

// 保存权限
const savePermission = async () => {
  if (!permissionForm.value.name.trim()) {
    notifyWarning('请输入权限名称')
    return
  }
  if (!permissionForm.value.code.trim()) {
    notifyWarning('请输入权限编码')
    return
  }
  if (!validatePermissionCode(permissionForm.value.code)) {
    notifyWarning('权限编码格式不正确，必须为 module:resource:action 格式，且 action 必须是 read/write/delete')
    return
  }
  if (!permissionForm.value.resource.trim()) {
    notifyWarning('请输入资源名称')
    return
  }
  if (!['read', 'write', 'delete'].includes(permissionForm.value.action)) {
    notifyWarning('操作类型必须是 read、write 或 delete')
    return
  }

  try {
    const params: PermissionCreate | PermissionUpdate = {
      name: permissionForm.value.name.trim(),
      code: permissionForm.value.code.trim(),
      resource: permissionForm.value.resource.trim(),
      action: permissionForm.value.action,
      description: permissionForm.value.description.trim() || undefined,
    }

    if (permissionDialogMode.value === 'create') {
      await createModulePermission(moduleId.value, params as PermissionCreate)
      notifySuccess('权限创建成功')
    } else if (selectedPermissionId.value) {
      // 编辑模式下不修改 code
      delete params.code
      await updateModulePermission(moduleId.value, selectedPermissionId.value, params as PermissionUpdate)
      notifySuccess('权限更新成功')
    }

    permissionDialogOpen.value = false
    await loadPermissions()
  } catch (error) {
    console.error('保存权限失败:', error)
    notifyError('保存权限失败')
  }
}

// 删除权限
const deletePermission = async () => {
  if (!selectedPermissionId.value) return
  try {
    await deleteModulePermission(moduleId.value, selectedPermissionId.value)
    notifySuccess('权限删除成功')
    deletePermissionDialogOpen.value = false
    selectedPermissionId.value = null
    await loadPermissions()
  } catch (error) {
    console.error('删除权限失败:', error)
    notifyError('删除权限失败')
  }
}

// ==================== 角色管理方法 ====================

// 筛选后的角色列表
const filteredRoles = computed(() => {
  if (!roleSearchKeyword.value.trim()) {
    return roles.value
  }
  const keyword = roleSearchKeyword.value.toLowerCase()
  return roles.value.filter(r =>
    r.name.toLowerCase().includes(keyword) ||
    r.code.toLowerCase().includes(keyword)
  )
})

// 当前选中的角色对象
const selectedRole = computed<ModuleRole | null>(() => {
  if (!selectedRoleId.value) return null
  return roles.value.find(r => r.id === selectedRoleId.value) || null
})

// 加载角色数据
const loadRoles = async () => {
  if (!moduleId.value) return
  rolesLoading.value = true
  try {
    const response = await getModuleRoles(moduleId.value)
    if (response.data) {
      roles.value = response.data
    }
  } catch (error) {
    console.error('加载角色失败:', error)
    notifyError('加载角色失败')
  } finally {
    rolesLoading.value = false
  }
}

// 打开新增角色弹窗
const openCreateRoleDialog = () => {
  roleDialogMode.value = 'create'
  roleForm.value = {
    name: '',
    code: '',
    description: '',
  }
  roleDialogOpen.value = true
}

// 打开编辑角色弹窗
const openEditRoleDialog = (role: ModuleRole) => {
  if (role.is_system) {
    notifyWarning('系统内置角色禁止修改')
    return
  }
  roleDialogMode.value = 'edit'
  selectedRoleId.value = role.id
  roleForm.value = {
    name: role.name,
    code: role.code,
    description: role.description || '',
  }
  roleDialogOpen.value = true
}

// 打开删除确认弹窗
const openDeleteRoleDialog = (role: ModuleRole) => {
  if (role.is_system) {
    notifyWarning('系统内置角色禁止删除')
    return
  }
  selectedRoleId.value = role.id
  deleteRoleDialogOpen.value = true
}

// 保存角色
const saveRole = async () => {
  if (!roleForm.value.name.trim()) {
    notifyWarning('请输入角色名称')
    return
  }
  if (!roleForm.value.code.trim()) {
    notifyWarning('请输入角色编码')
    return
  }

  try {
    if (roleDialogMode.value === 'create') {
      const params: RoleCreate = {
        name: roleForm.value.name.trim(),
        code: roleForm.value.code.trim(),
        description: roleForm.value.description.trim() || undefined,
      }
      await createModuleRole(moduleId.value, params)
      notifySuccess('角色创建成功')
    } else if (selectedRoleId.value) {
      const params: RoleUpdate = {
        name: roleForm.value.name.trim(),
        description: roleForm.value.description.trim() || undefined,
      }
      await updateModuleRole(moduleId.value, selectedRoleId.value, params)
      notifySuccess('角色更新成功')
    }

    roleDialogOpen.value = false
    await loadRoles()
  } catch (error) {
    console.error('保存角色失败:', error)
    notifyError('保存角色失败')
  }
}

// 删除角色
const deleteRole = async () => {
  if (!selectedRoleId.value) return
  try {
    await deleteModuleRole(moduleId.value, selectedRoleId.value)
    notifySuccess('角色删除成功')
    deleteRoleDialogOpen.value = false
    selectedRoleId.value = null
    await loadRoles()
  } catch (error) {
    console.error('删除角色失败:', error)
    notifyError('删除角色失败')
  }
}

// 打开权限分配弹窗
const openPermissionAssignDialog = (role: ModuleRole) => {
  selectedRoleId.value = role.id
  selectedPermissionIds.value = [...role.permission_ids]
  permissionAssignDialogOpen.value = true
}

// 切换权限选中状态
const togglePermission = (permissionId: string) => {
  const index = selectedPermissionIds.value.indexOf(permissionId)
  if (index === -1) {
    selectedPermissionIds.value.push(permissionId)
  } else {
    selectedPermissionIds.value.splice(index, 1)
  }
}

// 全选/取消全选权限
const toggleAllPermissions = () => {
  if (selectedPermissionIds.value.length === permissions.value.length) {
    selectedPermissionIds.value = []
  } else {
    selectedPermissionIds.value = permissions.value.map(p => p.id)
  }
}

// 保存权限分配
const savePermissionAssign = async () => {
  if (!selectedRoleId.value) return
  try {
    await updateRolePermissions(moduleId.value, selectedRoleId.value, selectedPermissionIds.value)
    notifySuccess('权限分配成功')
    permissionAssignDialogOpen.value = false
    await loadRoles()
  } catch (error) {
    console.error('保存权限分配失败:', error)
    notifyError('保存权限分配失败')
  }
}

// 监听 Tab 切换，加载菜单数据
watch(activeTab, (newTab) => {
  if (newTab === 'menus' && menus.value.length === 0) {
    loadMenus()
  }
  if (newTab === 'permissions' && permissions.value.length === 0) {
    loadPermissions()
  }
  if (newTab === 'roles' && roles.value.length === 0) {
    loadRoles()
  }
})

onMounted(() => {
  loadModule()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="icon" @click="handleBack">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div>
          <h2 class="text-xl font-semibold">
            <span v-if="loading"><Skeleton class="h-6 w-32" /></span>
            <span v-else>{{ moduleData?.name || '模块详情' }}</span>
          </h2>
          <p class="text-muted-foreground mt-1 text-sm">
            <span v-if="loading"><Skeleton class="h-4 w-24" /></span>
            <span v-else>{{ moduleData?.code || '--' }}</span>
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button @click="handleEdit">
          <Pencil class="mr-1 h-4 w-4" />
          编辑模块
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-3">
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Package class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">模块状态</span>
        </div>
        <div class="mt-2">
          <Badge v-if="moduleData" :variant="moduleData.is_active ? 'default' : 'secondary'">
            {{ moduleData.is_active ? '启用' : '停用' }}
          </Badge>
          <Skeleton v-else class="h-5 w-12" />
        </div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Key class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">必须模块</span>
        </div>
        <div class="mt-2">
          <Badge v-if="moduleData" :variant="moduleData.is_need ? 'default' : 'outline'">
            {{ moduleData.is_need ? '是' : '否' }}
          </Badge>
          <Skeleton v-else class="h-5 w-12" />
        </div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Users class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">分配租户</span>
        </div>
        <div class="text-2xl font-semibold">
          <span v-if="moduleData">{{ moduleData.tenant_count || 0 }}</span>
          <Skeleton v-else class="h-7 w-8" />
        </div>
      </Card>
    </div>

    <!-- Tab 切换区 -->
    <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
      <Tabs v-model="activeTab" class="flex h-full flex-col">
        <div class="border-b px-5 pt-4">
          <TabsList>
            <TabsTrigger value="info">
              <Package class="mr-1 h-4 w-4" />
              基本信息
            </TabsTrigger>
            <TabsTrigger value="menus">
              <Menu class="mr-1 h-4 w-4" />
              菜单管理
            </TabsTrigger>
            <TabsTrigger value="permissions">
              <Key class="mr-1 h-4 w-4" />
              权限管理
            </TabsTrigger>
            <TabsTrigger value="roles">
              <Users class="mr-1 h-4 w-4" />
              角色管理
            </TabsTrigger>
          </TabsList>
        </div>

        <div class="min-h-0 flex-1 overflow-auto px-5 py-5">
          <!-- 基本信息 Tab -->
          <TabsContent value="info" class="mt-0">
            <div v-if="loading" class="space-y-4">
              <div v-for="n in 6" :key="n" class="grid gap-4 md:grid-cols-2">
                <Skeleton class="h-16 w-full" />
                <Skeleton class="h-16 w-full" />
              </div>
            </div>
            <div v-else-if="moduleData" class="grid gap-4 md:grid-cols-2">
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块名称</div>
                <div class="mt-2 font-medium">{{ moduleData.name }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块编码</div>
                <div class="mt-2 font-medium">{{ moduleData.code }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块图标</div>
                <div class="mt-2 font-medium">{{ moduleData.icon || '未设置' }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块状态</div>
                <div class="mt-2">
                  <Badge :variant="moduleData.is_active ? 'default' : 'secondary'">
                    {{ moduleData.is_active ? '启用' : '停用' }}
                  </Badge>
                </div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">是否必须模块</div>
                <div class="mt-2">
                  <Badge :variant="moduleData.is_need ? 'default' : 'outline'">
                    {{ moduleData.is_need ? '是' : '否' }}
                  </Badge>
                </div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">创建时间</div>
                <div class="mt-2 font-medium">{{ formatDate(moduleData.created_at) }}</div>
              </div>
              <div class="rounded-lg border p-4 md:col-span-2">
                <div class="text-muted-foreground text-xs">模块描述</div>
                <div class="mt-2 text-sm leading-6">{{ moduleData.description || '暂无描述' }}</div>
              </div>
            </div>
          </TabsContent>

          <!-- 菜单管理 Tab -->
          <TabsContent value="menus" class="mt-0">
            <div v-if="menusLoading" class="flex h-full items-center justify-center py-12">
              <Skeleton class="h-8 w-8 rounded-full" />
            </div>
            <div v-else class="flex h-full min-h-[400px] gap-4">
              <!-- 左侧菜单树 -->
              <Card class="flex min-h-0 w-[300px] shrink-0 flex-col gap-0 overflow-hidden py-0">
                <div class="border-b px-4 py-4">
                  <div class="flex items-center justify-between">
                    <div class="font-medium">菜单树</div>
                    <Button size="sm" @click="openCreateMenuDialog">
                      <Plus class="mr-1 h-4 w-4" />
                      新增
                    </Button>
                  </div>
                  <div class="text-muted-foreground mt-1 text-xs">点击菜单项查看详情</div>
                </div>
                <ScrollArea class="min-h-0 flex-1 px-3 py-3">
                  <div v-if="menus.length === 0" class="text-muted-foreground py-8 text-center text-sm">
                    暂无菜单数据
                  </div>
                  <Tree
                    v-else
                    v-model="selectedMenuValues"
                    :data="menuTreeData"
                    :expanded-value="expandedMenuIds"
                    :multiple="false"
                    :show-line="true"
                    @on-node-click="handleMenuNodeClick"
                  >
                    <template #leaf-icon>
                      <FileText class="h-4 w-4 text-muted-foreground" />
                    </template>
                  </Tree>
                </ScrollArea>
              </Card>

              <!-- 右侧菜单详情 -->
              <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
                <div class="border-b px-5 py-4">
                  <div class="flex items-center justify-between">
                    <div class="font-medium">{{ selectedMenu?.name || '菜单详情' }}</div>
                    <div v-if="selectedMenu" class="flex items-center gap-2">
                      <Button size="sm" variant="outline" @click="openEditMenuDialog">
                        <Pencil class="mr-1 h-4 w-4" />
                        编辑
                      </Button>
                      <Button size="sm" variant="destructive" @click="openDeleteMenuDialog">
                        <Trash2 class="mr-1 h-4 w-4" />
                        删除
                      </Button>
                    </div>
                  </div>
                  <div v-if="selectedMenu" class="text-muted-foreground mt-1 text-xs">
                    编码：{{ selectedMenu.code }}
                  </div>
                </div>
                <div v-if="selectedMenu" class="flex-1 overflow-auto px-5 py-5">
                  <div class="grid gap-4 md:grid-cols-2">
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">菜单名称</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.name }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">菜单编码</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.code }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">菜单路径</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.path }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">菜单图标</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.icon || '未设置' }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">排序</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.sort }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">子菜单数量</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.children?.length || 0 }}</div>
                    </div>
                    <div class="rounded-lg border p-4 md:col-span-2">
                      <div class="text-muted-foreground text-xs">创建时间</div>
                      <div class="mt-2 font-medium">{{ formatDate(selectedMenu.created_at) }}</div>
                    </div>
                  </div>
                </div>
                <div v-else class="flex flex-1 flex-col items-center justify-center gap-4 py-12">
                  <FolderOpen class="text-muted-foreground h-12 w-12" />
                  <div class="text-center">
                    <div class="font-medium">请选择菜单</div>
                    <div class="text-muted-foreground mt-1 text-sm">从左侧树中选择一个菜单查看详情</div>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>

          <!-- 权限管理 Tab -->
          <TabsContent value="permissions" class="mt-0">
            <div v-if="permissionsLoading" class="flex h-full items-center justify-center py-12">
              <Skeleton class="h-8 w-8 rounded-full" />
            </div>
            <div v-else class="flex h-full flex-col gap-4">
              <!-- 工具栏 -->
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div class="relative w-full sm:w-64">
                  <Search class="text-muted-foreground absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" />
                  <Input
                    v-model="permissionSearchKeyword"
                    placeholder="搜索权限名称、编码..."
                    class="pl-9"
                  />
                </div>
                <Button @click="openCreatePermissionDialog">
                  <Plus class="mr-1 h-4 w-4" />
                  新增权限
                </Button>
              </div>

              <!-- 权限列表 -->
              <div class="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead class="w-[150px]">权限名称</TableHead>
                      <TableHead class="w-[200px]">权限编码</TableHead>
                      <TableHead class="w-[120px]">资源</TableHead>
                      <TableHead class="w-[100px]">操作类型</TableHead>
                      <TableHead>说明</TableHead>
                      <TableHead class="w-[120px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-if="filteredPermissions.length === 0">
                      <TableCell colspan="6" class="text-muted-foreground text-center">
                        {{ permissionSearchKeyword ? '未找到匹配的权限' : '暂无权限数据' }}
                      </TableCell>
                    </TableRow>
                    <TableRow v-for="permission in filteredPermissions" :key="permission.id">
                      <TableCell class="font-medium">{{ permission.name }}</TableCell>
                      <TableCell class="font-mono text-sm">{{ permission.code }}</TableCell>
                      <TableCell>{{ permission.resource }}</TableCell>
                      <TableCell>
                        <Badge :variant="getActionBadgeVariant(permission.action)">
                          {{ permission.action }}
                        </Badge>
                      </TableCell>
                      <TableCell>{{ permission.description || '--' }}</TableCell>
                      <TableCell>
                        <div class="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            @click="openEditPermissionDialog(permission)"
                          >
                            <Pencil class="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            @click="openDeletePermissionDialog(permission)"
                          >
                            <Trash2 class="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>

              <!-- 权限统计 -->
              <div class="text-muted-foreground text-sm">
                共 {{ permissions.length }} 项权限{{ permissionSearchKeyword ? `，筛选结果 ${filteredPermissions.length} 项` : '' }}
              </div>
            </div>
          </TabsContent>

          <!-- 角色管理 Tab -->
          <TabsContent value="roles" class="mt-0">
            <div v-if="rolesLoading" class="flex h-full items-center justify-center py-12">
              <Skeleton class="h-8 w-8 rounded-full" />
            </div>
            <div v-else class="flex h-full flex-col gap-4">
              <!-- 工具栏 -->
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div class="relative w-full sm:w-64">
                  <Search class="text-muted-foreground absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" />
                  <Input
                    v-model="roleSearchKeyword"
                    placeholder="搜索角色名称、编码..."
                    class="pl-9"
                  />
                </div>
                <Button @click="openCreateRoleDialog">
                  <Plus class="mr-1 h-4 w-4" />
                  新增角色
                </Button>
              </div>

              <!-- 角色列表 -->
              <div class="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead class="w-[150px]">角色名称</TableHead>
                      <TableHead class="w-[150px]">角色编码</TableHead>
                      <TableHead>说明</TableHead>
                      <TableHead class="w-[100px]">系统角色</TableHead>
                      <TableHead class="w-[100px]">权限数量</TableHead>
                      <TableHead class="w-[150px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-if="filteredRoles.length === 0">
                      <TableCell colspan="6" class="text-muted-foreground text-center">
                        {{ roleSearchKeyword ? '未找到匹配的角色' : '暂无角色数据' }}
                      </TableCell>
                    </TableRow>
                    <TableRow v-for="role in filteredRoles" :key="role.id">
                      <TableCell class="font-medium">
                        <div class="flex items-center gap-2">
                          {{ role.name }}
                          <Badge v-if="role.is_system" variant="outline" class="text-xs">
                            系统
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell class="font-mono text-sm">{{ role.code }}</TableCell>
                      <TableCell>{{ role.description || '--' }}</TableCell>
                      <TableCell>
                        <Badge :variant="role.is_system ? 'default' : 'secondary'">
                          {{ role.is_system ? '是' : '否' }}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {{ role.permission_ids?.length || 0 }}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div class="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            title="分配权限"
                            @click="openPermissionAssignDialog(role)"
                          >
                            <Shield class="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            :disabled="role.is_system"
                            :title="role.is_system ? '系统内置角色禁止修改' : '编辑'"
                            @click="openEditRoleDialog(role)"
                          >
                            <Pencil class="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            :disabled="role.is_system"
                            :title="role.is_system ? '系统内置角色禁止删除' : '删除'"
                            @click="openDeleteRoleDialog(role)"
                          >
                            <Trash2 class="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>

              <!-- 角色统计 -->
              <div class="text-muted-foreground text-sm">
                共 {{ roles.length }} 个角色{{ roleSearchKeyword ? `，筛选结果 ${filteredRoles.length} 个` : '' }}
              </div>
            </div>
          </TabsContent>
        </div>
      </Tabs>
    </Card>

    <!-- 菜单表单弹窗 -->
    <Dialog v-model:open="menuDialogOpen">
      <DialogContent class="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{{ menuDialogMode === 'create' ? '新增菜单' : '编辑菜单' }}</DialogTitle>
        </DialogHeader>
        <div class="grid gap-4 py-4">
          <div class="grid gap-2">
            <Label>菜单名称 <span class="text-destructive">*</span></Label>
            <Input v-model="menuForm.name" placeholder="请输入菜单名称" />
          </div>
          <div class="grid gap-2">
            <Label>菜单编码 <span class="text-destructive">*</span></Label>
            <Input
              v-model="menuForm.code"
              placeholder="请输入菜单编码"
              :disabled="menuDialogMode === 'edit'"
            />
            <p v-if="menuDialogMode === 'edit'" class="text-muted-foreground text-xs">编码不可修改</p>
          </div>
          <div class="grid gap-2">
            <Label>菜单路径 <span class="text-destructive">*</span></Label>
            <Input v-model="menuForm.path" placeholder="请输入菜单路径，如 /system/users" />
          </div>
          <div class="grid gap-2">
            <Label>父菜单</Label>
            <Select v-model="menuForm.parent_id">
              <SelectTrigger>
                <SelectValue placeholder="请选择父菜单（不选则为顶级菜单）" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">无（顶级菜单）</SelectItem>
                <SelectItem
                  v-for="option in parentMenuOptions"
                  :key="option.id"
                  :value="option.id"
                >
                  {{ '-- '.repeat(option.level) }}{{ option.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label>菜单图标</Label>
            <Input v-model="menuForm.icon" placeholder="请输入图标名称" />
          </div>
          <div class="grid gap-2">
            <Label>排序</Label>
            <Input v-model.number="menuForm.sort" type="number" placeholder="数字越小越靠前" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="menuDialogOpen = false">取消</Button>
          <Button @click="saveMenu">保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 删除确认弹窗 -->
    <Dialog v-model:open="deleteMenuDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>确认删除菜单</DialogTitle>
          <DialogDescription>
            确定要删除菜单「{{ selectedMenu?.name }}」吗？此操作不可撤销。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="deleteMenuDialogOpen = false">取消</Button>
          <Button
            variant="destructive"
            @click="deleteMenu"
          >
            确认删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 权限表单弹窗 -->
    <Dialog v-model:open="permissionDialogOpen">
      <DialogContent class="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{{ permissionDialogMode === 'create' ? '新增权限' : '编辑权限' }}</DialogTitle>
        </DialogHeader>
        <div class="grid gap-4 py-4">
          <div class="grid gap-2">
            <Label>权限名称 <span class="text-destructive">*</span></Label>
            <Input v-model="permissionForm.name" placeholder="请输入权限名称" />
          </div>
          <div class="grid gap-2">
            <Label>权限编码 <span class="text-destructive">*</span></Label>
            <Input
              v-model="permissionForm.code"
              placeholder="格式: module:resource:action"
              :disabled="permissionDialogMode === 'edit'"
            />
            <p class="text-muted-foreground text-xs">
              {{ permissionDialogMode === 'edit' ? '编码不可修改' : '格式: module:resource:action，如 user:data:read' }}
            </p>
          </div>
          <div class="grid gap-2">
            <Label>资源 <span class="text-destructive">*</span></Label>
            <Input v-model="permissionForm.resource" placeholder="请输入资源名称，如 user、role" />
          </div>
          <div class="grid gap-2">
            <Label>操作类型 <span class="text-destructive">*</span></Label>
            <Select v-model="permissionForm.action">
              <SelectTrigger>
                <SelectValue placeholder="请选择操作类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="read">read - 读取</SelectItem>
                <SelectItem value="write">write - 写入</SelectItem>
                <SelectItem value="delete">delete - 删除</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label>说明</Label>
            <Input v-model="permissionForm.description" placeholder="请输入权限说明" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="permissionDialogOpen = false">取消</Button>
          <Button @click="savePermission">保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 删除权限确认弹窗 -->
    <Dialog v-model:open="deletePermissionDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>确认删除权限</DialogTitle>
          <DialogDescription>
            确定要删除权限「{{ selectedPermission?.name }}」吗？此操作不可撤销。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="deletePermissionDialogOpen = false">取消</Button>
          <Button
            variant="destructive"
            @click="deletePermission"
          >
            确认删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 角色表单弹窗 -->
    <Dialog v-model:open="roleDialogOpen">
      <DialogContent class="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{{ roleDialogMode === 'create' ? '新增角色' : '编辑角色' }}</DialogTitle>
        </DialogHeader>
        <div class="grid gap-4 py-4">
          <div class="grid gap-2">
            <Label>角色名称 <span class="text-destructive">*</span></Label>
            <Input v-model="roleForm.name" placeholder="请输入角色名称" />
          </div>
          <div class="grid gap-2">
            <Label>角色编码 <span class="text-destructive">*</span></Label>
            <Input
              v-model="roleForm.code"
              placeholder="请输入角色编码"
              :disabled="roleDialogMode === 'edit'"
            />
            <p v-if="roleDialogMode === 'edit'" class="text-muted-foreground text-xs">编码不可修改</p>
          </div>
          <div class="grid gap-2">
            <Label>说明</Label>
            <Textarea v-model="roleForm.description" placeholder="请输入角色说明" :rows="3" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="roleDialogOpen = false">取消</Button>
          <Button @click="saveRole">保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 删除角色确认弹窗 -->
    <Dialog v-model:open="deleteRoleDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>确认删除角色</DialogTitle>
          <DialogDescription>
            确定要删除角色「{{ selectedRole?.name }}」吗？此操作不可撤销。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="deleteRoleDialogOpen = false">取消</Button>
          <Button
            variant="destructive"
            @click="deleteRole"
          >
            确认删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 权限分配弹窗 -->
    <Dialog v-model:open="permissionAssignDialogOpen">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>分配权限</DialogTitle>
          <DialogDescription>
            为角色「{{ selectedRole?.name }}」分配权限
          </DialogDescription>
        </DialogHeader>
        <div class="py-4">
          <div class="mb-3 flex items-center justify-between">
            <span class="text-sm font-medium">已选择 {{ selectedPermissionIds.length }} / {{ permissions.length }} 项权限</span>
            <Button variant="outline" size="sm" @click="toggleAllPermissions">
              {{ selectedPermissionIds.length === permissions.length ? '取消全选' : '全选' }}
            </Button>
          </div>
          <ScrollArea class="h-[400px] rounded-lg border">
            <div class="p-4">
              <div v-if="permissions.length === 0" class="text-muted-foreground py-8 text-center text-sm">
                暂无可分配的权限，请先在「权限管理」中创建权限
              </div>
              <div v-else class="space-y-3">
                <div
                  v-for="permission in permissions"
                  :key="permission.id"
                  class="flex items-center gap-3 rounded-md border p-3 transition-colors hover:bg-muted/50"
                  :class="{ 'bg-muted/50': selectedPermissionIds.includes(permission.id) }"
                  @click="togglePermission(permission.id)"
                >
                  <Checkbox
                    :checked="selectedPermissionIds.includes(permission.id)"
                    @update:checked="togglePermission(permission.id)"
                    @click.stop
                  />
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <span class="font-medium">{{ permission.name }}</span>
                      <Badge :variant="getActionBadgeVariant(permission.action)" class="text-xs">
                        {{ permission.action }}
                      </Badge>
                    </div>
                    <div class="text-muted-foreground mt-1 font-mono text-xs">
                      {{ permission.code }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </ScrollArea>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="permissionAssignDialogOpen = false">取消</Button>
          <Button @click="savePermissionAssign">保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
