<script setup lang="ts">
/**
 * UserList — 人员管理页面
 *
 * 布局：
 * - 顶部统计卡片（人员总数、启用账号数、当前部门人数、多角色成员数）
 * - 左侧 300px 组织树筛选
 * - 右侧 DataTable 人员列表 + 多条件筛选 + 行内操作
 */

import { ref, computed, onMounted, h } from "vue"
import type { ColumnDef } from "@tanstack/vue-table"
import {
  Users,
  UserCheck,
  UserX,
  Crown,
  Building2,
  Search,
  RotateCcw,
  Pencil,
  Trash2,
  KeyRound,
  ShieldCheck,
  ShieldOff,
} from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  Input,
  DataTable,
  useDataTable,
} from "@/components"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ScrollArea } from "@/components/ui/scroll-area"
import { confirmAction, notifySuccess, notifyError, getErrorMessage } from "@/framework/utils/feedback"
import type { User, UserStats, Organization, RoleOption } from "@/iam/types"
import {
  getUsers,
  getUserStats,
  getRoleOptions,
  createUser,
  updateUser,
  deleteUser,
  disableUser,
  enableUser,
  resetUserPassword,
  assignUserRoles,
} from "@/iam/api/user"
import { getOrganizationTree } from "@/iam/api/organization"
import UserFormDialog, { type UserSubmitData } from "@/iam/components/UserFormDialog.vue"

// ========== 状态 ==========

// 统计
const stats = ref<UserStats>({ total: 0, enabled: 0, disabled: 0, multi_role: 0 })

// 组织树
const organizationTree = ref<Organization[]>([])

// 角色选项
const roleOptions = ref<RoleOption[]>([])

// 筛选条件
const filters = ref({
  keyword: "",
  status: "__all__",
  role_id: "__all__",
  organization_id: "",
  include_children: true,
})

// 当前选中的组织名称
const selectedOrgName = ref("")

// 弹窗
const formDialogOpen = ref(false)
const formDialogMode = ref<"create" | "edit">("create")
const currentUser = ref<User | null>(null)

// ========== 计算属性 ==========

// 统计卡片数据
const statCards = computed(() => [
  {
    title: "人员总数",
    value: stats.value.total,
    icon: Users,
    color: "text-blue-500",
    description: "全部注册用户",
  },
  {
    title: "启用账号",
    value: stats.value.enabled,
    icon: UserCheck,
    color: "text-green-500",
    description: "状态为激活的用户",
  },
  {
    title: "停用账号",
    value: stats.value.disabled,
    icon: UserX,
    color: "text-red-500",
    description: "状态为停用的用户",
  },
  {
    title: "多角色成员",
    value: stats.value.multi_role,
    icon: Crown,
    color: "text-amber-500",
    description: "拥有 2 个以上角色的用户",
  },
])

// 状态选项
const statusOptions = [
  { label: "全部", value: "__all__" },
  { label: "启用", value: "active" },
  { label: "停用", value: "inactive" },
  { label: "锁定", value: "locked" },
]

// ========== 方法 ==========

/** 状态 Badge 样式 */
function getStatusBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  if (status === "active") return "default"
  if (status === "locked") return "destructive"
  return "secondary"
}

function getStatusLabel(status: string): string {
  if (status === "active") return "启用"
  if (status === "locked") return "锁定"
  return "停用"
}

/** 加载组织树 */
async function loadOrganizationTree() {
  try {
    const res = await getOrganizationTree()
    organizationTree.value = res.data || []
  } catch (error) {
    console.error("加载组织树失败:", error)
  }
}

/** 加载角色选项 */
async function loadRoleOptions() {
  try {
    const res = await getRoleOptions()
    roleOptions.value = res.data || []
  } catch (error) {
    console.error("加载角色选项失败:", error)
  }
}

