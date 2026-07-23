<script setup lang="ts">
/**
 * PermissionRequestList — 权限申请页面
 *
 * 布局：
 * - Tabs：我的申请 / 待我审批
 * - 搜索筛选区
 * - DataTable 列表 + 行内审批操作
 * - 新建申请弹窗
 */

import { ref, onMounted, h } from "vue"
import type { ColumnDef } from "@tanstack/vue-table"
import {
  Send,
  CheckCircle,
  XCircle,
  RefreshCw,
  Plus,
} from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  DataTable,
  useDataTable,
  Input,
} from "@/components"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type {
  PermissionRequestItem,
  PermissionRequestCreate,
} from "@/iam/types/permissionRequest"
import {
  getPermissionRequests,
  getPendingApprovals,
  submitPermissionRequest,
  approvePermissionRequest,
  rejectPermissionRequest,
} from "@/iam/api/permissionRequest"
import { confirmAction, notifySuccess, notifyError, getErrorMessage } from "@/framework/utils/feedback"

// ========== 状态 ==========

const activeTab = ref("my-requests")
const statusFilter = ref("all")
const keyword = ref("")

// 新建申请弹窗
const createDialogOpen = ref(false)
const createSubmitting = ref(false)
const createForm = ref<PermissionRequestCreate>({
  resource: "",
  action: "",
  reason: "",
})

// 拒绝弹窗
const rejectDialogOpen = ref(false)
const rejectTarget = ref<PermissionRequestItem | null>(null)
const rejectReason = ref("")

// ========== 方法 ==========

/** 格式化日期时间 */
function formatDateTime(value?: string | null): string {
  if (!value) return "-"
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value))
}

/** 状态标签 */
function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: "待审批",
    approved: "已通过",
    rejected: "已拒绝",
  }
  return labels[status] || status
}

/** 状态 Badge variant */
function getStatusVariant(status: string): "default" | "secondary" | "destructive" {
  const variants: Record<string, "default" | "secondary" | "destructive"> = {
    pending: "secondary",
    approved: "default",
    rejected: "destructive",
  }
  return variants[status] || "secondary"
}

/** 打开新建申请弹窗 */
function handleCreate() {
  createForm.value = { resource: "", action: "", reason: "" }
  createDialogOpen.value = true
}

/** 提交新建申请 */
async function handleCreateSubmit() {
  if (!createForm.value.resource || !createForm.value.action || !createForm.value.reason) {
    notifyError("资源、操作和原因不能为空")
    return
  }
  createSubmitting.value = true
  try {
    await submitPermissionRequest(createForm.value)
    notifySuccess("申请已提交")
    createDialogOpen.value = false
    await myRequestTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "提交申请失败"))
  } finally {
    createSubmitting.value = false
  }
}

/** 审批通过 */
async function handleApprove(item: PermissionRequestItem) {
  if (!await confirmAction(`确定要通过「${item.applicant_name}」的权限申请吗？`)) return
  try {
    await approvePermissionRequest(item.id)
    notifySuccess("已通过")
    await pendingTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "审批失败"))
  }
}

/** 打开拒绝弹窗 */
function handleOpenReject(item: PermissionRequestItem) {
  rejectTarget.value = item
  rejectReason.value = ""
  rejectDialogOpen.value = true
}

/** 提交拒绝 */
async function handleRejectSubmit() {
  if (!rejectTarget.value) return
  try {
    await rejectPermissionRequest(rejectTarget.value.id, { reason: rejectReason.value })
    notifySuccess("已拒绝")
    rejectDialogOpen.value = false
    rejectTarget.value = null
    await pendingTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "审批失败"))
  }
}

// ========== 列定义 ==========

/** 我的申请列 */
const myRequestColumns: ColumnDef<PermissionRequestItem>[] = [
  {
    id: "resource",
    header: "资源",
    size: 160,
    cell: ({ row }) => h("span", { class: "font-mono text-sm" }, row.original.resource),
  },
  {
    id: "action",
    header: "操作",
    size: 100,
    cell: ({ row }) => h(Badge, { variant: "outline" }, () => row.original.action),
  },
  {
    id: "reason",
    header: "申请原因",
    size: 240,
    cell: ({ row }) => h("span", { class: "text-sm truncate block" }, row.original.reason),
  },
  {
    id: "status",
    header: "状态",
    size: 80,
    cell: ({ row }) => {
      const item = row.original
      return h(Badge, { variant: getStatusVariant(item.status) }, () => getStatusLabel(item.status))
    },
  },
  {
    id: "created_at",
    header: "申请时间",
    size: 140,
    cell: ({ row }) => h("span", { class: "text-muted-foreground text-sm" }, formatDateTime(row.original.created_at)),
  },
]

