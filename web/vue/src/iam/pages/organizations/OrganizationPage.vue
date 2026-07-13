<script setup lang="ts">
/**
 * OrganizationPage — 组织管理页面
 *
 * 布局参照 kbhub organization.vue:
 * - Header: 左侧标题 + 描述，右侧操作按钮组（根据选中状态动态禁用）
 * - Body: 左侧 300px 组织树 + 右侧 Tabs（组织信息、下级组织、直属成员）
 */

import { ref, computed, onMounted, h, defineComponent, type PropType, type VNodeChild } from "vue"
import { useRouter } from "vue-router"
import type { ColumnDef } from "@tanstack/vue-table"
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
  DataTable,
  useDataTable,
  Input,
  PeopleSelectDialog,
  type OrgTreeNode,
  type PeopleItem,
} from "@/components"
import { ChildOrgRowActions, OrgMemberRowActions } from "@/iam/components"
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
import type { Organization, OrganizationDetail, OrganizationUser } from "@/iam/types"
import {
  getOrganizationTree,
  getOrganizationDetail,
  createOrganization,
  updateOrganization,
  deleteOrganization,
  getOrganizationMembers,
  batchAddOrganizationUsers,
  enableOrganizationUser,
  disableOrganizationUser,
  removeOrganizationUser,
} from "@/iam/api/organization"
import CreateOrganizationDialog, { type SubmitData } from "@/iam/components/CreateOrganizationDialog.vue"

const router = useRouter()

// ========== 递归树节点组件 ==========

const OrganizationTreeNode = defineComponent({
  name: "OrganizationTreeNode",
  props: {
    organizations: { type: Array as PropType<Organization[]>, required: true },
    selectedId: { type: String as PropType<string | null>, default: null },
    depth: { type: Number, default: 0 },
  },
  emits: ["select"],
  setup(props, { emit }) {
    return (): VNodeChild[] => {
      const nodes: VNodeChild[] = []
      for (const org of props.organizations) {
        const isSelected = props.selectedId === org.id
        const indent = 12 + props.depth * 20

        nodes.push(
          h(
            "button",
            {
              class: [
                "flex items-center w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left",
                { "bg-accent": isSelected },
              ],
              style: { paddingLeft: `${indent}px` },
              "data-testid": "org-tree-node",
              "data-org-id": org.id,
              "data-org-name": org.name,
              onClick: () => emit("select", org),
            },
            [
              h(Building2, { class: "h-4 w-4 mr-2 shrink-0 text-blue-500" }),
              h("span", { class: "truncate" }, org.name),
              org.children?.length
                ? h(
                    Badge,
                    { variant: "secondary", class: "ml-auto shrink-0 text-xs" },
                    () => String(org.children!.length),
                  )
                : null,
            ],
          ),
        )
        if (org.children?.length) {
          nodes.push(
            h(OrganizationTreeNode, {
              organizations: org.children,
              selectedId: props.selectedId,
              depth: props.depth + 1,
              onSelect: (org: Organization) => emit("select", org),
            }),
          )
        }
      }
      return nodes
    }
  },
})

// ========== 状态 ==========

const loading = ref(false)
const organizationTree = ref<Organization[]>([])
const selectedId = ref<string | null>(null)
const selectedOrganization = ref<OrganizationDetail | null>(null)
const detailLoading = ref(false)

// 搜索
const searchKeyword = ref("")

// 弹窗
const createDialogOpen = ref(false)
const createDialogMode = ref<"create-root" | "create-child" | "create-sibling" | "edit">("create-root")

// Tabs
const activeTab = ref("info")

// 下级组织
const childOrganizations = ref<Organization[]>([])

// 直属成员
const members = ref<OrganizationUser[]>([])
const membersLoading = ref(false)

// 添加成员弹窗
const addMemberDialogOpen = ref(false)

// ========== 下级组织 DataTable ==========

