<script setup lang="ts">
/**
 * PermissionList — 权限管理页面
 *
 * 布局：
 * - 左侧：权限树（按资源分组）
 * - 右侧：Tabs（角色列表、菜单列表）
 */

import { ref, computed, onMounted } from "vue"
import {
  Shield,
  Search,
  Users,
  Menu,
  Settings,
} from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  Skeleton,
  Input,
  Checkbox,
} from "@/components"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components"
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

const loading = ref(false)
const permissions = ref<Permission[]>([])
const roles = ref<Role[]>([])
const menus = ref<MenuTreeNode[]>([])

// 权限树搜索
const searchKeyword = ref("")

// 当前选中的资源
const selectedResource = ref<string | null>(null)

// Tabs
const activeTab = ref("roles")

// 分配权限弹窗
const assignDialogOpen = ref(false)
const currentRole = ref<Role | null>(null)
const selectedPermissionIds = ref<string[]>([])
const assignLoading = ref(false)

// ========== 计算属性 ==========

// 按资源分组的权限
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

// 资源列表（用于左侧树）
const resources = computed(() => {
  return permissionGroups.value.map((g) => ({
    id: g.resource,
    name: g.resource,
    count: g.permissions.length,
  }))
})

// 筛选后的权限组
const filteredGroups = computed(() => {
  if (!searchKeyword.value.trim()) {
    return permissionGroups.value
  }

  const keyword = searchKeyword.value.toLowerCase()
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

// ========== 方法 ==========

/** 加载数据 */
async function loadData() {
  loading.value = true
  try {
    const [permRes, rolesRes, menusRes] = await Promise.all([
      getPermissions({ page: 1, page_size: 1000 }),
      getRoles({ page: 1, page_size: 100 }),
      getMenus(),
    ])
    permissions.value = permRes.data?.items || []
    roles.value = rolesRes.data?.items || []
    menus.value = menusRes.data?.menus || []
  } catch (error) {
    notifyError(getErrorMessage(error, "加载数据失败"))
  } finally {
    loading.value = false
  }
}

/** 选择资源 */
function selectResource(resource: string) {
  selectedResource.value = resource
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
    await assignRolePermissions(currentRole.value.id, selectedPermissionIds.value)
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
</script>

<template>
  <AppPage title="权限管理" variant="workbench" description="管理系统权限、角色和菜单">
    <div class="flex gap-4 flex-1 min-h-0">
      <!-- 左侧：权限树 -->
      <div class="w-[280px] shrink-0 flex flex-col border rounded-lg overflow-hidden">
        <div class="p-3 border-b bg-muted/30">
          <div class="relative">
            <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              v-model="searchKeyword"
              placeholder="搜索权限..."
              class="pl-8"
            />
          </div>
        </div>

        <ScrollArea class="flex-1">
          <div v-if="loading" class="p-3 space-y-2">
            <Skeleton v-for="i in 6" :key="i" class="h-6 w-full" />
          </div>

          <div v-else-if="resources.length === 0" class="p-4 text-center text-muted-foreground text-sm">
            暂无权限数据
          </div>

          <div v-else class="py-1">
            <button
              v-for="resource in resources"
              :key="resource.id"
              class="flex items-center w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left"
              :class="{ 'bg-accent': selectedResource === resource.id }"
              @click="selectResource(resource.id)"
            >
              <Shield class="h-4 w-4 mr-2 shrink-0 text-blue-500" />
              <span class="truncate">{{ resource.name }}</span>
              <Badge variant="secondary" class="ml-auto shrink-0 text-xs">
                {{ resource.count }}
              </Badge>
            </button>
          </div>
        </ScrollArea>
      </div>

      <!-- 右侧：Tabs -->
      <div class="flex-1 flex flex-col border rounded-lg overflow-hidden">
        <Tabs v-model="activeTab" class="flex-1 flex flex-col">
          <div class="px-4 pt-2 border-b">
            <TabsList>
              <TabsTrigger value="roles">
                <Users class="h-4 w-4 mr-1" />
                角色列表
              </TabsTrigger>
              <TabsTrigger value="menus">
                <Menu class="h-4 w-4 mr-1" />
                菜单列表
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea class="flex-1">
            <!-- 角色列表 Tab -->
            <TabsContent value="roles" class="p-4 m-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>角色名称</TableHead>
                    <TableHead>角色编码</TableHead>
                    <TableHead>描述</TableHead>
                    <TableHead class="w-[100px]">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-if="loading">
                    <TableCell v-for="n in 4" :key="n">
                      <Skeleton class="h-5 w-full" />
                    </TableCell>
                  </TableRow>
                  <TableRow v-else-if="roles.length === 0">
                    <TableCell colspan="4" class="h-16 text-center text-muted-foreground">
                      暂无角色数据
                    </TableCell>
                  </TableRow>
                  <TableRow v-else v-for="role in roles" :key="role.id">
                    <TableCell class="font-medium">{{ role.name }}</TableCell>
                    <TableCell class="font-mono text-sm">{{ role.code }}</TableCell>
                    <TableCell>{{ role.description || "--" }}</TableCell>
                    <TableCell>
                      <Button variant="outline" size="sm" @click="handleAssignPermissions(role)">
                        <Settings class="mr-1 h-3.5 w-3.5" />
                        分配权限
                      </Button>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TabsContent>

            <!-- 菜单列表 Tab -->
            <TabsContent value="menus" class="p-4 m-0">
              <div v-if="loading" class="py-4">
                <Skeleton v-for="i in 5" :key="i" class="h-8 w-full mb-2" />
              </div>

              <div v-else-if="menus.length === 0" class="py-8 text-center text-muted-foreground">
                暂无菜单数据
              </div>

              <div v-else class="space-y-1">
                <template v-for="menu in menus" :key="menu.id">
                  <div class="flex items-center gap-2 py-2 px-2 rounded hover:bg-accent">
                    <Menu class="h-4 w-4 text-muted-foreground" />
                    <span class="font-medium">{{ menu.name }}</span>
                    <span class="text-xs text-muted-foreground">{{ menu.path }}</span>
                  </div>
                  <!-- 子菜单 -->
                  <template v-if="menu.children" v-for="child in menu.children" :key="child.id">
                    <div class="flex items-center gap-2 py-2 px-6 rounded hover:bg-accent">
                      <Menu class="h-3.5 w-3.5 text-muted-foreground" />
                      <span>{{ child.name }}</span>
                      <span class="text-xs text-muted-foreground">{{ child.path }}</span>
                    </div>
                  </template>
                </template>
              </div>
            </TabsContent>
          </ScrollArea>
        </Tabs>
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

        <ScrollArea class="h-[400px] pr-4">
          <div v-for="group in permissionGroups" :key="group.resource" class="mb-4">
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
