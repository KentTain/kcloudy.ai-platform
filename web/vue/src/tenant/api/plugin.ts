import { rawDel, rawGet, rawPost, rawPatch } from '@/framework/api/client';
import type { ApiResponse, PaginatedResponse } from '@/framework/api/types';

// ==================== 类型定义 ====================

export interface PluginDefinition {
  id: string;
  plugin_id: string;
  plugin_unique_identifier: string;
  refers: number;
  install_type: string;
  manifest_type?: string;
  is_recommended: boolean;
  is_enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PluginDefinitionDetail extends PluginDefinition {
  declaration: Record<string, any>;
}

export interface PluginDefinitionQuery {
  page?: number;
  page_size?: number;
  keyword?: string;
  type?: string;
  is_recommended?: boolean;
  is_enabled?: boolean;
}

export interface UpdatePluginDefinitionRequest {
  is_recommended?: boolean;
  is_enabled?: boolean;
}

export interface ScanDirectoryRequest {
  directory: string;
  recursive?: boolean;
}

export interface ScannedPluginResult {
  plugin_id: string;
  version: string;
  status: string;
  message?: string;
}

export interface ScanDirectoryResponse {
  total_count: number;
  success_count: number;
  skipped_count: number;
  failed_count: number;
  results: ScannedPluginResult[];
}

export interface UploadPluginResponse {
  plugin_id: string;
  version: string;
  plugin_unique_identifier: string;
  status: string;
  message: string;
}

export interface DefinitionStats {
  total_count: number;
  by_type: Record<string, number>;
  recommended_count: number;
  enabled_count: number;
}

export interface InstallationStats {
  total_count: number;
  active_count: number;
  weekly_new_count: number;
}

export interface PluginStatistics {
  definition_stats: DefinitionStats;
  installation_stats: InstallationStats;
  cached_at?: string;
}

// ==================== API 函数 ====================

export const getPluginDefinitions = (params?: PluginDefinitionQuery) =>
  rawGet<PaginatedResponse<PluginDefinition>>('/tenant/admin/v1/plugin-definitions', { params });

export const getPluginDefinition = (id: string) =>
  rawGet<ApiResponse<PluginDefinitionDetail>>('/tenant/admin/v1/plugin-definitions/');

export const updatePluginDefinition = (id: string, data: UpdatePluginDefinitionRequest) =>
  rawPatch<ApiResponse<PluginDefinition>>('/tenant/admin/v1/plugin-definitions/', data);

export const deletePluginDefinition = (id: string) =>
  rawDel<ApiResponse<void>>('/tenant/admin/v1/plugin-definitions/');

export const scanDirectoryForPlugins = (data: ScanDirectoryRequest) =>
  rawPost<ApiResponse<ScanDirectoryResponse>>('/tenant/admin/v1/plugin-definitions/scan', data);

export const uploadPluginPackage = (file: File, overwrite?: boolean) => {
  const formData = new FormData();
  formData.append('file', file);
  if (overwrite !== undefined) {
    formData.append('overwrite', String(overwrite));
  }
  return rawPost<ApiResponse<UploadPluginResponse>>('/tenant/admin/v1/plugin-definitions/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getPluginStatistics = () =>
  rawGet<ApiResponse<PluginStatistics>>('/tenant/admin/v1/plugin-definitions/statistics');