/** 待我审批列 */
const pendingColumns: ColumnDef<PermissionRequestItem>[] = [
  {
    id: "applicant_name",
    header: "申请人",
    size: 100,
    cell: ({ row }) => h("span", { class: "font-medium" }, row.original.applicant_name),
  },
  {
    id: "resource",
    header: "资源",
    size: 160,
    cell: ({ row }) => h("span", { class: "font-mono text-sm" }, row.original.resource),
  },
  {
    id: "action",
    header: "操作",
    size: 100,
    cell: ({ row }) => h(Badge, { variant: "outline" }, () => row.original.action),
  },
  {
    id: "reason",
    header: "申请原因",
    size: 200,
    cell: ({ row }) => h("span", { class: "text-sm truncate block" }, row.original.reason),
  },
  {
    id: "created_at",
    header: "申请时间",
    size: 140,
    cell: ({ row }) => h("span", { class: "text-muted-foreground text-sm" }, formatDateTime(row.original.created_at)),
  },
  {
    id: "actions",
    header: "审批",
    size: 140,
    cell: ({ row }) => {
      const item = row.original
      return h("div", { class: "flex items-center gap-1" }, [
        h(
          Button,
          {
            size: "sm" as const,
            variant: "outline" as const,
            class: "h-7 px-2 text-green-600 hover:text-green-700",
            onClick: () => handleApprove(item),
          },
          () => [h(CheckCircle, { class: "h-3.5 w-3.5 mr-1" }), "通过"]
        ),
        h(
          Button,
          {
            size: "sm" as const,
            variant: "outline" as const,
            class: "h-7 px-2 text-destructive hover:text-destructive",
            onClick: () => handleOpenReject(item),
          },
          () => [h(XCircle, { class: "h-3.5 w-3.5 mr-1" }), "拒绝"]
        ),
      ])
    },
  },
]

// ========== DataTable 初始化 ==========

const myRequestTable = useDataTable<PermissionRequestItem>({
  columns: myRequestColumns,
  remoteFetchFn: async ({ page, page_size }) => {
    const res = await getPermissionRequests({
      page,
      page_size,
      status: statusFilter.value === "all" ? undefined : statusFilter.value,
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
  enabled: () => activeTab.value === "my-requests",
})

const pendingTable = useDataTable<PermissionRequestItem>({
  columns: pendingColumns,
  remoteFetchFn: async ({ page, page_size }) => {
    const res = await getPendingApprovals({
      page,
      page_size,
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
  enabled: () => activeTab.value === "pending-approvals",
})
</script>

<template>
  <AppPage title="权限申请" variant="workbench" description="申请资源权限或审批他人的权限申请">
    <!-- 顶部操作栏 -->
    <div class="flex flex-wrap items-center justify-between gap-3 rounded-md bg-background mb-4">
      <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
        <Select v-model="statusFilter">
          <SelectTrigger class="w-32 max-w-full">
            <SelectValue placeholder="全部状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="pending">待审批</SelectItem>
            <SelectItem value="approved">已通过</SelectItem>
            <SelectItem value="rejected">已拒绝</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="ml-auto flex shrink-0 items-center gap-2">
        <Button type="button" @click="handleCreate">
          <Plus class="mr-1 h-4 w-4" />
          新建申请
        </Button>
        <Button
          type="button"
          variant="outline"
          :disabled="myRequestTable.loading.value || pendingTable.loading.value"
          @click="activeTab === 'my-requests' ? myRequestTable.refresh(true) : pendingTable.refresh(true)"
        >
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
      </div>
    </div>

    <!-- Tabs 内容 -->
    <Tabs v-model="activeTab" class="flex min-h-0 flex-1 flex-col">
      <div class="mb-4">
        <TabsList>
          <TabsTrigger value="my-requests">
            <Send class="h-4 w-4 mr-1" />
            我的申请
          </TabsTrigger>
          <TabsTrigger value="pending-approvals">
            <CheckCircle class="h-4 w-4 mr-1" />
            待我审批
          </TabsTrigger>
        </TabsList>
      </div>

      <!-- 我的申请 -->
      <TabsContent value="my-requests" class="flex min-h-0 flex-1 flex-col m-0">
        <DataTable :data-table="myRequestTable" :fixed-layout="true" />
      </TabsContent>

      <!-- 待我审批 -->
      <TabsContent value="pending-approvals" class="flex min-h-0 flex-1 flex-col m-0">
        <DataTable :data-table="pendingTable" :fixed-layout="true" />
      </TabsContent>
    </Tabs>

    <!-- 新建申请弹窗 -->
    <Dialog v-model:open="createDialogOpen">
      <DialogContent class="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>新建权限申请</DialogTitle>
          <DialogDescription>
            申请获取特定资源的操作权限
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4">
          <div class="space-y-2">
            <label class="text-sm font-medium">
              资源 <span class="text-destructive">*</span>
            </label>
            <Input v-model="createForm.resource" placeholder="例如：document:dataset" />
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium">
              操作 <span class="text-destructive">*</span>
            </label>
            <Input v-model="createForm.action" placeholder="例如：write" />
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium">
              申请原因 <span class="text-destructive">*</span>
            </label>
            <Input v-model="createForm.reason" placeholder="请输入申请原因" />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="createDialogOpen = false">取消</Button>
          <Button :disabled="createSubmitting" @click="handleCreateSubmit">
            {{ createSubmitting ? "提交中..." : "提交" }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 拒绝弹窗 -->
    <Dialog v-model:open="rejectDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>拒绝权限申请</DialogTitle>
          <DialogDescription>
            拒绝「{{ rejectTarget?.applicant_name }}」对 {{ rejectTarget?.resource }}:{{ rejectTarget?.action }} 的申请
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-2">
          <label class="text-sm font-medium">拒绝原因</label>
          <Input v-model="rejectReason" placeholder="请输入拒绝原因（可选）" />
        </div>

        <DialogFooter>
          <Button variant="outline" @click="rejectDialogOpen = false">取消</Button>
          <Button variant="destructive" @click="handleRejectSubmit">确定拒绝</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>
