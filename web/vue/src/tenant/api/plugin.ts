import { rawDel, rawGet, rawPatch, rawPost, rawPut } from '@/framework/api/client';
import type { ApiResponse } from '@/framework/api/types';

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

// ==================== 预览功能类型 ====================

export interface ScannedPluginPreview {
  plugin_id: string;
  version: string;
  name: string;
  description: string;
  exists: boolean;
  status: 'ready' | 'invalid';
  error_message?: string;
}

export interface ParsedPluginInfo {
  plugin_id: string;
  version: string;
  name: string;
  description: string;
  manifest_type: string;
  declaration: Record<string, any>;
  exists: boolean;
}

export interface ScanDirectoryConfirmRequest {
  directory: string;
  recursive?: boolean;
  plugin_ids: string[];
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

// ==================== 安装到租户 ====================

export interface InstallToTenantsRequest {
  tenant_ids: string[];
  auto_start?: boolean;
}

export interface InstallSuccessItem {
  tenant_id: string;
  plugin_id: string;
}

export interface InstallFailedItem {
  tenant_id: string;
  message: string;
}

export interface InstallSkippedItem {
  tenant_id: string;
  reason: string;
}

export interface InstallToTenantsResponse {
  success: InstallSuccessItem[];
  failed: InstallFailedItem[];
  skipped: InstallSkippedItem[];
}

// ==================== API 函数 ====================

export const getPluginDefinitions = (params?: PluginDefinitionQuery) =>
  rawGet<ApiResponse<PluginDefinition[]>>('/tenant/admin/v1/plugin-definitions', { params });

export const getPluginDefinition = (id: string) =>
  rawGet<ApiResponse<PluginDefinitionDetail>>(`/tenant/admin/v1/plugin-definitions/${id}`);

export const updatePluginDefinition = (id: string, data: UpdatePluginDefinitionRequest) =>
  rawPatch<ApiResponse<PluginDefinition>>(`/tenant/admin/v1/plugin-definitions/${id}`, data);

export const deletePluginDefinition = (id: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/plugin-definitions/${id}`);

export const scanDirectoryForPlugins = (data: ScanDirectoryConfirmRequest) =>
  rawPost<ApiResponse<ScanDirectoryResponse>>('/tenant/admin/v1/plugin-definitions/scan', data);

// ==================== 预览功能 API ====================

export const scanDirectoryPreview = (data: ScanDirectoryRequest) =>
  rawPost<ApiResponse<ScannedPluginPreview[]>>('/tenant/admin/v1/plugin-definitions/scan/preview', data);

export const parsePluginPackage = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return rawPost<ApiResponse<ParsedPluginInfo>>('/tenant/admin/v1/plugin-definitions/parse', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

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

export const installPluginToTenants = (pluginId: string, data: InstallToTenantsRequest) =>
  rawPost<ApiResponse<InstallToTenantsResponse>>(`/tenant/admin/v1/plugin-definitions/${pluginId}/install`, data);

