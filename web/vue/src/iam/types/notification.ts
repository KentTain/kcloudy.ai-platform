/**
 * 站内信类型定义
 */

import type { BasePaginatedQuery } from "@/framework/types";

/** 站内信项 */
export interface NotificationItem {
  id: string;
  tenant_id: string;
  user_id: string;
  title: string;
  content: string;
  type: "system" | "permission" | "policy" | "general";
  is_read: boolean;
  link?: string;
  sender_id?: string;
  sender_name?: string;
  created_at: string;
  read_at?: string;
}

/** 站内信查询参数 */
export interface NotificationQuery extends BasePaginatedQuery {
  type?: string;
  is_read?: boolean;
  keyword?: string;
}

/** 标记已读请求 */
export interface NotificationMarkReadRequest {
  notification_ids: string[];
}
