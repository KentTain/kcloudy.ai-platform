<script setup lang="ts">
/**
 * DepartmentPage — 部门管理页面
 *
 * 布局参照 kbhub organization.vue:
 * - Header: 左侧标题 + 描述，右侧操作按钮组（根据选中状态动态禁用）
 * - Body: 左侧 300px 组织树 + 右侧 Tabs（组织信息、下级组织、直属成员）
 */

import { ref, computed, onMounted, watch } from "vue"
import { useRouter } from "vue-router"
import {
  Building2,
  Plus,
  Pencil,
  Trash2,
  Users,
  FolderTree,
  Info,
  Search,
  UserPlus,
} from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  Skeleton,
  DescriptionList,
  type DescriptionItem,
  Table,
  Input,
  PeopleSelectDialog,
  type OrgTreeNode,
  type PeopleItem,
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
import type { Department, DepartmentDetail, DepartmentUser } from "@/iam/types"
import {
  getDepartmentTree,
  getDepartmentDetail,
  createDepartment,
  updateDepartment,
  deleteDepartment,
  getDepartmentMembers,
  batchAddDepartmentUsers,
  enableDepartmentUser,
  disableDepartmentUser,
  removeDepartmentUser,
} from "@/iam/api/department"
import CreateDepartmentDialog, { type SubmitData } from "@/iam/components/CreateDepartmentDialog.vue"

const router = useRouter()

// ========== 状态 ==========

const loading = ref(false)
const departmentTree = ref<Department[]>([])
const selectedId = ref<string | null>(null)
const selectedDepartment = ref<DepartmentDetail | null>(null)
const detailLoading = ref(false)

// 搜索
const searchKeyword = ref("")

// 弹窗
const createDialogOpen = ref(false)
const createDialogMode = ref<"create-root" | "create-child" | "create-sibling" | "edit">("create-root")

// Tabs
const activeTab = ref("info")

// 下级组织
const childDepartments = ref<Department[]>([])

// 直属成员
const members = ref<DepartmentUser[]>([])
const membersLoading = ref(false)

// 添加成员弹窗
const addMemberDialogOpen = ref(false)

// ========== 计算属性 ==========

const hasSelection = computed(() => !!selectedId.value)

// ========== 方法 ==========

/** 加载组织树 */
async function loadTree() {
  loading.value = true
  try {
    const res = await getDepartmentTree()
    departmentTree.value = res.data || []
  } catch (error) {
    notifyError(getErrorMessage(error, "加载组织树失败"))
  } finally {
    loading.value = false
  }
}

/** 选择组织节点 */
async function selectDepartment(dept: Department) {
  selectedId.value = dept.id
  await loadDepartmentDetail()
}

/** 加载组织详情 */
async function loadDepartmentDetail() {
  if (!selectedId.value) return

  detailLoading.value = true
  try {
    const [detailRes, membersRes] = await Promise.all([
      getDepartmentDetail(selectedId.value),
      getDepartmentMembers(selectedId.value),
    ])
    selectedDepartment.value = detailRes.data
    members.value = membersRes.data || []

    // 提取下级组织
    const findChildren = (items: Department[], parentId: string): Department[] => {
      return items.filter((item) => item.parent_id === parentId)
    }
    childDepartments.value = findChildren(departmentTree.value, selectedId.value)
  } catch (error) {
    notifyError(getErrorMessage(error, "加载组织详情失败"))
  } finally {
    detailLoading.value = false
  }
}

/** 组织信息描述项 */
const infoItems = computed<DescriptionItem[]>(() => {
  const dept = selectedDepartment.value
  if (!dept) return []
  return [
    { label: "组织名称", value: dept.name },
    { label: "组织编码", value: dept.code || "--" },
    { label: "组织路径", value: dept.path || "--" },
    { label: "排序号", value: String(dept.sort_order) },
    { label: "直属成员数", value: String(dept.direct_member_count) },
    { label: "累计成员数", value: String(dept.total_member_count) },
    { label: "状态", value: dept.status === "active" ? "启用" : "停用" },
  ]
})

/** 搜索过滤 */
const filteredTree = computed(() => {
  if (!searchKeyword.value.trim()) return departmentTree.value

  const keyword = searchKeyword.value.toLowerCase()

  function filterNodes(nodes: Department[]): Department[] {
    return nodes.reduce<Department[]>((acc, node) => {
      const matches = node.name.toLowerCase().includes(keyword) || (node.code?.toLowerCase().includes(keyword) ?? false)
      const filteredChildren = node.children ? filterNodes(node.children) : []

      if (matches || filteredChildren.length > 0) {
        acc.push({ ...node, children: filteredChildren.length > 0 ? filteredChildren : node.children })
      }

      return acc
    }, [])
  }

  return filterNodes(departmentTree.value)
})

