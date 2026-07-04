/**
 * 模型配置 API 函数
 */
import { get, post } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type {
  AvailableModelItem,
  ModelConfigOverviewResponse,
  ModelSelectItem,
} from "@/ai/types/modelConfig";

/** 获取模型配置页面聚合数据 */
export const getModelConfigOverview = (): Promise<ModelConfigOverviewResponse> =>
  get<ApiResponse<ModelConfigOverviewResponse>>("/ai/console/v1/model-config/overview").then(
    (res) => res.data!,
  );

/** 获取插件可用模型列表 */
export const getAvailableModels = (pluginId: string): Promise<AvailableModelItem[]> =>
  get<ApiResponse<{ models: AvailableModelItem[] }>>(
    `/ai/console/v1/model-config/plugins/${pluginId}/available-models`,
  ).then((res) => res.data?.models ?? []);

/** 配置插件启用的模型 */
export const setEnabledModels = (
  pluginId: string,
  data: { model_names: string[] },
): Promise<void> =>
  post<ApiResponse<null>>(
    `/ai/console/v1/model-config/plugins/${pluginId}/enabled-models`,
    data,
  ).then(() => {});

/** 按类型获取可选模型（设置默认模型弹窗用） */
export const getModelsByType = (modelType: string): Promise<ModelSelectItem[]> =>
  get<ApiResponse<ModelSelectItem[]>>("/ai/console/v1/model-config/models", {
    params: { model_type: modelType },
  }).then((res) => res.data ?? []);

/** 批量设置默认模型 */
export const batchSetDefaultModels = (
  data: {
    items: { model_type: string; plugin_id: string; model_name?: string }[];
  },
): Promise<void> =>
  post<ApiResponse<null>>("/ai/console/v1/model-config/default-models/batch", data).then(
    () => {},
  );
