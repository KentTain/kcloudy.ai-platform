<script setup lang="ts">
/**
 * PolicyList — 企业 Policy 管理页面
 *
 * 布局：
 * - 搜索筛选区（类型、状态、关键词）
 * - DataTable Policy 列表 + 行内操作
 * - 创建/编辑 Policy 弹窗
 */

import { ref, onMounted, h } from "vue"
import type { ColumnDef } from "@tanstack/vue-table"
import {
  Shield,
  Plus,
  Pencil,
  Trash2,
  Power,
  PowerOff,
  RefreshCw,
} from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  DataTable,
  useDataTable,
  Input,
} from "@/components"
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
  PolicyItem,
  PolicyCreate,
  PolicyUpdate,
} from "@/iam/types/policy"
import {
  getPolicies,
  createPolicy,
  updatePolicy,
  deletePolicy,
  enablePolicy,
  disablePolicy,
} from "@/iam/api/policy"
import { confirmAction, notifySuccess, notifyError, getErrorMessage } from "@/framework/utils/feedback"

// ========== 状态 ==========

const typeFilter = ref("all")
const enabledFilter = ref("all")
const keyword = ref("")

// 创建/编辑弹窗
const formDialogOpen = ref(false)
const formDialogMode = ref<"create" | "edit">("create")
const formSubmitting = ref(false)
const formValues = ref<{
  id: string
  name: string
  description: string
  type: "allow" | "deny"
  effect: "allow" | "deny"
  resources: string
  actions: string
  priority: number
  is_enabled: boolean
}>({
  id: "",
  name: "",
  description: "",
  type: "allow",
  effect: "allow",
  resources: "",
  actions: "",
  priority: 0,
  is_enabled: true,
})

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

/** 打开创建弹窗 */
function handleCreate() {
  formDialogMode.value = "create"
  formValues.value = {
    id: "",
    name: "",
    description: "",
    type: "allow",
    effect: "allow",
    resources: "",
    actions: "",
    priority: 0,
    is_enabled: true,
  }
  formDialogOpen.value = true
}

/** 打开编辑弹窗 */
function handleEdit(item: PolicyItem) {
  formDialogMode.value = "edit"
  formValues.value = {
    id: item.id,
    name: item.name,
    description: item.description || "",
    type: item.type,
    effect: item.effect,
    resources: item.resources.join(", "),
    actions: item.actions.join(", "),
    priority: item.priority,
    is_enabled: item.is_enabled,
  }
  formDialogOpen.value = true
}

/** 提交表单 */
async function handleFormSubmit() {
  if (!formValues.value.name) {
    notifyError("策略名称不能为空")
    return
  }

  const resourcesArr = formValues.value.resources
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
  const actionsArr = formValues.value.actions
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)

  if (resourcesArr.length === 0 || actionsArr.length === 0) {
    notifyError("资源和操作不能为空")
    return
  }

  formSubmitting.value = true
  try {
    if (formDialogMode.value === "edit") {
      const data: PolicyUpdate = {
        name: formValues.value.name,
        description: formValues.value.description || undefined,
        type: formValues.value.type,
        effect: formValues.value.effect,
        resources: resourcesArr,
        actions: actionsArr,
        priority: formValues.value.priority,
      }
      await updatePolicy(formValues.value.id, data)
      notifySuccess("更新成功")
    } else {
      const data: PolicyCreate = {
        name: formValues.value.name,
        description: formValues.value.description || undefined,
        type: formValues.value.type,
        effect: formValues.value.effect,
        resources: resourcesArr,
        actions: actionsArr,
        priority: formValues.value.priority,
        is_enabled: formValues.value.is_enabled,
      }
      await createPolicy(data)
      notifySuccess("创建成功")
    }
    formDialogOpen.value = false
    await dataTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "操作失败"))
  } finally {
    formSubmitting.value = false
  }
}