/** 新增一级组织 */
function handleAddRoot() {
  createDialogMode.value = "create-root"
  createDialogOpen.value = true
}

/** 新增子组织 */
function handleAddChild() {
  createDialogMode.value = "create-child"
  createDialogOpen.value = true
}

/** 新增同级 */
function handleAddSibling() {
  createDialogMode.value = "create-sibling"
  createDialogOpen.value = true
}

/** 编辑 */
function handleEdit() {
  createDialogMode.value = "edit"
  createDialogOpen.value = true
}

/** 删除 */
async function handleDelete() {
  if (!selectedId.value) return

  if (!await confirmAction(`确定要删除组织「${selectedDepartment.value?.name}」吗？删除后不可恢复。`)) {
    return
  }

  try {
    await deleteDepartment(selectedId.value)
    notifySuccess("删除成功")
    selectedId.value = null
    selectedDepartment.value = null
    await loadTree()
  } catch (error) {
    notifyError(getErrorMessage(error, "删除失败"))
  }
}

/** 提交创建/编辑 */
async function handleCreateSubmit(data: SubmitData) {
  try {
    if (createDialogMode.value === "edit" && selectedId.value) {
      await updateDepartment(selectedId.value, data)
      notifySuccess("更新成功")
    } else {
      // 创建时根据 mode 决定 parent_id
      let parentId = data.parent_id
      if (createDialogMode.value === "create-child" && selectedId.value) {
        parentId = selectedId.value
      } else if (createDialogMode.value === "create-sibling" && selectedDepartment.value) {
        parentId = selectedDepartment.value.parent_id || undefined
      } else if (createDialogMode.value === "create-root") {
        parentId = undefined
      }

      await createDepartment({ ...data, parent_id: parentId })
      notifySuccess("创建成功")
    }

    createDialogOpen.value = false
    await loadTree()
  } catch (error) {
    notifyError(getErrorMessage(error, "操作失败"))
  }
}

/** 查看下级组织 */
function viewChildDepartment(dept: Department) {
  selectDepartment(dept)
}

/** 添加成员 */
function handleAddMembers() {
  addMemberDialogOpen.value = true
}

/** 确认添加成员 */
async function handleConfirmMembers(userIds: string[]) {
  if (!selectedId.value || userIds.length === 0) return

  try {
    const res = await batchAddDepartmentUsers(selectedId.value, userIds)
    notifySuccess(`成功添加 ${res.data?.added || 0} 个成员`)
    await loadDepartmentDetail()
  } catch (error) {
    notifyError(getErrorMessage(error, "添加成员失败"))
  }
}

/** 启用成员 */
async function handleEnableMember(user: DepartmentUser) {
  if (!selectedId.value) return

  try {
    await enableDepartmentUser(selectedId.value, user.user_id)
    notifySuccess("已启用")
    await loadDepartmentDetail()
  } catch (error) {
    notifyError(getErrorMessage(error, "启用失败"))
  }
}

/** 停用成员 */
async function handleDisableMember(user: DepartmentUser) {
  if (!selectedId.value) return

  if (!await confirmAction(`确定要停用「${user.nickname || user.username}」吗？`)) {
    return
  }

  try {
    await disableDepartmentUser(selectedId.value, user.user_id)
    notifySuccess("已停用")
    await loadDepartmentDetail()
  } catch (error) {
    notifyError(getErrorMessage(error, "停用失败"))
  }
}

/** 移除成员 */
async function handleRemoveMember(user: DepartmentUser) {
  if (!selectedId.value) return

  if (!await confirmAction(`确定要将「${user.nickname || user.username}」移出本组织吗？`)) {
    return
  }

  try {
    await removeDepartmentUser(selectedId.value, user.user_id)
    notifySuccess("已移除")
    await loadDepartmentDetail()
  } catch (error) {
    notifyError(getErrorMessage(error, "移除失败"))
  }
}

// PeopleSelectDialog API 回调
async function loadOrgNodesCallback(): Promise<OrgTreeNode[]> {
  try {
    const res = await getDepartmentTree()
    const depts = res.data || []
    function toOrgTreeNodes(nodes: Department[]): OrgTreeNode[] {
      return nodes.map((d) => ({
        id: d.id,
        name: d.name,
        code: d.code,
        parent_id: d.parent_id,
        has_user_num: d.direct_member_count || 0,
        has_org_num: d.children?.length || 0,
        tree_leaf: !d.children || d.children.length === 0,
        children: d.children ? toOrgTreeNodes(d.children) : undefined,
      }))
    }
    return toOrgTreeNodes(depts)
  } catch {
    return []
  }
}

