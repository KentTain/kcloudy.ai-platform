<script setup lang="ts">
/**
 * AuditLogList - 审计日志页面
 *
 * 布局：
 * - 顶部筛选栏（业务域、操作类型、资源类型、时间范围、操作人）
 * - DataTable 审计日志列表 + 行内操作
 * - 侧边详情面板
 */

import { ref, onMounted, h } from "vue"
import type { ColumnDef } from "@tanstack/vue-table"
import { RotateCcw, RefreshCw } from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
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
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { AuditLog, AuditLogOptions, AuditOption } from "@/iam/types"
import { getAuditLogs, getAuditOptions } from "@/iam/api/auditLog"

// ========== 状态 ==========

// 筛选条件
const filters = ref({
  business_domain: "all",
  operation_type: "all",
  resource_type: "all",
  time_range: "7d" as "24h" | "7d" | "30d" | "all",
  operator_by: "",
})

// 选项数据
const options = ref<AuditLogOptions>({
  business_domains: [],
  actions: [],
  resource_types: [],
})

// 详情面板
const detailOpen = ref(false)
const activeLog = ref<AuditLog | null>(null)

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

/** 获取操作类型标签 */
function getActionLabel(log: AuditLog): string {
  const action = options.value.actions.find((a) => a.value === log.operation_type)
  return action?.label || log.operation_type
}

/** 加载选项 */
async function loadOptions() {
  try {
    const res = await getAuditOptions()
    options.value = res.data || {
      business_domains: [],
      actions: [],
      resource_types: [],
    }
  } catch (error) {
    console.error("加载选项失败:", error)
  }
}

/** 重置筛选 */
function handleReset() {
  const changed =
    filters.value.business_domain !== "all" ||
    filters.value.operation_type !== "all" ||
    filters.value.resource_type !== "all" ||
    filters.value.time_range !== "7d" ||
    filters.value.operator_by !== ""

  filters.value = {
    business_domain: "all",
    operation_type: "all",
    resource_type: "all",
    time_range: "7d",
    operator_by: "",
  }

  if (!changed) {
    dataTable.refresh(true)
  }
}

/** 显示详情 */
function showDetail(log: AuditLog) {
  activeLog.value = log
  detailOpen.value = true
}

