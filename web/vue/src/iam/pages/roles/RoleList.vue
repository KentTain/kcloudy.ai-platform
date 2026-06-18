<script setup lang="ts">
/**
 * RoleList — 角色管理页面
 *
 * 布局：
 * - 左侧：角色列表（300px 固定宽度）
 * - 右侧：Tabs（角色成员、权限列表）
 */

import { ref, computed, onMounted } from "vue"
import {
  Shield,
  Users,
  Plus,
  Pencil,
  Trash2,
  Settings,
  UserPlus,
  X,
  Search,
} from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  Skeleton,
  Table,
  Checkbox,
  PeopleSelectDialog,
  Input,
} from "@/components"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
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
import { confirmAction, notifySuccess, notifyError, getErrorMessage } from "@/framework/utils/feedback"
import type { Role, Permission, PermissionGroup } from "@/iam/types"
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
import { getDepartmentTree, getDepartmentMembers } from "@/iam/api/department"
import { getUsers } from "@/iam/api/user"

// ========== 状态 ==========

const loading = ref(false)
const roles = ref<Role[]>([])
const selectedRole = ref<Role | null>(null)
const activeTab = ref("members")

// 角色成员
const members = ref<{ user_id: string; username: string; nickname?: string; email?: string; phone?: string; status: string }[]>([])
const membersLoading = ref(false)

// 角色权限
const allPermissions = ref<Permission[]>([])
const rolePermissions = ref<Permission[]>([])

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

// ========== 方法 ==========

/** 加载角色列表 */
async function loadRoles() {
  loading.value = true
  try {
    const res = await getRoles({ page: 1, page_size: 100 })
    roles.value = res.data?.items || []
  } catch (error) {
    notifyError(getErrorMessage(error, "加载角色列表失败"))
  } finally {
    loading.value = false
  }
}

/** 选择角色 */
async function selectRole(role: Role) {
  selectedRole.value = role
  activeTab.value = "members"
  await loadRoleMembers()
  await loadRolePermissions()
}

/** 加载角色成员 */
async function loadRoleMembers() {
  if (!selectedRole.value) return
  membersLoading.value = true
  try {
    const res = await getRoleMembers(selectedRole.value.id)
    members.value = res.data || []
  } catch (error) {
    notifyError(getErrorMessage(error, "加载角色成员失败"))
    members.value = []
  } finally {
    membersLoading.value = false
  }
}

/** 加载角色权限 */
async function loadRolePermissions() {
  if (!selectedRole.value) return
  try {
    const res = await getRolePermissions(selectedRole.value.id)
    rolePermissions.value = res.data || []
  } catch {
    rolePermissions.value = []
  }
}

/** 加载所有权限 */
async function loadAllPermissions() {
  if (allPermissions.value.length > 0) return
  try {
    const res = await getPermissions({ page: 1, page_size: 1000 })
    allPermissions.value = res.data?.items || []
  } catch {
    allPermissions.value = []
  }
}

/** 添加成员 */
async function handleAddMembers(userIds: string[]) {
  if (!selectedRole.value || userIds.length === 0) return
  try {
    const res = await addRoleMembers(selectedRole.value.id, userIds)
    notifySuccess(`成功添加 ${res.data?.added || 0} 个成员`)
    addMemberDialogOpen.value = false
    await loadRoleMembers()
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
    await loadRoleMembers()
  } catch (error) {
    notifyError(getErrorMessage(error, "移除成员失败"))
  }
}

/** 打开分配权限弹窗 */
async function handleOpenAssignPerm() {
  if (!selectedRole.value) return
  await loadAllPermissions()
  selectedPermIds.value = rolePermissions.value.map((p) => p.id)
  assignPermDialogOpen.value = true
}

