<script setup lang="ts">
/**
 * UserList — 人员管理页面
 *
 * 布局：
 * - 顶部统计卡片（人员总数、启用账号数、当前部门人数、多角色成员数）
 * - 左侧 300px 部门树筛选
 * - 右侧 DataTable 人员列表 + 多条件筛选 + 行内操作
 */

import { ref, computed, onMounted, watch } from "vue"
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
  Skeleton,
  DataTable,
  DataTablePagination,
  useDataTable,
  type DescriptionItem,
  Input,
  TreeSelect,
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
import type { User, UserStats, Department, RoleOption } from "@/iam/types"
import type { TreeSelectNode } from "@/framework/types/tree"
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
import { getDepartmentTree } from "@/iam/api/department"
import UserFormDialog, { type UserSubmitData } from "@/iam/components/UserFormDialog.vue"

// ========== 状态 ==========

const loading = ref(false)
const users = ref<User[]>([])
const total = ref(0)

// 统计
const stats = ref<UserStats>({ total: 0, enabled: 0, disabled: 0, multi_role: 0 })

// 部门树
const departmentTree = ref<Department[]>([])

// 角色选项
const roleOptions = ref<RoleOption[]>([])

// 筛选条件
const filters = ref({
  keyword: "",
  status: "",
  role_id: "",
  dept_id: "",
  include_children: true,
})

// 分页
const pagination = ref({ page: 1, pageSize: 20 })

// 当前选中的部门名称
const selectedDeptName = ref("")

// 弹窗
const formDialogOpen = ref(false)
const formDialogMode = ref<"create" | "edit">("create")
const currentUser = ref<User | null>(null)

// ========== 计算属性 ==========

// 将 Department 转换为 TreeSelectNode
const treeSelectData = computed<TreeSelectNode[]>(() => {
  function toNodes(depts: Department[]): TreeSelectNode[] {
    return depts.map((d) => ({
      id: d.id,
      name: d.name,
      children: d.children ? toNodes(d.children) : undefined,
      isLeaf: !d.children || d.children.length === 0,
    }))
  }
  return toNodes(departmentTree.value)
})

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
  { label: "全部", value: "" },
  { label: "启用", value: "active" },
  { label: "停用", value: "inactive" },
  { label: "锁定", value: "locked" },
]

// ========== DataTable 配置 ==========

const columns = [
  { key: "username", header: "用户名", width: "120px" },
  { key: "nickname", header: "昵称", width: "100px" },
  { key: "dept_name", header: "部门", width: "140px" },
  { key: "email", header: "邮箱", width: "160px" },
  { key: "phone", header: "手机号", width: "120px" },
  { key: "status", header: "状态", width: "80px" },
  { key: "actions", header: "操作", width: "200px" },
]

const { dataTable } = useDataTable({
  columns,
  data: users,
  total,
  pageSize: pagination.value.pageSize,
  getRowId: (row) => row.id,
})

// ========== 方法 ==========