/** 加载用户统计 */
async function loadStats() {
  try {
    const res = await getUserStats()
    stats.value = res.data || { total: 0, enabled: 0, disabled: 0, multi_role: 0 }
  } catch (error) {
    console.error("加载统计失败:", error)
  }
}

// ========== 列定义 ==========

const userColumns: ColumnDef<User>[] = [
  {
    accessorKey: "username",
    header: "用户名",
    size: 120,
    cell: ({ row }) => h("span", { class: "font-medium" }, row.original.username),
  },
  {
    accessorKey: "nickname",
    header: "昵称",
    size: 100,
    cell: ({ row }) => row.original.nickname || "--",
  },
  {
    accessorKey: "organization_name",
    header: "组织",
    size: 140,
    cell: ({ row }) => row.original.organization_name || "--",
  },
  {
    accessorKey: "email",
    header: "邮箱",
    size: 160,
    cell: ({ row }) => row.original.email || "--",
  },
  {
    accessorKey: "phone",
    header: "手机号",
    size: 120,
    cell: ({ row }) => row.original.phone || "--",
  },
  {
    accessorKey: "status",
    header: "状态",
    size: 80,
    cell: ({ row }) => {
      const status = row.original.status
      return h(Badge, { variant: getStatusBadgeVariant(status) }, () => getStatusLabel(status))
    },
  },
  {
    id: "actions",
    header: "操作",
    size: 180,
    cell: ({ row }) => {
      const user = row.original
      const buttons = [
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleEdit(user) },
          () => h(Pencil, { class: "h-3.5 w-3.5" })
        ),
      ]

      if (user.status === "active") {
        buttons.push(
          h(
            Button,
            { variant: "ghost", size: "sm", onClick: () => handleDisable(user) },
            () => h(ShieldOff, { class: "h-3.5 w-3.5" })
          )
        )
      } else {
        buttons.push(
          h(
            Button,
            { variant: "ghost", size: "sm", onClick: () => handleEnable(user) },
            () => h(ShieldCheck, { class: "h-3.5 w-3.5" })
          )
        )
      }

      buttons.push(
        h(
          Button,
          { variant: "ghost", size: "sm", onClick: () => handleResetPassword(user) },
          () => h(KeyRound, { class: "h-3.5 w-3.5" })
        )
      )

      buttons.push(
        h(
          Button,
          {
            variant: "ghost",
            size: "sm",
            class: "text-destructive hover:text-destructive",
            onClick: () => handleDelete(user),
          },
          () => h(Trash2, { class: "h-3.5 w-3.5" })
        )
      )

      return h("div", { class: "flex items-center gap-1" }, buttons)
    },
  },
]

// ========== 初始化 DataTable ==========

const dataTable = useDataTable<User>({
  columns: userColumns,
  remoteFetchFn: async ({ page, page_size }) => {
    const roleId = filters.value.role_id === "__all__" ? undefined : filters.value.role_id
    const status = filters.value.status === "__all__" ? undefined : filters.value.status
    const res = await getUsers({
      page,
      page_size,
      keyword: filters.value.keyword || undefined,
      status: status,
      role_id: roleId,
      organization_id: filters.value.organization_id || undefined,
      include_children: filters.value.include_children,
    })
    return {
      code: res.code,
      data: res.data || [],
      msg: res.msg,
      page: res.page || page,
      page_size: res.page_size || page_size,
      total: res.total || 0,
    }
  },
})

/** 选择组织筛选 */
function selectOrganization(orgId: string | undefined) {
  filters.value.organization_id = orgId || ""

  // 查找组织名称
  if (orgId) {
    const findOrg = (orgs: Organization[]): Organization | undefined => {
      for (const d of orgs) {
        if (d.id === orgId) return d
        if (d.children) {
          const found = findOrg(d.children)
          if (found) return found
        }
      }
    }
    const org = findOrg(organizationTree.value)
    selectedOrgName.value = org?.name || ""
  } else {
    selectedOrgName.value = ""
  }

  dataTable.refresh(true)
}

