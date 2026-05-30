<script setup lang="ts">
/**
 * AppNotificationPanel 通知面板组件
 * 显示通知列表，支持全部已读
 */
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { useNotificationStore, type NotificationItem } from "@/framework/stores/notification";

const router = useRouter();
const notificationStore = useNotificationStore();

const notifications = computed(() => notificationStore.notifications);
const unreadCount = computed(() => notificationStore.unreadCount);

function getTypeBgClass(type: NotificationItem["type"]) {
  const classes = {
    system: "bg-blue-50 dark:bg-blue-950",
    warning: "bg-amber-50 dark:bg-amber-950",
    success: "bg-green-50 dark:bg-green-950",
  };
  return classes[type];
}

function getTypeIcon(type: NotificationItem["type"]) {
  const icons = {
    system: "📢",
    warning: "⚠️",
    success: "✅",
  };
  return icons[type];
}

function formatTime(date: Date) {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / (1000 * 60));
  const hours = Math.floor(diff / (1000 * 60 * 60));

  if (minutes < 60) return `${minutes} 分钟前`;
  if (hours < 24) return `${hours} 小时前`;
  return date.toLocaleDateString();
}

function handleMarkAllRead() {
  notificationStore.markAllAsRead();
}

function handleViewAll() {
  router.push("/notifications");
}
</script>

<template>
  <Popover>
    <PopoverTrigger as-child>
      <Button variant="ghost" size="icon" class="relative h-9 w-9">
        <span class="text-base">🔔</span>
        <span
          v-if="unreadCount > 0"
          class="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full border-2 border-background"
        />
      </Button>
    </PopoverTrigger>
    <PopoverContent align="end" class="w-[360px] p-0">
      <!-- 标题栏 -->
      <div class="flex items-center justify-between px-4 py-3 border-b">
        <span class="text-sm font-semibold">通知</span>
        <button
          type="button"
          class="text-xs text-primary hover:underline"
          @click="handleMarkAllRead"
        >
          全部已读
        </button>
      </div>

      <!-- 通知列表 -->
      <div class="max-h-[320px] overflow-auto">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="px-4 py-3 border-b last:border-b-0 hover:bg-muted/50 transition-colors"
          :class="{ 'bg-muted/30': !notification.read }"
        >
          <div class="flex gap-3">
            <div
              class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
              :class="getTypeBgClass(notification.type)"
            >
              {{ getTypeIcon(notification.type) }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-[13px] font-medium text-foreground">
                {{ notification.title }}
              </div>
              <div class="text-[12px] text-muted-foreground mt-1 line-clamp-2">
                {{ notification.content }}
              </div>
              <div class="text-[11px] text-muted-foreground/70 mt-1">
                {{ formatTime(notification.time) }}
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="notifications.length === 0"
          class="py-8 text-center text-sm text-muted-foreground"
        >
          暂无通知
        </div>
      </div>

      <!-- 底部 -->
      <div class="px-4 py-3 border-t text-center">
        <button
          type="button"
          class="text-xs text-primary hover:underline"
          @click="handleViewAll"
        >
          查看全部通知
        </button>
      </div>
    </PopoverContent>
  </Popover>
</template>