/** 切换权限选中 */
function togglePermission(permId: string) {
  const index = selectedPermIds.value.indexOf(permId)
  if (index > -1) {
    selectedPermIds.value.splice(index, 1)
  } else {
    selectedPermIds.value.push(permId)
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
    const res = await getDepartmentTree()
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
    return (res.data?.items || []).map((u) => ({
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
    const res = await getDepartmentMembers(orgId)
    return (res.data || []) as unknown as PeopleItem[]
  } catch {
    return []
  }
}

// 初始化
onMounted(() => {
  loadRoles()
})
</script>

<template>
  <AppPage title="角色管理" variant="workbench" description="管理系统角色、成员和权限">
    <div class="flex gap-4 flex-1 min-h-0">
      <!-- 左侧：角色列表 -->
      <div class="w-[300px] shrink-0 flex flex-col border rounded-lg overflow-hidden">
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
      <div class="flex-1 flex flex-col border rounded-lg overflow-hidden">
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

            <ScrollArea class="flex-1">
              <!-- 角色成员 Tab -->
              <TabsContent value="members" class="p-4 m-0">
                <div class="mb-3 flex items-center justify-between">
                  <span class="text-sm text-muted-foreground">
                    共 {{ members.length }} 个成员
                  </span>
                  <Button size="sm" @click="addMemberDialogOpen = true">
                    <UserPlus class="h-3.5 w-3.5 mr-1" />
                    添加成员
                  </Button>
                </div>

                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>姓名</TableHead>
                      <TableHead>账号</TableHead>
                      <TableHead>邮箱</TableHead>
                      <TableHead>手机</TableHead>
                      <TableHead class="w-[80px]">状态</TableHead>
                      <TableHead class="w-[100px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-if="membersLoading">
                      <TableCell v-for="n in 6" :key="n">
                        <Skeleton class="h-5 w-full" />
                      </TableCell>
                    </TableRow>
                    <TableRow v-else-if="members.length === 0">
                      <TableCell colspan="6" class="h-16 text-center text-muted-foreground">
                        暂无成员
                      </TableCell>
                    </TableRow>
                    <TableRow v-else v-for="member in members" :key="member.user_id">
                      <TableCell class="font-medium">
                        {{ member.nickname || member.username }}
                      </TableCell>
                      <TableCell class="font-mono text-sm">
                        {{ member.username }}
                      </TableCell>
                      <TableCell>{{ member.email || "--" }}</TableCell>
                      <TableCell>{{ member.phone || "--" }}</TableCell>
                      <TableCell>
                        <Badge :variant="member.status === 'active' ? 'default' : 'secondary'">
                          {{ member.status === 'active' ? '启用' : '停用' }}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          class="text-destructive hover:text-destructive"
                          @click="handleRemoveMember(member)"
                        >
                          <X class="h-3.5 w-3.5 mr-1" />
                          移除
                        </Button>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TabsContent>

              <!-- 权限列表 Tab -->
              <TabsContent value="permissions" class="p-4 m-0">
                <div class="mb-3 flex items-center justify-between">
                  <div class="relative flex-1 max-w-[300px]">
                    <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      v-model="permSearchKeyword"
                      placeholder="搜索权限..."
                      class="pl-8"
                    />
                  </div>
                  <Button size="sm" @click="handleOpenAssignPerm">
                    <Settings class="h-3.5 w-3.5 mr-1" />
                    分配权限
                  </Button>
                </div>

                <div v-if="rolePermissions.length === 0" class="py-8 text-center text-muted-foreground">
                  <Shield class="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>暂无权限</p>
                </div>

                <div v-else class="space-y-4">
                  <div
                    v-for="group in filteredPermissionGroups.filter(g => g.permissions.some(p => rolePermissions.some(rp => rp.id === p.id)))"
                    :key="group.resource"
                    class="border rounded-lg p-3"
                  >
                    <h4 class="font-medium text-sm mb-2 flex items-center gap-2">
                      <Shield class="h-4 w-4 text-blue-500" />
                      {{ group.resource }}
                    </h4>
                    <div class="flex flex-wrap gap-2">
                      <Badge
                        v-for="perm in group.permissions.filter(p => rolePermissions.some(rp => rp.id === p.id))"
                        :key="perm.id"
                        variant="secondary"
                      >
                        {{ perm.name }}
                      </Badge>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </ScrollArea>
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
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>分配权限</DialogTitle>
          <DialogDescription>
            为角色「{{ selectedRole?.name }}」分配权限
          </DialogDescription>
        </DialogHeader>

        <div class="mb-3">
          <div class="relative">
            <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
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
                  :checked="selectedPermIds.includes(perm.id)"
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
          <DialogDescription v-if="formDialogMode === "create"">
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
