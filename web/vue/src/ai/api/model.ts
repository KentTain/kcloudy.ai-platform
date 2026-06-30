/**
 * 模型 API 函数
 *
 * 与后端 AI 服务的模型接口通信
 */
import { get, post } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";

/**
 * 模型项
 */
export interface ModelItem {
  id: string;
  name: string;
  label?: string;
  description: string | null;
}

/**
 * 提供商项
 */
export interface ProviderItem {
  id: string;
  name: string;
  icon_small?: string;
  icon_large?: string;
  models: ModelItem[];
}

/**
 * 模型列表响应
 */
export interface ModelListResponse {
  providers: ProviderItem[];
}

/**
 * 默认模型配置
 */
export interface DefaultModel {
  id: string;
  tenant_id: string;
  model_type: string;
  plugin_id: string;
  model_name?: string;
  credential_id?: string;
  custom_base_url?: string;
  custom_model_name?: string;
  is_valid: boolean;
}

/**
 * 获取模型列表
 */
export const getModels = (): Promise<ModelListResponse> =>
  get<ApiResponse<ModelListResponse>>("/ai/console/v1/models").then((res) => res.data!);

/**
 * 获取默认模型
 */
export const getDefaultModel = (modelType: string): Promise<DefaultModel | null> =>
  get<ApiResponse<DefaultModel>>("/ai/console/v1/plugins/default-models", {
    params: { model_type: modelType },
  }).then((res) => res.data ?? null);

/**
 * 设置默认模型
 */
export const setDefaultModel = (data: {
  model_type: string;
  plugin_id: string;
  model_name?: string;
  credential_id?: string;
  custom_base_url?: string;
  custom_model_name?: string;
}): Promise<DefaultModel> =>
  post<ApiResponse<DefaultModel>>("/ai/console/v1/plugins/default-models", data).then(
    (res) => res.data!
  );