/** 搜索 */
function handleSearch() {
  dataTable.refresh(true)
}

/** 重置筛选 */
function handleReset() {
  filters.value = { keyword: "", status: "__all__", role_id: "__all__", organization_id: "", include_children: true }
  selectedOrgName.value = ""
  dataTable.refresh(true)
}

/** 创建用户 */
function handleCreate() {
  currentUser.value = null
  formDialogMode.value = "create"
  formDialogOpen.value = true
}

/** 编辑用户 */
function handleEdit(user: User) {
  currentUser.value = user
  formDialogMode.value = "edit"
  formDialogOpen.value = true
}

/** 提交用户表单 */
async function handleFormSubmit(data: UserSubmitData) {
  try {
    if (formDialogMode.value === "edit" && currentUser.value) {
      await updateUser(currentUser.value.id, {
        nickname: data.nickname,
        email: data.email,
        phone: data.phone,
      })
      if (data.role_ids.length > 0) {
        await assignUserRoles(currentUser.value.id, data.role_ids)
      }
      notifySuccess("更新成功")
    } else {
      await createUser({
        username: data.username,
        password: data.password!,
        nickname: data.nickname,
        email: data.email,
        phone: data.phone,
      })
      notifySuccess("创建成功")
    }

    formDialogOpen.value = false
    await Promise.all([dataTable.refresh(), loadStats()])
  } catch (error) {
    notifyError(getErrorMessage(error, "操作失败"))
  }
}

/** 启用用户 */
async function handleEnable(user: User) {
  try {
    await enableUser(user.id)
    notifySuccess("已启用")
    await Promise.all([dataTable.refresh(), loadStats()])
  } catch (error) {
    notifyError(getErrorMessage(error, "启用失败"))
  }
}

/** 停用用户 */
async function handleDisable(user: User) {
  if (!await confirmAction(`确定要停用「${user.nickname || user.username}」吗？`)) return

  try {
    await disableUser(user.id)
    notifySuccess("已停用")
    await Promise.all([dataTable.refresh(), loadStats()])
  } catch (error) {
    notifyError(getErrorMessage(error, "停用失败"))
  }
}

/** 重置密码 */
async function handleResetPassword(user: User) {
  if (!await confirmAction(`确定要重置「${user.nickname || user.username}」的密码吗？`)) return

  try {
    const res = await resetUserPassword(user.id)
    notifySuccess(`密码已重置为: ${res.data?.password || "(已生成)"}`)
  } catch (error) {
    notifyError(getErrorMessage(error, "重置密码失败"))
  }
}

/** 删除用户 */
async function handleDelete(user: User) {
  if (!await confirmAction(`确定要删除「${user.nickname || user.username}」吗？删除后不可恢复。`)) return

  try {
    await deleteUser(user.id)
    notifySuccess("删除成功")
    await Promise.all([dataTable.refresh(), loadStats()])
  } catch (error) {
    notifyError(getErrorMessage(error, "删除失败"))
  }
}

// 初始化
onMounted(() => {
  loadOrganizationTree()
  loadRoleOptions()
  loadStats()
})
</script>