/** 加载部门树 */
async function loadDepartmentTree() {
  try {
    const res = await getDepartmentTree()
    departmentTree.value = res.data || []
  } catch (error) {
    console.error("加载部门树失败:", error)
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

/** 加载用户列表 */
async function loadUsers() {
  loading.value = true
  try {
    const res = await getUsers({
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      keyword: filters.value.keyword || undefined,
      status: filters.value.status || undefined,
      dept_id: filters.value.dept_id || undefined,
      include_children: filters.value.include_children,
    })
    users.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (error) {
    notifyError(getErrorMessage(error, "加载用户列表失败"))
  } finally {
    loading.value = false
  }
}

/** 选择部门筛选 */
function selectDepartment(deptId: string | undefined) {
  filters.value.dept_id = deptId || ""
  pagination.value.page = 1

  // 查找部门名称
  if (deptId) {
    const findDept = (depts: Department[]): Department | undefined => {
      for (const d of depts) {
        if (d.id === deptId) return d
        if (d.children) {
          const found = findDept(d.children)
          if (found) return found
        }
      }
    }
    const dept = findDept(departmentTree.value)
    selectedDeptName.value = dept?.name || ""
  } else {
    selectedDeptName.value = ""
  }

  loadUsers()
}

/** 搜索 */
function handleSearch() {
  pagination.value.page = 1
  loadUsers()
}

/** 重置筛选 */
function handleReset() {
  filters.value = { keyword: "", status: "", role_id: "", dept_id: "", include_children: true }
  pagination.value.page = 1
  selectedDeptName.value = ""
  loadUsers()
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
    await Promise.all([loadUsers(), loadStats()])
  } catch (error) {
    notifyError(getErrorMessage(error, "操作失败"))
  }
}

/** 启用用户 */
async function handleEnable(user: User) {
  try {
    await enableUser(user.id)
    notifySuccess("已启用")
    await Promise.all([loadUsers(), loadStats()])
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
    await Promise.all([loadUsers(), loadStats()])
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
    await Promise.all([loadUsers(), loadStats()])
  } catch (error) {
    notifyError(getErrorMessage(error, "删除失败"))
  }
}

/** 分页变化 */
function handlePageChange(page: number) {
  pagination.value.page = page
  loadUsers()
}

function handlePageSizeChange(pageSize: number) {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadUsers()
}

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

// 初始化
onMounted(() => {
  loadDepartmentTree()
  loadRoleOptions()
  loadStats()
  loadUsers()
})
</script>

<template>
  <AppPage title="人员管理" variant="workbench" description="管理系统用户，查看人员统计，按部门筛选">
    <!-- 操作按钮 -->
    <template #actions>
      <Button @click="handleCreate">
        <Users class="mr-1 h-4 w-4" />
        新增人员
      </Button>
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

    <div class="flex gap-4 flex-1 min-h-0">
      <!-- 左侧：部门树筛选 -->
      <div class="w-[300px] shrink-0 flex flex-col border rounded-lg overflow-hidden">
        <div class="p-3 border-b bg-muted/30 flex items-center justify-between">
          <span class="text-sm font-medium">组织筛选</span>
          <Button
            v-if="filters.dept_id"
            variant="ghost"
            size="sm"
            class="h-6 px-2 text-xs"
            @click="selectDepartment(undefined)"
          >
            查看全部
          </Button>
        </div>

        <ScrollArea class="flex-1">
          <div v-if="departmentTree.length === 0" class="p-4 text-center text-muted-foreground text-sm">
            暂无组织数据
          </div>

          <div v-else class="py-1">
            <template v-for="dept in departmentTree" :key="dept.id">
              <button
                class="flex items-center w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left"
                :class="{ 'bg-accent': filters.dept_id === dept.id }"
                @click="selectDepartment(dept.id)"
              >
                <Building2 class="h-4 w-4 mr-2 shrink-0 text-blue-500" />
                <span class="truncate">{{ dept.name }}</span>
                <Badge v-if="dept.total_member_count" variant="secondary" class="ml-auto shrink-0 text-xs">
                  {{ dept.total_member_count }}
                </Badge>
              </button>
              <!-- 子节点 -->
              <template v-if="dept.children" v-for="child in dept.children" :key="child.id">
                <button
                  class="flex items-center w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left pl-8"
                  :class="{ 'bg-accent': filters.dept_id === child.id }"
                  @click="selectDepartment(child.id)"
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
      <div class="flex-1 flex flex-col border rounded-lg overflow-hidden">
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
                  <SelectItem value="">全部角色</SelectItem>
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

        <!-- DataTable -->
        <div class="flex-1 overflow-auto">
          <DataTable :data-table="dataTable">
            <template #cell-username="{ row }">
              <span class="font-medium">{{ row.username }}</span>
            </template>
            <template #cell-nickname="{ row }">
              {{ row.nickname || "--" }}
            </template>
            <template #cell-dept_name="{ row }">
              {{ row.dept_name || "--" }}
            </template>
            <template #cell-email="{ row }">
              {{ row.email || "--" }}
            </template>
            <template #cell-phone="{ row }">
              {{ row.phone || "--" }}
            </template>
            <template #cell-status="{ row }">
              <Badge :variant="getStatusBadgeVariant(row.status)">
                {{ getStatusLabel(row.status) }}
              </Badge>
            </template>
            <template #cell-actions="{ row }">
              <div class="flex items-center gap-1">
                <Button variant="ghost" size="sm" @click="handleEdit(row)">
                  <Pencil class="h-3.5 w-3.5" />
                </Button>
                <Button
                  v-if="row.status === 'active'"
                  variant="ghost"
                  size="sm"
                  @click="handleDisable(row)"
                >
                  <ShieldOff class="h-3.5 w-3.5" />
                </Button>
                <Button
                  v-else
                  variant="ghost"
                  size="sm"
                  @click="handleEnable(row)"
                >
                  <ShieldCheck class="h-3.5 w-3.5" />
                </Button>
                <Button variant="ghost" size="sm" @click="handleResetPassword(row)">
                  <KeyRound class="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  class="text-destructive hover:text-destructive"
                  @click="handleDelete(row)"
                >
                  <Trash2 class="h-3.5 w-3.5" />
                </Button>
              </div>
            </template>
          </DataTable>
        </div>

        <!-- 分页 -->
        <div class="p-3 border-t">
          <DataTablePagination
            :table="dataTable.table"
            @page-change="handlePageChange"
            @page-size-change="handlePageSizeChange"
          />
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