const childOrgColumns: ColumnDef<Organization>[] = [
  {
    accessorKey: "name",
    header: "组织名称",
    size: 160,
    cell: ({ row }) => h("span", { class: "font-medium" }, row.original.name),
  },
  {
    accessorKey: "code",
    header: "组织编码",
    size: 120,
    cell: ({ row }) => row.original.code || "--",
  },
  {
    accessorKey: "direct_member_count",
    header: "成员数",
    size: 80,
    cell: ({ row }) => row.original.direct_member_count ?? "--",
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
        () => (status === "active" ? "启用" : "停用")
      )
    },
  },
  {
    id: "actions",
    header: "操作",
    size: 80,
    cell: ({ row }) =>
      h(ChildOrgRowActions, {
        row: row.original,
        onView: viewChildOrganization,
      }),
  },
]

const childOrgTable = useDataTable<Organization>({
  columns: childOrgColumns,
  remoteFetchFn: async () => {
    // 数据在 loadOrganizationDetail 中加载
    return {
      code: 200,
      msg: "OK",
      data: childOrganizations.value,
      total: childOrganizations.value.length,
      page: 1,
      page_size: 100,
    }
  },
  enabled: () => !!selectedId.value && activeTab.value === "children",
})

// ========== 直属成员 DataTable ==========

const memberColumns: ColumnDef<OrganizationUser>[] = [
  {
    accessorKey: "nickname",
    header: "姓名",
    size: 120,
    cell: ({ row }) =>
      h("span", { class: "font-medium" }, row.original.nickname || row.original.username),
  },
  {
    accessorKey: "username",
    header: "账号",
    size: 120,
    cell: ({ row }) => h("span", { class: "font-mono text-sm" }, row.original.username),
  },
  {
    accessorKey: "phone",
    header: "联系方式",
    size: 140,
    cell: ({ row }) => row.original.phone || row.original.email || "--",
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
        () => (status === "active" ? "启用" : "停用")
      )
    },
  },
  {
    id: "actions",
    header: "操作",
    size: 160,
    cell: ({ row }) =>
      h(OrgMemberRowActions, {
        row: row.original,
        onDisable: handleDisableMember,
        onEnable: handleEnableMember,
        onRemove: handleRemoveMember,
      }),
  },
]

const memberTable = useDataTable<OrganizationUser>({
  columns: memberColumns,
  remoteFetchFn: async () => {
    // 数据在 loadOrganizationDetail 中加载
    return {
      code: 200,
      msg: "OK",
      data: members.value,
      total: members.value.length,
      page: 1,
      page_size: 100,
    }
  },
  enabled: () => !!selectedId.value && activeTab.value === "members",
})

// ========== 计算属性 ==========

const hasSelection = computed(() => !!selectedId.value)

// ========== 方法 ==========

/** 加载组织树 */
async function loadTree() {
  loading.value = true
  try {
    const res = await getOrganizationTree()
    organizationTree.value = res.data || []
    // 默认选中第一个节点
    if (organizationTree.value.length > 0 && !selectedId.value) {
      await selectOrganization(organizationTree.value[0])
    }
  } catch (error) {
    notifyError(getErrorMessage(error, "加载组织树失败"))
  } finally {
    loading.value = false
  }
}

/** 选择组织节点 */
async function selectOrganization(org: Organization) {
  selectedId.value = org.id
  await loadOrganizationDetail()
}

/** 加载组织详情 */
async function loadOrganizationDetail() {
  if (!selectedId.value) return

  detailLoading.value = true
  try {
    const [detailRes, membersRes] = await Promise.all([
      getOrganizationDetail(selectedId.value),
      getOrganizationMembers(selectedId.value),
    ])
    selectedOrganization.value = detailRes.data
    members.value = membersRes.data || []

    // 提取下级组织
    const findChildren = (items: Organization[], parentId: string): Organization[] => {
      return items.filter((item) => item.parent_id === parentId)
    }
    childOrganizations.value = findChildren(organizationTree.value, selectedId.value)

    // 刷新 DataTable
    await Promise.all([childOrgTable.refresh(true), memberTable.refresh(true)])
  } catch (error) {
    notifyError(getErrorMessage(error, "加载组织详情失败"))
  } finally {
    detailLoading.value = false
  }
}