<template>
  <AppPage title="人员管理" variant="workbench" description="管理系统用户，查看人员统计，按组织筛选">
    <!-- 操作按钮 -->
    <template #actions>
      <div class="flex items-center gap-2">
        <Button @click="handleCreate">
          <Users class="mr-1 h-4 w-4" />
          新增人员
        </Button>
      </div>
    </template>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-4 gap-4 mb-4">
      <div
        v-for="card in statCards"
        :key="card.title"
        class="border rounded-lg p-4 bg-card"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">{{ card.title }}</p>
            <p class="text-2xl font-bold mt-1">{{ card.value }}</p>
            <p class="text-xs text-muted-foreground mt-1">{{ card.description }}</p>
          </div>
          <component :is="card.icon" class="h-8 w-8 opacity-20" :class="card.color" />
        </div>
      </div>
    </div>

    <div class="flex min-h-0 flex-1 gap-4">
      <!-- 左侧：组织树筛选 -->
      <div class="w-[300px] shrink-0 flex flex-col border rounded-lg overflow-hidden">
        <div class="p-3 border-b bg-muted/30 flex items-center justify-between">
          <span class="text-sm font-medium">组织筛选</span>
          <Button
            v-if="filters.organization_id"
            variant="ghost"
            size="sm"
            class="h-6 px-2 text-xs"
            @click="selectOrganization(undefined)"
          >
            查看全部
          </Button>
        </div>

        <ScrollArea class="min-h-0 flex-1 px-3 py-3">
          <div v-if="organizationTree.length === 0" class="p-4 text-center text-muted-foreground text-sm">
            暂无组织数据
          </div>

          <div v-else class="py-1">
            <template v-for="org in organizationTree" :key="org.id">
              <button
                class="flex items-center w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left"
                :class="{ 'bg-accent': filters.organization_id === org.id }"
                @click="selectOrganization(org.id)"
              >
                <Building2 class="h-4 w-4 mr-2 shrink-0 text-blue-500" />
                <span class="truncate">{{ org.name }}</span>
                <Badge v-if="org.total_member_count" variant="secondary" class="ml-auto shrink-0 text-xs">
                  {{ org.total_member_count }}
                </Badge>
              </button>
              <!-- 子节点 -->
              <template v-if="org.children" v-for="child in org.children" :key="child.id">
                <button
                  class="flex items-center w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left pl-8"
                  :class="{ 'bg-accent': filters.organization_id === child.id }"
                  @click="selectOrganization(child.id)"
                >
                  <Building2 class="h-4 w-4 mr-2 shrink-0 text-blue-500" />
                  <span class="truncate">{{ child.name }}</span>
                </button>
              </template>
            </template>
          </div>
        </ScrollArea>
      </div>

      <!-- 右侧：用户列表 -->
      <div class="flex min-w-0 flex-1 flex-col border rounded-lg overflow-hidden">
        <!-- 筛选栏 -->
        <div class="p-3 border-b bg-muted/30">
          <div class="flex flex-wrap items-end gap-3">
            <div class="flex flex-col gap-1">
              <span class="text-xs text-muted-foreground">关键词</span>
              <Input
                v-model="filters.keyword"
                placeholder="姓名/账号/手机号"
                class="w-[180px]"
                @keyup.enter="handleSearch"
              />
            </div>
            <div class="flex flex-col gap-1">
              <span class="text-xs text-muted-foreground">状态</span>
              <Select v-model="filters.status">
                <SelectTrigger class="w-[100px]">
                  <SelectValue placeholder="全部" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="flex flex-col gap-1">
              <span class="text-xs text-muted-foreground">角色</span>
              <Select v-model="filters.role_id">
                <SelectTrigger class="w-[140px]">
                  <SelectValue placeholder="全部角色" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">全部角色</SelectItem>
                  <SelectItem v-for="role in roleOptions" :key="role.id" :value="role.id">
                    {{ role.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button size="sm" @click="handleSearch">
              <Search class="mr-1 h-4 w-4" />
              搜索
            </Button>
            <Button variant="outline" size="sm" @click="handleReset">
              <RotateCcw class="mr-1 h-4 w-4" />
              重置
            </Button>
          </div>
        </div>

        <!-- 用户列表 -->
        <div class="flex min-h-0 flex-1 flex-col p-3">
          <DataTable :data-table="dataTable" :fixed-layout="true" />
        </div>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <UserFormDialog
      v-model:open="formDialogOpen"
      :mode="formDialogMode"
      :user="currentUser"
      @submit="handleFormSubmit"
    />
  </AppPage>
</template>