/** 切换启用/停用 */
async function handleToggleEnabled(item: PolicyItem) {
  if (item.is_system) {
    notifyError("系统内置策略无法修改")
    return
  }
  try {
    if (item.is_enabled) {
      await disablePolicy(item.id)
      notifySuccess("已停用")
    } else {
      await enablePolicy(item.id)
      notifySuccess("已启用")
    }
    await dataTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "操作失败"))
  }
}

/** 删除 */
async function handleDelete(item: PolicyItem) {
  if (item.is_system) {
    notifyError("系统内置策略无法删除")
    return
  }
  if (!await confirmAction(`确定要删除策略「${item.name}」吗？`)) return
  try {
    await deletePolicy(item.id)
    notifySuccess("删除成功")
    await dataTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "删除失败"))
  }
}

// ========== 列定义 ==========

const columns: ColumnDef<PolicyItem>[] = [
  {
    id: "name",
    header: "名称",
    size: 180,
    cell: ({ row }) => {
      const item = row.original
      const classes = item.is_system ? "font-medium" : "font-medium"
      return h("span", { class: classes }, item.name)
    },
  },
  {
    id: "type",
    header: "类型",
    size: 80,
    cell: ({ row }) => {
      const item = row.original
      const variant = item.type === "allow" ? "default" : "destructive"
      const label = item.type === "allow" ? "允许" : "拒绝"
      return h(Badge, { variant }, () => label)
    },
  },
  {
    id: "resources",
    header: "资源",
    size: 200,
    cell: ({ row }) => {
      const item = row.original
      return h("span", { class: "font-mono text-sm truncate block" }, item.resources.join(", "))
    },
  },
  {
    id: "actions_field",
    header: "操作",
    size: 120,
    cell: ({ row }) => {
      const item = row.original
      return h("span", { class: "text-sm" }, item.actions.join(", "))
    },
  },
  {
    id: "priority",
    header: "优先级",
    size: 80,
    cell: ({ row }) => h("span", { class: "text-sm" }, String(row.original.priority)),
  },
  {
    id: "is_enabled",
    header: "状态",
    size: 80,
    cell: ({ row }) => {
      const item = row.original
      return h(
        Badge,
        { variant: item.is_enabled ? "default" : "secondary" },
        () => item.is_enabled ? "启用" : "停用"
      )
    },
  },
  {
    id: "updated_at",
    header: "更新时间",
    size: 140,
    cell: ({ row }) => h("span", { class: "text-muted-foreground text-sm" }, formatDateTime(row.original.updated_at)),
  },
  {
    id: "actions",
    header: "操作",
    size: 160,
    cell: ({ row }) => {
      const item = row.original
      return h("div", { class: "flex items-center gap-1" }, [
        h(
          Button,
          {
            size: "sm" as const,
            variant: "ghost" as const,
            class: "h-7 px-2",
            onClick: () => handleEdit(item),
          },
          () => [h(Pencil, { class: "h-3.5 w-3.5 mr-1" }), "编辑"]
        ),
        !item.is_system
          ? h(
              Button,
              {
                size: "sm" as const,
                variant: "ghost" as const,
                class: "h-7 px-2",
                onClick: () => handleToggleEnabled(item),
              },
              () => item.is_enabled
                ? [h(PowerOff, { class: "h-3.5 w-3.5 mr-1" }), "停用"]
                : [h(Power, { class: "h-3.5 w-3.5 mr-1" }), "启用"]
            )
          : null,
        !item.is_system
          ? h(
              Button,
              {
                size: "sm" as const,
                variant: "ghost" as const,
                class: "h-7 px-2 text-destructive hover:text-destructive",
                onClick: () => handleDelete(item),
              },
              () => [h(Trash2, { class: "h-3.5 w-3.5 mr-1" }), "删除"]
            )
          : null,
      ])
    },
  },
]

// ========== DataTable 初始化 ==========

