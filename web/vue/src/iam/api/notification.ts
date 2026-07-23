/**
 * 站内信 API
 */

import { get, post } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type {
  NotificationItem,
  NotificationQuery,
  NotificationMarkReadRequest,
} from "@/iam/types/notification";

/**
 * 获取站内信列表
 */
export const getNotifications = (params?: NotificationQuery) =>
  get<ApiResponse<NotificationItem[]>>("/iam/console/v1/notifications", { params });

/**
 * 获取未读站内信数量
 */
export const getUnreadCount = () =>
  get<ApiResponse<number>>("/iam/console/v1/notifications/unread-count");

/**
 * 标记站内信已读
 */
export const markRead = (data: NotificationMarkReadRequest) =>
  post<ApiResponse<void>>("/iam/console/v1/notifications/mark-read", data);

/**
 * 全部标记已读
 */
export const markAllRead = () =>
  post<ApiResponse<void>>("/iam/console/v1/notifications/mark-all-read");