/** HTML 转义 */
function escapeHtml(value: string): string {
  const htmlEscapes: Record<string, string> = {
    "'": "&#39;",
    '"': "&quot;",
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
  }
  return value.replace(/[&<>"']/g, (char) => htmlEscapes[char] ?? char)
}

/** 渲染日志详情文本 */
function renderLogText(log: AuditLog): string {
  const details = log.details
  if (!details) return "-"

  const type = (details as Record<string, unknown>).type as string | undefined
  const keys = Object.keys(details).filter((key) => key !== "type")
  const firstKey = keys[0]

  if (!firstKey) return type || "-"

  const firstValue = (details as Record<string, unknown>)[firstKey]
  return firstValue !== undefined && firstValue !== null ? String(firstValue) : type || "-"
}

// ========== 列定义 ==========

const columns: ColumnDef<AuditLog>[] = [
  {
    id: "operated_at",
    header: "操作时间",
    size: 140,
    cell: ({ row }) => {
      const log = row.original
      return h("span", { class: "text-muted-foreground" }, formatDateTime(log.operated_at ?? log.created_at))
    },
  },
  {
    id: "operation_type",
    header: "动作",
    size: 200,
    cell: ({ row }) => {
      const log = row.original
      return h(
        Button,
        {
          class: "h-auto p-0 text-left font-medium",
          onClick: () => showDetail(log),
          type: "button",
          variant: "link",
        },
        () => getActionLabel(log)
      )
    },
  },
  {
    id: "operator_by",
    header: "操作人",
    size: 120,
    cell: ({ row }) => {
      const log = row.original
      return h("span", {}, log.operator_name || log.operator_by || "-")
    },
  },
  {
    id: "details",
    header: "日志",
    size: 320,
    cell: ({ row }) => {
      const log = row.original
      const text = renderLogText(log)
      return h("span", { class: "block truncate text-sm", title: escapeHtml(text) }, text)
    },
  },
]

// ========== 初始化 DataTable ==========

const dataTable = useDataTable<AuditLog>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const res = await getAuditLogs({
      page,
      page_size,
      business_domain: filters.value.business_domain === "all" ? undefined : filters.value.business_domain,
      operation_type: filters.value.operation_type === "all" ? undefined : filters.value.operation_type,
      resource_type: filters.value.resource_type === "all" ? undefined : filters.value.resource_type,
      operator_by: filters.value.operator_by || undefined,
      time_range: filters.value.time_range,
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

// 初始化
onMounted(() => {
  loadOptions()
})
</script>

<template>
  <AppPage title="审计日志" variant="workbench" description="查看租户范围内所有用户的关键动作，支持按业务域、操作人、动作、资源和时间范围追溯">
    <!-- 筛选栏 -->
    <div class="flex flex-wrap items-center justify-between gap-3 rounded-md bg-background mb-4">
      <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
        <Select v-model="filters.business_domain">
          <SelectTrigger class="w-40 max-w-full">
            <SelectValue placeholder="全部业务域" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部业务域</SelectItem>
            <SelectItem
              v-for="option in options.business_domains"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </SelectItem>
          </SelectContent>
        </Select>

        <Select v-model="filters.operation_type">
          <SelectTrigger class="w-48 max-w-full">
            <SelectValue placeholder="全部动作" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部动作</SelectItem>
            <SelectItem
              v-for="option in options.actions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </SelectItem>
          </SelectContent>
        </Select>

        <Select v-model="filters.resource_type">
          <SelectTrigger class="w-36 max-w-full">
            <SelectValue placeholder="全部资源" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部资源</SelectItem>
            <SelectItem
              v-for="option in options.resource_types"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </SelectItem>
          </SelectContent>
        </Select>

        <Select v-model="filters.time_range">
          <SelectTrigger class="w-36 max-w-full">
            <SelectValue placeholder="时间范围" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="24h">最近 24 小时</SelectItem>
            <SelectItem value="7d">最近 7 天</SelectItem>
            <SelectItem value="30d">最近 30 天</SelectItem>
            <SelectItem value="all">全部时间</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="ml-auto flex shrink-0 items-center gap-2">
        <Button type="button" variant="outline" @click="handleReset">
          <RotateCcw class="mr-1 h-4 w-4" />
          重置
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

    <!-- 审计日志列表 -->
    <div class="flex min-h-0 flex-1 flex-col">
      <DataTable :data-table="dataTable" :fixed-layout="true" />
    </div>

    <!-- 详情面板 -->
    <Sheet v-model:open="detailOpen">
      <SheetContent class="overflow-y-auto sm:max-w-2xl">
        <SheetHeader>
          <SheetTitle>{{ activeLog ? getActionLabel(activeLog) : "审计详情" }}</SheetTitle>
          <SheetDescription v-if="activeLog">
            {{ formatDateTime(activeLog.operated_at ?? activeLog.created_at) }}
            · {{ activeLog.operator_name ?? activeLog.operator_by ?? "-" }}
          </SheetDescription>
        </SheetHeader>

        <div v-if="activeLog" class="flex flex-col gap-5 px-4 pb-6">
          <div class="grid gap-3 md:grid-cols-2">
            <div class="rounded-md border p-3">
              <p class="text-sm text-muted-foreground">动作类型</p>
              <p class="mt-1.5 font-medium text-sm">{{ getActionLabel(activeLog) }}</p>
              <p class="break-all text-xs text-muted-foreground mt-0.5">
                {{ activeLog.operation_type ?? "-" }}
              </p>
            </div>
            <div class="rounded-md border p-3">
              <p class="text-sm text-muted-foreground">操作时间</p>
              <p class="mt-1.5 font-medium text-sm">
                {{ formatDateTime(activeLog.operated_at ?? activeLog.created_at) }}
              </p>
            </div>
            <div class="rounded-md border p-3 md:col-span-2">
              <p class="text-sm text-muted-foreground">操作人</p>
              <p class="mt-1.5 font-medium">{{ activeLog.operator_name ?? "-" }}</p>
              <p class="break-all text-xs text-muted-foreground mt-0.5">
                {{ activeLog.operator_by ?? "-" }}
              </p>
            </div>
            <div class="rounded-md border p-3">
              <p class="text-sm text-muted-foreground">业务域</p>
              <p class="mt-1.5 font-medium">
                {{ options.business_domains.find((d) => d.value === activeLog.business_domain)?.label ?? activeLog.business_domain ?? "-" }}
              </p>
            </div>
            <div class="rounded-md border p-3">
              <p class="text-sm text-muted-foreground">资源</p>
              <p class="mt-1.5 font-medium text-sm">
                {{ activeLog.resource_name ?? activeLog.resource_id ?? "-" }}
              </p>
            </div>
          </div>

          <!-- 操作详情 -->
          <div v-if="activeLog.details && Object.keys(activeLog.details).length > 0" class="rounded-md border p-3">
            <p class="text-sm text-muted-foreground mb-2">操作详情</p>
            <ScrollArea class="max-h-[300px]">
              <pre class="text-xs bg-muted p-3 rounded overflow-x-auto">{{ JSON.stringify(activeLog.details, null, 2) }}</pre>
            </ScrollArea>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  </AppPage>
</template>