const dataTable = useDataTable<PolicyItem>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const res = await getPolicies({
      page,
      page_size,
      type: typeFilter.value === "all" ? undefined : typeFilter.value,
      is_enabled: enabledFilter.value === "all" ? undefined : enabledFilter.value === "enabled",
      keyword: keyword.value || undefined,
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
</script>

<template>
  <AppPage title="企业策略" variant="workbench" description="管理企业级访问策略，控制资源权限的允许和拒绝规则">
    <!-- 搜索筛选栏 -->
    <div class="flex flex-wrap items-center justify-between gap-3 rounded-md bg-background mb-4">
      <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
        <div class="relative">
          <Shield class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            v-model="keyword"
            placeholder="搜索策略..."
            class="pl-8 w-48"
          />
        </div>

        <Select v-model="typeFilter">
          <SelectTrigger class="w-32 max-w-full">
            <SelectValue placeholder="全部类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部类型</SelectItem>
            <SelectItem value="allow">允许</SelectItem>
            <SelectItem value="deny">拒绝</SelectItem>
          </SelectContent>
        </Select>

        <Select v-model="enabledFilter">
          <SelectTrigger class="w-32 max-w-full">
            <SelectValue placeholder="全部状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="enabled">启用</SelectItem>
            <SelectItem value="disabled">停用</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="ml-auto flex shrink-0 items-center gap-2">
        <Button type="button" @click="handleCreate">
          <Plus class="mr-1 h-4 w-4" />
          新建策略
        </Button>
        <Button
          type="button"
          variant="outline"
          :disabled="dataTable.loading.value"
          @click="dataTable.refresh(true)"
        >
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
      </div>
    </div>

    <!-- Policy 列表 -->
    <div class="flex min-h-0 flex-1 flex-col">
      <DataTable :data-table="dataTable" :fixed-layout="true" />
    </div>

    <!-- 创建/编辑弹窗 -->
    <Dialog v-model:open="formDialogOpen">
      <DialogContent class="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle>
            {{ formDialogMode === "create" ? "新建策略" : "编辑策略" }}
          </DialogTitle>
          <DialogDescription v-if="formDialogMode === 'create'">
            创建一条新的访问策略
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4">
          <div class="space-y-2">
            <label class="text-sm font-medium">
              策略名称 <span class="text-destructive">*</span>
            </label>
            <Input v-model="formValues.name" placeholder="请输入策略名称" />
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium">描述</label>
            <Input v-model="formValues.description" placeholder="请输入描述（可选）" />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">策略类型</label>
              <Select v-model="formValues.type">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="allow">允许</SelectItem>
                  <SelectItem value="deny">拒绝</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium">效果</label>
              <Select v-model="formValues.effect">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="allow">允许</SelectItem>
                  <SelectItem value="deny">拒绝</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium">
              资源 <span class="text-destructive">*</span>
            </label>
            <Input v-model="formValues.resources" placeholder="多个资源用逗号分隔，例如：document:dataset, document:file" />
            <p class="text-xs text-muted-foreground">多个资源用英文逗号分隔</p>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium">
              操作 <span class="text-destructive">*</span>
            </label>
            <Input v-model="formValues.actions" placeholder="多个操作用逗号分隔，例如：read, write" />
            <p class="text-xs text-muted-foreground">多个操作用英文逗号分隔</p>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium">优先级</label>
            <Input
              v-model="formValues.priority"
              type="number"
              placeholder="0"
            />
            <p class="text-xs text-muted-foreground">数值越大优先级越高</p>
          </div>

          <div v-if="formDialogMode === 'create'" class="flex items-center gap-2">
            <label class="text-sm font-medium">创建后启用</label>
            <Badge :variant="formValues.is_enabled ? 'default' : 'secondary'">
              {{ formValues.is_enabled ? "启用" : "停用" }}
            </Badge>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="formDialogOpen = false">取消</Button>
          <Button :disabled="formSubmitting" @click="handleFormSubmit">
            {{ formSubmitting ? "保存中..." : "确定" }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>
