<script setup lang="ts">
/**
 * NotificationList — 站内信列表页面
 *
 * 布局：
 * - 顶部：未读数 + 全部已读按钮
 * - 搜索筛选区
 * - 站内信列表（未读优先，支持分页）
 */

import { ref, onMounted, h } from "vue"
import type { ColumnDef } from "@tanstack/vue-table"
import { Bell, CheckCheck, RefreshCw, ExternalLink } from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  DataTable,
  useDataTable,
  Input,
} from "@/components"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { NotificationItem } from "@/iam/types/notification"
import {
  getNotifications,
  getUnreadCount,
  markRead,
  markAllRead,
} from "@/iam/api/notification"
import { notifySuccess, notifyError, getErrorMessage } from "@/framework/utils/feedback"

// ========== 状态 ==========

const unreadCount = ref(0)
const keyword = ref("")
const typeFilter = ref("all")
const readFilter = ref("all")
const markReadLoading = ref(false)

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

/** 获取通知类型标签 */
function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    system: "系统",
    permission: "权限",
    policy: "策略",
    general: "通用",
  }
  return labels[type] || type
}

/** 获取通知类型 Badge variant */
function getTypeVariant(type: string): "default" | "secondary" | "outline" | "destructive" {
  const variants: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
    system: "default",
    permission: "secondary",
    policy: "outline",
    general: "outline",
  }
  return variants[type] || "outline"
}

/** 加载未读数 */
async function loadUnreadCount() {
  try {
    const res = await getUnreadCount()
    unreadCount.value = res.data ?? 0
  } catch {
    unreadCount.value = 0
  }
}

/** 标记单条已读 */
async function handleMarkRead(item: NotificationItem) {
  if (item.is_read) return
  try {
    await markRead({ notification_ids: [item.id] })
    notifySuccess("已标记为已读")
    await dataTable.refresh(true)
    await loadUnreadCount()
  } catch (error) {
    notifyError(getErrorMessage(error, "标记已读失败"))
  }
}

/** 全部标记已读 */
async function handleMarkAllRead() {
  if (unreadCount.value === 0) return
  markReadLoading.value = true
  try {
    await markAllRead()
    notifySuccess("已全部标记为已读")
    await dataTable.refresh(true)
    await loadUnreadCount()
  } catch (error) {
    notifyError(getErrorMessage(error, "全部标记已读失败"))
  } finally {
    markReadLoading.value = false
  }
}

/** 跳转链接 */
function handleLinkClick(item: NotificationItem) {
  if (item.link) {
    window.location.href = item.link
  }
}

// ========== 列定义 ==========

const columns: ColumnDef<NotificationItem>[] = [
  {
    id: "is_read",
    header: "状态",
    size: 60,
    cell: ({ row }) => {
      const item = row.original
      if (item.is_read) {
        return h("span", { class: "text-muted-foreground" }, "")
      }
      return h("span", { class: "inline-block h-2 w-2 rounded-full bg-primary" })
    },
  },
  {
    id: "type",
    header: "类型",
    size: 80,
    cell: ({ row }) => {
      const item = row.original
      return h(Badge, { variant: getTypeVariant(item.type) }, () => getTypeLabel(item.type))
    },
  },
  {
    id: "title",
    header: "标题",
    size: 240,
    cell: ({ row }) => {
      const item = row.original
      const classes = item.is_read ? "text-sm" : "text-sm font-medium"
      return h("span", { class: classes }, item.title)
    },
  },
  {
    id: "content",
    header: "内容",
    size: 320,
    cell: ({ row }) => {
      const item = row.original
      return h("span", { class: "block truncate text-sm text-muted-foreground", title: item.content }, item.content)
    },
  },
  {
    id: "sender_name",
    header: "发送者",
    size: 100,
    cell: ({ row }) => row.original.sender_name || "-",
  },
  {
    id: "created_at",
    header: "时间",
    size: 140,
    cell: ({ row }) => {
      return h("span", { class: "text-muted-foreground text-sm" }, formatDateTime(row.original.created_at))
    },
  },
  {
    id: "actions",
    header: "操作",
    size: 120,
    cell: ({ row }) => {
      const item = row.original
      return h("div", { class: "flex items-center gap-1" }, [
        !item.is_read
          ? h(
              Button,
              {
                size: "sm" as const,
                variant: "ghost" as const,
                class: "h-7 px-2",
                onClick: () => handleMarkRead(item),
              },
              () => "已读"
            )
          : null,
        item.link
          ? h(
              Button,
              {
                size: "sm" as const,
                variant: "ghost" as const,
                class: "h-7 px-2",
                onClick: () => handleLinkClick(item),
              },
              () => [h(ExternalLink, { class: "h-3.5 w-3.5 mr-1" }), "查看"]
            )
          : null,
      ])
    },
  },
]

// ========== 初始化 DataTable ==========

const dataTable = useDataTable<NotificationItem>({
  columns,
  remoteFetchFn: async ({ page, page_size }) => {
    const res = await getNotifications({
      page,
      page_size,
      keyword: keyword.value || undefined,
      type: typeFilter.value === "all" ? undefined : typeFilter.value,
      is_read: readFilter.value === "all" ? undefined : readFilter.value === "unread" ? false : true,
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
  loadUnreadCount()
})
</script>

<template>
  <AppPage title="站内信" variant="workbench" description="查看系统通知和消息，支持按类型和已读状态筛选">
    <!-- 顶部操作栏 -->
    <div class="flex flex-wrap items-center justify-between gap-3 rounded-md bg-background mb-4">
      <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2">
        <div class="relative">
          <Bell class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            v-model="keyword"
            placeholder="搜索通知..."
            class="pl-8 w-48"
          />
        </div>

        <Select v-model="typeFilter">
          <SelectTrigger class="w-32 max-w-full">
            <SelectValue placeholder="全部类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部类型</SelectItem>
            <SelectItem value="system">系统</SelectItem>
            <SelectItem value="permission">权限</SelectItem>
            <SelectItem value="policy">策略</SelectItem>
            <SelectItem value="general">通用</SelectItem>
          </SelectContent>
        </Select>

        <Select v-model="readFilter">
          <SelectTrigger class="w-32 max-w-full">
            <SelectValue placeholder="全部状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="unread">未读</SelectItem>
            <SelectItem value="read">已读</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="ml-auto flex shrink-0 items-center gap-2">
        <Badge v-if="unreadCount > 0" variant="default" class="mr-1">
          {{ unreadCount }} 条未读
        </Badge>
        <Button
          type="button"
          variant="outline"
          :disabled="unreadCount === 0 || markReadLoading"
          @click="handleMarkAllRead"
        >
          <CheckCheck class="mr-1 h-4 w-4" />
          全部已读
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

    <!-- 通知列表 -->
    <div class="flex min-h-0 flex-1 flex-col">
      <DataTable :data-table="dataTable" :fixed-layout="true" />
    </div>
  </AppPage>
</template>
