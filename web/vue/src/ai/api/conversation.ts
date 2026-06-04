/**
 * 会话 API 函数
 *
 * 与后端 AI 服务的会话接口通信
 */
import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/types";
import type { Conversation } from "@/ai/types";

/**
 * 创建会话请求参数
 */
export interface CreateConversationParams {
  title?: string;
}

/**
 * 更新会话请求参数
 */
export interface UpdateConversationParams {
  title?: string;
}

/**
 * 获取会话列表
 */
export const getConversations = (): Promise<Conversation[]> =>
  get<ApiResponse<Conversation[]>>("/v1/conversations").then((res) => res.data);

/**
 * 获取会话详情
 */
export const getConversation = (id: string): Promise<Conversation> =>
  get<ApiResponse<Conversation>>(`/v1/conversations/${id}`).then((res) => res.data);

/**
 * 创建会话
 */
export const createConversation = (params?: CreateConversationParams): Promise<Conversation> =>
  post<ApiResponse<Conversation>>("/v1/conversations", params).then((res) => res.data);

/**
 * 更新会话
 */
export const updateConversation = (
  id: string,
  params: UpdateConversationParams
): Promise<Conversation> =>
  put<ApiResponse<Conversation>>(`/v1/conversations/${id}`, params).then((res) => res.data);

/**
 * 删除会话
 */
export const deleteConversation = (id: string): Promise<void> =>
  del(`/v1/conversations/${id}`);
