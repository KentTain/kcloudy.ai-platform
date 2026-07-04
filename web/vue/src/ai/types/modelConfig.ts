/**
 * 模型配置类型定义
 */

/** 模型类型 */
export type ModelTypeKey =
  | "llm"
  | "text-embedding"
  | "rerank"
  | "speech2text"
  | "moderation"
  | "tts"
  | "text2img";

/** 模型类型标签映射 */
export const MODEL_TYPE_LABELS: Record<ModelTypeKey, string> = {
  llm: "LLM",
  "text-embedding": "嵌入",
  rerank: "排序",
  speech2text: "语音转文本",
  moderation: "内容审核",
  tts: "文本转语音",
  text2img: "文本转图片",
};

/** 模型配置项（二级行数据） */
export interface ModelConfigItem {
  model_name: string;
  model_label?: string;
  model_type: ModelTypeKey;
  is_default: boolean;
}

/** 插件及其模型（一级+二级数据） */
export interface PluginWithModels {
  plugin_id: string;
  plugin_name: string;
  status: string;
  models: ModelConfigItem[];
}

/** 默认模型展示项 */
export interface DefaultModelItem {
  model_type: ModelTypeKey;
  plugin_id?: string;
  model_name?: string;
  is_valid: boolean;
}

/** 可选模型项（配置模型弹窗用） */
export interface AvailableModelItem {
  model_name: string;
  model_label?: string;
  model_type: ModelTypeKey;
  is_enabled: boolean;
}

/** 默认模型选择项（设置默认弹窗用） */
export interface ModelSelectItem {
  plugin_id: string;
  plugin_name: string;
  provider: string;
  model_name: string;
  model_label?: string;
  model_type: ModelTypeKey;
}

/** 模型配置页面聚合响应 */
export interface ModelConfigOverviewResponse {
  total_plugins: number;
  configured_plugins: number;
  total_models: number;
  default_models: DefaultModelItem[];
  plugins: PluginWithModels[];
}
