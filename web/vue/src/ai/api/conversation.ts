/**
 * 会话 API 函数
 *
 * 与后端 AI 服务的会话接口通信
 */
import { del, get } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";

/**
 * 会话列表项（与后端 Schema 一致）
 */
export interface ConversationListItem {
  id: string;
  name: string;
  created_at: string;
  message_count: number;
}

/**
 * 会话列表响应
 */
export interface ConversationListResponse {
  conversations: ConversationListItem[];
}

/**
 * 获取会话列表
 */
export const getConversations = (): Promise<ConversationListResponse> =>
  get<ApiResponse<ConversationListResponse>>("/ai/console/v1/conversations").then((res) => res.data!);

/**
 * 删除会话
 */
export const deleteConversation = (id: string): Promise<{ success: boolean }> =>
  del<ApiResponse<{ success: boolean }>>(`/ai/console/v1/conversations/${id}`).then((res) => res.data!);