async function searchPeopleCallback(keyword: string): Promise<PeopleItem[]> {
  try {
    const { getUsers } = await import("@/iam/api/user")
    const res = await getUsers({ keyword, page: 1, page_size: 100 })
    const users = res.data?.items || []
    return users.map((u) => ({
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
    return (res.data || []) as PeopleItem[]
  } catch {
    return []
  }
}

// 初始化
onMounted(() => {
  loadTree()
})
</script>

<template>
  <AppPage title="部门管理" variant="workbench" description="管理组织架构，添加、编辑、删除部门，查看部门成员">
    <!-- Header 操作按钮 -->
    <template #actions>
      <div class="flex items-center gap-2">
        <Button :disabled="!hasSelection" @click="handleAddSibling">
          <Plus class="mr-1 h-4 w-4" />
          新增同级
        </Button>
        <Button :disabled="!hasSelection" @click="handleAddChild">
          <Plus class="mr-1 h-4 w-4" />
          新增子组织
        </Button>
        <Button variant="outline" :disabled="!hasSelection" @click="handleEdit">
          <Pencil class="mr-1 h-4 w-4" />
          编辑
        </Button>
        <Button variant="destructive" :disabled="!hasSelection" @click="handleDelete">
          <Trash2 class="mr-1 h-4 w-4" />
          删除
        </Button>
      </div>
    </template>

    <!-- Body -->
    <div class="flex gap-4 h-[calc(100vh-200px)]">
      <!-- 左侧：组织树 -->
      <div class="w-[300px] shrink-0 flex flex-col border rounded-lg overflow-hidden">
        <div class="p-3 border-b bg-muted/30">
          <div class="relative">
            <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              v-model="searchKeyword"
              placeholder="搜索组织..."
              class="pl-8"
            />
          </div>
        </div>

        <ScrollArea class="flex-1">
          <div v-if="loading" class="p-3 space-y-2">
            <Skeleton v-for="i in 8" :key="i" class="h-6 w-full" />
          </div>

          <div v-else-if="filteredTree.length === 0" class="p-4 text-center text-muted-foreground text-sm">
            {{ searchKeyword ? "未找到匹配的组织" : "暂无组织数据" }}
          </div>

          <div v-else class="py-1">
            <template v-for="dept in filteredTree" :key="dept.id">
              <button
                class="flex items-center w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left"
                :class="{ 'bg-accent': selectedId === dept.id }"
                @click="selectDepartment(dept)"
              >
                <Building2 class="h-4 w-4 mr-2 shrink-0 text-blue-500" />
                <span class="truncate">{{ dept.name }}</span>
                <Badge v-if="dept.children?.length" variant="secondary" class="ml-auto shrink-0 text-xs">
                  {{ dept.children.length }}
                </Badge>
              </button>
              <!-- 子节点 -->
              <template v-if="dept.children" v-for="child in dept.children" :key="child.id">
                <button
                  class="flex items-center w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left pl-8"
                  :class="{ 'bg-accent': selectedId === child.id }"
                  @click="selectDepartment(child)"
                >
                  <Building2 class="h-4 w-4 mr-2 shrink-0 text-blue-500" />
                  <span class="truncate">{{ child.name }}</span>
                </button>
              </template>
            </template>
          </div>
        </ScrollArea>

        <div class="p-2 border-t">
          <Button variant="outline" class="w-full" @click="handleAddRoot">
            <Plus class="mr-1 h-4 w-4" />
            新增一级组织
          </Button>
        </div>
      </div>

      <!-- 右侧：详情 + Tabs -->
      <div class="flex-1 flex flex-col border rounded-lg overflow-hidden">
        <template v-if="selectedDepartment">
          <!-- 头部信息 -->
          <div class="p-4 border-b bg-muted/20">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-lg font-semibold">{{ selectedDepartment.name }}</h2>
                <p class="text-sm text-muted-foreground mt-1">
                  {{ selectedDepartment.path || "根级组织" }}
                </p>
              </div>
              <div class="flex items-center gap-4 text-sm">
                <div class="flex items-center gap-1">
                  <Users class="h-4 w-4 text-muted-foreground" />
                  <span>直属成员 {{ selectedDepartment.direct_member_count }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <FolderTree class="h-4 w-4 text-muted-foreground" />
                  <span>下级组织 {{ selectedDepartment.children_count }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Tabs -->
          <Tabs v-model="activeTab" class="flex-1 flex flex-col">
            <div class="px-4 pt-2 border-b">
              <TabsList>
                <TabsTrigger value="info">
                  <Info class="h-4 w-4 mr-1" />
                  组织信息
                </TabsTrigger>
                <TabsTrigger value="children">
                  <FolderTree class="h-4 w-4 mr-1" />
                  下级组织
                </TabsTrigger>
                <TabsTrigger value="members">
                  <Users class="h-4 w-4 mr-1" />
                  直属成员
                </TabsTrigger>
              </TabsList>
            </div>

            <ScrollArea class="flex-1">
              <!-- 组织信息 Tab -->
              <TabsContent value="info" class="p-4 m-0">
                <DescriptionList :items="infoItems" :columns="2" bordered />
              </TabsContent>

              <!-- 下级组织 Tab -->
              <TabsContent value="children" class="p-4 m-0">
                <div v-if="childDepartments.length === 0" class="py-8 text-center text-muted-foreground">
                  当前组织暂无下级组织
                </div>
                <Table v-else>
                  <TableHeader>
                    <TableRow>
                      <TableHead>组织名称</TableHead>
                      <TableHead>组织编码</TableHead>
                      <TableHead>成员数</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead class="w-[80px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="dept in childDepartments" :key="dept.id">
                      <TableCell class="font-medium">{{ dept.name }}</TableCell>
                      <TableCell>{{ dept.code || "--" }}</TableCell>
                      <TableCell>--</TableCell>
                      <TableCell>
                        <Badge :variant="dept.status === 'active' ? 'default' : 'secondary'">
                          {{ dept.status === "active" ? "启用" : "停用" }}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button variant="link" size="sm" @click="viewChildDepartment(dept)">
                          查看
                        </Button>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TabsContent>

              <!-- 直属成员 Tab -->
              <TabsContent value="members" class="p-4 m-0">
                <div class="flex items-center justify-between mb-3">
                  <p class="text-sm text-muted-foreground">
                    当前组织的直属成员，不包含下级组织的成员
                  </p>
                  <Button size="sm" @click="handleAddMembers">
                    <UserPlus class="mr-1 h-4 w-4" />
                    添加成员
                  </Button>
                </div>

                <div v-if="membersLoading" class="py-4">
                  <Skeleton v-for="i in 5" :key="i" class="h-10 w-full mb-2" />
                </div>

                <div v-else-if="members.length === 0" class="py-8 text-center text-muted-foreground">
                  当前组织暂无直属成员
                </div>

                <Table v-else>
                  <TableHeader>
                    <TableRow>
                      <TableHead>姓名</TableHead>
                      <TableHead>账号</TableHead>
                      <TableHead>联系方式</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead class="w-[160px]">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="member in members" :key="member.user_id">
                      <TableCell class="font-medium">
                        {{ member.nickname || member.username }}
                      </TableCell>
                      <TableCell>{{ member.username }}</TableCell>
                      <TableCell>{{ member.phone || member.email || "--" }}</TableCell>
                      <TableCell>
                        <Badge :variant="member.status === 'active' ? 'default' : 'secondary'">
                          {{ member.status === "active" ? "启用" : "停用" }}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div class="flex items-center gap-1">
                          <Button
                            v-if="member.status === 'active'"
                            variant="ghost"
                            size="sm"
                            @click="handleDisableMember(member)"
                          >
                            停用
                          </Button>
                          <Button
                            v-else
                            variant="ghost"
                            size="sm"
                            @click="handleEnableMember(member)"
                          >
                            启用
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            class="text-destructive hover:text-destructive"
                            @click="handleRemoveMember(member)"
                          >
                            移除
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TabsContent>
            </ScrollArea>
          </Tabs>
        </template>

        <div v-else class="flex-1 flex items-center justify-center text-muted-foreground">
          <div class="text-center">
            <Building2 class="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>请选择左侧组织查看详情</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <CreateDepartmentDialog
      v-model:open="createDialogOpen"
      :mode="createDialogMode"
      :current-department="selectedDepartment"
      :department-tree="departmentTree"
      @submit="handleCreateSubmit"
    />

    <!-- 添加成员弹窗 -->
    <PeopleSelectDialog
      v-model:open="addMemberDialogOpen"
      title="选择人员"
      :multiple="true"
      :disabled-ids="members.map((m) => m.user_id)"
      :load-org-nodes="loadOrgNodesCallback"
      :search-people="searchPeopleCallback"
      :load-org-people="loadOrgPeopleCallback"
      @confirm="(ids, _users) => handleConfirmMembers(ids)"
    />
  </AppPage>
</template>
