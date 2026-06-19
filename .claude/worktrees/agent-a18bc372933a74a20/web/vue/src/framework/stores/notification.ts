import { defineStore } from "pinia";
import { ref, computed } from "vue";

/**
 * 通知类型
 */
export type NotificationType = "system" | "warning" | "success";

/**
 * 通知项
 */
export interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  content: string;
  time: Date;
  read: boolean;
}

/**
 * 通知状态管理
 */
export const useNotificationStore = defineStore("notification", () => {
  const notifications = ref<NotificationItem[]>([]);

  const unreadCount = computed(
    () => notifications.value.filter((n) => !n.read).length
  );

  const hasUnread = computed(() => unreadCount.value > 0);

  function addNotification(notification: Omit<NotificationItem, "id" | "time" | "read">) {
    notifications.value.push({
      ...notification,
      id: `notification-${Date.now()}`,
      time: new Date(),
      read: false,
    });
  }

  function markAsRead(id: string) {
    const notification = notifications.value.find((n) => n.id === id);
    if (notification) {
      notification.read = true;
    }
  }

  function markAllAsRead() {
    notifications.value.forEach((n) => (n.read = true));
  }

  function clearAll() {
    notifications.value = [];
  }

  // 模拟数据（开发用）
  function initMockData() {
    notifications.value = [
      {
        id: "1",
        type: "system",
        title: "系统升级通知",
        content: "系统将于今晚 22:00 进行维护升级，届时服务将暂停约 30 分钟。",
        time: new Date(Date.now() - 10 * 60 * 1000),
        read: false,
      },
      {
        id: "2",
        type: "warning",
        title: "存储空间预警",
        content: "知识库存储空间已使用 85%，建议及时清理或扩容。",
        time: new Date(Date.now() - 60 * 60 * 1000),
        read: false,
      },
      {
        id: "3",
        type: "success",
        title: "文档处理完成",
        content: "《API 设计规范》已成功向量化，共处理 128 个文档片段。",
        time: new Date(Date.now() - 2 * 60 * 60 * 1000),
        read: true,
      },
    ];
  }

  return {
    notifications,
    unreadCount,
    hasUnread,
    addNotification,
    markAsRead,
    markAllAsRead,
    clearAll,
    initMockData,
  };
});

export default useNotificationStore;