/** 组织信息描述项 */
const infoItems = computed<DescriptionItem[]>(() => {
  const org = selectedOrganization.value
  if (!org) return []
  return [
    { label: "组织名称", value: org.name },
    { label: "组织编码", value: org.code || "--" },
    { label: "组织路径", value: org.path || "--" },
    { label: "排序号", value: String(org.sort_order) },
    { label: "直属成员数", value: String(org.direct_member_count) },
    { label: "累计成员数", value: String(org.total_member_count) },
    { label: "状态", value: org.status === "active" ? "启用" : "停用" },
  ]
})

/** 搜索过滤 */
const filteredTree = computed(() => {
  if (!searchKeyword.value.trim()) return organizationTree.value

  const keyword = searchKeyword.value.toLowerCase()

  function filterNodes(nodes: Organization[]): Organization[] {
    return nodes.reduce<Organization[]>((acc, node) => {
      const matches = node.name.toLowerCase().includes(keyword) || (node.code?.toLowerCase().includes(keyword) ?? false)
      const filteredChildren = node.children ? filterNodes(node.children) : []

      if (matches || filteredChildren.length > 0) {
        acc.push({ ...node, children: filteredChildren.length > 0 ? filteredChildren : node.children })
      }

      return acc
    }, [])
  }

  return filterNodes(organizationTree.value)
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

  if (!await confirmAction(`确定要删除组织「${selectedOrganization.value?.name}」吗？删除后不可恢复。`)) {
    return
  }

  try {
    await deleteOrganization(selectedId.value)
    notifySuccess("删除成功")
    selectedId.value = null
    selectedOrganization.value = null
    await loadTree()
  } catch (error) {
    notifyError(getErrorMessage(error, "删除失败"))
  }
}

/** 提交创建/编辑 */
async function handleCreateSubmit(data: SubmitData) {
  try {
    if (createDialogMode.value === "edit" && selectedId.value) {
      await updateOrganization(selectedId.value, data)
      notifySuccess("更新成功")
    } else {
      // 创建时根据 mode 决定 parent_id
      let parentId = data.parent_id
      if (createDialogMode.value === "create-child" && selectedId.value) {
        parentId = selectedId.value
      } else if (createDialogMode.value === "create-sibling" && selectedOrganization.value) {
        parentId = selectedOrganization.value.parent_id || undefined
      } else if (createDialogMode.value === "create-root") {
        parentId = undefined
      }

      await createOrganization({ ...data, parent_id: parentId })
      notifySuccess("创建成功")
    }

    createDialogOpen.value = false
    await loadTree()
  } catch (error) {
    notifyError(getErrorMessage(error, "操作失败"))
  }
}

/** 查看下级组织 */
function viewChildOrganization(org: Organization) {
  selectOrganization(org)
}

/** 添加成员 */
function handleAddMembers() {
  addMemberDialogOpen.value = true
}

/** 确认添加成员 */
async function handleConfirmMembers(userIds: string[]) {
  if (!selectedId.value || userIds.length === 0) return

  try {
    const res = await batchAddOrganizationUsers(selectedId.value, userIds)
    notifySuccess(`成功添加 ${res.data?.added || 0} 个成员`)
    await loadOrganizationDetail()
  } catch (error) {
    notifyError(getErrorMessage(error, "添加成员失败"))
  }
}

/** 启用成员 */
async function handleEnableMember(user: OrganizationUser) {
  if (!selectedId.value) return

  try {
    await enableOrganizationUser(selectedId.value, user.id)
    notifySuccess("已启用")
    await loadOrganizationDetail()
  } catch (error) {
    notifyError(getErrorMessage(error, "启用失败"))
  }
}

/** 停用成员 */
async function handleDisableMember(user: OrganizationUser) {
  if (!selectedId.value) return

  if (!await confirmAction(`确定要停用「${user.nickname || user.username}」吗？`)) {
    return
  }

  try {
    await disableOrganizationUser(selectedId.value, user.id)
    notifySuccess("已停用")
    await loadOrganizationDetail()
  } catch (error) {
    notifyError(getErrorMessage(error, "停用失败"))
  }
}

/** 移除成员 */
async function handleRemoveMember(user: OrganizationUser) {
  if (!selectedId.value) return

  if (!await confirmAction(`确定要将「${user.nickname || user.username}」移出本组织吗？`)) {
    return
  }

  try {
    await removeOrganizationUser(selectedId.value, user.id)
    notifySuccess("已移除")
    await loadOrganizationDetail()
  } catch (error) {
    notifyError(getErrorMessage(error, "移除失败"))
  }
}

// PeopleSelectDialog API 回调
async function loadOrgNodesCallback(): Promise<OrgTreeNode[]> {
  try {
    const res = await getOrganizationTree()
    const orgs = res.data || []
    function toOrgTreeNodes(nodes: Organization[]): OrgTreeNode[] {
      return nodes.map((d) => {
        const children = d.children ? toOrgTreeNodes(d.children) : undefined
        return {
          id: d.id,
          name: d.name,
          code: d.code ?? undefined,
          parent_id: d.parent_id ?? undefined,
          has_user_num: d.direct_member_count || 0,
          has_org_num: d.children?.length || 0,
          tree_leaf: !d.children || d.children.length === 0,
          children,
        }
      })
    }
    return toOrgTreeNodes(orgs)
  } catch {
    return []
  }
}

async function searchPeopleCallback(keyword: string): Promise<PeopleItem[]> {
  try {
    const { getUsers } = await import("@/iam/api/user")
    const res = await getUsers({ keyword, page: 1, page_size: 100 })
    const users = res.data || []
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
    const res = await getOrganizationMembers(orgId)
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

// 初始化
onMounted(() => {
  loadTree()
})
</script>

<template>
  <AppPage title="组织管理" variant="workbench" description="管理组织架构，添加、编辑、删除组织，查看组织成员">
    <!-- Header 操作按钮 -->
    <template #actions>
      <div class="flex items-center gap-2">
        <Button :disabled="!hasSelection" @click="handleAddSibling" data-testid="add-sibling-btn">
          <Plus class="mr-1 h-4 w-4" />
          新增同级
        </Button>
        <Button :disabled="!hasSelection" @click="handleAddChild" data-testid="add-child-btn">
          <Plus class="mr-1 h-4 w-4" />
          新增子组织
        </Button>
        <Button variant="outline" :disabled="!hasSelection" @click="handleEdit" data-testid="edit-org-btn">
          <Pencil class="mr-1 h-4 w-4" />
          编辑
        </Button>
        <Button variant="danger" :disabled="!hasSelection" @click="handleDelete" data-testid="delete-org-btn">
          <Trash2 class="mr-1 h-4 w-4" />
          删除
        </Button>
      </div>
    </template>

    <!-- Body -->
    <div class="flex gap-4 h-[calc(100vh-200px)]" data-testid="org-page-body">
      <!-- 左侧：组织树 -->
      <div class="w-[300px] min-h-0 shrink-0 flex flex-col border rounded-lg overflow-hidden bg-card" data-testid="org-tree-panel">
        <div class="p-3 border-b bg-muted/30">
          <div class="relative">
            <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              v-model="searchKeyword"
              placeholder="搜索组织..."
              class="pl-8"
              data-testid="org-search"
            />
          </div>
        </div>

        <ScrollArea class="flex-1">
          <div v-if="loading" class="p-3 space-y-2" data-testid="org-tree-loading">
            <Skeleton v-for="i in 8" :key="i" class="h-6 w-full" />
          </div>

          <div v-else-if="filteredTree.length === 0" class="p-4 text-center text-muted-foreground text-sm" data-testid="org-tree-empty">
            {{ searchKeyword ? "未找到匹配的组织" : "暂无组织数据" }}
          </div>

          <div v-else class="py-1" data-testid="org-tree">
            <OrganizationTreeNode
              :organizations="filteredTree"
              :selected-id="selectedId"
              :depth="0"
              @select="selectOrganization"
            />
          </div>
        </ScrollArea>

        <div class="p-2 border-t">
          <Button variant="outline" class="w-full" @click="handleAddRoot" data-testid="add-root-btn">
            <Plus class="mr-1 h-4 w-4" />
            新增一级组织
          </Button>
        </div>
      </div>

      <!-- 右侧：详情 + Tabs -->
      <div class="flex-1 flex flex-col border rounded-lg overflow-hidden bg-card" data-testid="org-detail-panel">
        <template v-if="selectedOrganization">
          <!-- 头部信息 -->
          <div class="p-4 border-b bg-muted/20" data-testid="org-detail-header">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-lg font-semibold" data-testid="org-detail-name">{{ selectedOrganization.name }}</h2>
                <p class="text-sm text-muted-foreground mt-1">
                  {{ selectedOrganization.path || "根级组织" }}
                </p>
              </div>
              <div class="flex items-center gap-4 text-sm">
                <div class="flex items-center gap-1">
                  <Users class="h-4 w-4 text-muted-foreground" />
                  <span>直属成员 {{ selectedOrganization.direct_member_count }}</span>
                </div>
                <div class="flex items-center gap-1">
                  <FolderTree class="h-4 w-4 text-muted-foreground" />
                  <span>下级组织 {{ selectedOrganization.children_count }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Tabs -->
          <Tabs v-model="activeTab" class="flex-1 flex flex-col">
            <div class="px-4 pt-2 border-b">
              <TabsList>
                <TabsTrigger value="info" data-testid="tab-info">
                  <Info class="h-4 w-4 mr-1" />
                  组织信息
                </TabsTrigger>
                <TabsTrigger value="children" data-testid="tab-children">
                  <FolderTree class="h-4 w-4 mr-1" />
                  下级组织
                </TabsTrigger>
                <TabsTrigger value="members" data-testid="tab-members">
                  <Users class="h-4 w-4 mr-1" />
                  直属成员
                </TabsTrigger>
              </TabsList>
            </div>

            <ScrollArea class="flex-1">
              <!-- 组织信息 Tab -->
              <TabsContent value="info" class="p-4 m-0">
                <DescriptionList :items="infoItems" :columns="2" bordered data-testid="org-info" />
              </TabsContent>

              <!-- 下级组织 Tab -->
              <TabsContent value="children" class="p-4 m-0">
                <div v-if="childOrganizations.length === 0" class="py-8 text-center text-muted-foreground" data-testid="no-child-orgs">
                  当前组织暂无下级组织
                </div>
                <DataTable v-else :data-table="childOrgTable" :fixed-layout="true" data-testid="child-org-table" />
              </TabsContent>

              <!-- 直属成员 Tab -->
              <TabsContent value="members" class="p-4 m-0">
                <div class="flex items-center justify-between mb-3">
                  <p class="text-sm text-muted-foreground">
                    当前组织的直属成员，不包含下级组织的成员
                  </p>
                  <Button size="sm" @click="handleAddMembers" data-testid="add-member-btn">
                    <UserPlus class="mr-1 h-4 w-4" />
                    添加成员
                  </Button>
                </div>

                <div v-if="membersLoading" class="py-4" data-testid="members-loading">
                  <Skeleton v-for="i in 5" :key="i" class="h-10 w-full mb-2" />
                </div>

                <div v-else-if="members.length === 0" class="py-8 text-center text-muted-foreground" data-testid="no-members">
                  当前组织暂无直属成员
                </div>

                <DataTable v-else :data-table="memberTable" :fixed-layout="true" data-testid="member-table" />
              </TabsContent>
            </ScrollArea>
          </Tabs>
        </template>

        <div v-else class="flex-1 flex items-center justify-center text-muted-foreground" data-testid="no-selection">
          <div class="text-center">
            <Building2 class="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>请选择左侧组织查看详情</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <CreateOrganizationDialog
      v-model:open="createDialogOpen"
      :mode="createDialogMode"
      :current-organization="selectedOrganization"
      :organization-tree="organizationTree"
      @submit="handleCreateSubmit"
    />

    <!-- 添加成员弹窗 -->
    <PeopleSelectDialog
      v-model:open="addMemberDialogOpen"
      title="选择人员"
      :multiple="true"
      :disabled-ids="members.map((m) => m.id)"
      :load-org-nodes="loadOrgNodesCallback"
      :search-people="searchPeopleCallback"
      :load-org-people="loadOrgPeopleCallback"
      @confirm="(ids, _users) => handleConfirmMembers(ids)"
    />
  </AppPage>
</template>
