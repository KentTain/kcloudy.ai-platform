/**
 * 模型 API 函数
 *
 * 与后端 AI 服务的模型接口通信
 */
import { get } from "@/framework/api/client";
import type { Success } from "@/framework/types";

/**
 * 模型项
 */
export interface ModelItem {
  id: string;
  name: string;
  description: string | null;
}

/**
 * 提供商项
 */
export interface ProviderItem {
  id: string;
  name: string;
  models: ModelItem[];
}

/**
 * 模型列表响应
 */
export interface ModelListResponse {
  providers: ProviderItem[];
}

/**
 * 获取模型列表
 */
export const getModels = (): Promise<ModelListResponse> =>
  get<Success<ModelListResponse>>("/ai/console/v1/models").then((res) => res.data);
