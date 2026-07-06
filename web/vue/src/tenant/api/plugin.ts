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

// ==================== 插件启停 ====================

export interface BatchStartStopRequest {
  plugin_id: string;
  tenant_ids: string[];
}

export interface BatchOperationItem {
  tenant_id: string;
  plugin_id: string;
  status: string;
}

export interface BatchOperationFailedItem {
  tenant_id: string;
  plugin_id: string;
  error: string;
}

export interface BatchStartStopResponse {
  success: BatchOperationItem[];
  failed: BatchOperationFailedItem[];
}

// ==================== 插件安装记录 ====================

export interface PluginInstallation {
  tenant_id: string;
  plugin_id: string;
  plugin_unique_identifier: string;
  declaration: Record<string, any>;
  status: string; // PENDING / ACTIVE / INACTIVE / FAILED
  installed_at?: string;
  plugin_type?: string;
  runtime_type?: string;
  source?: string;
}

export interface PluginInstallationQuery {
  page?: number;
  page_size?: number;
  tenant_id?: string;
  plugin_id?: string;
  status?: string;
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

export const startPluginInstallation = (tenantId: string, pluginId: string) =>
  rawPost<ApiResponse<{ tenant_id: string; plugin_id: string; status: string }>>(
    `/tenant/admin/v1/plugin-installations/${tenantId}/${pluginId}/start`,
  );

export const stopPluginInstallation = (tenantId: string, pluginId: string) =>
  rawPost<ApiResponse<{ tenant_id: string; plugin_id: string; status: string }>>(
    `/tenant/admin/v1/plugin-installations/${tenantId}/${pluginId}/stop`,
  );

export const batchStartPluginInstallations = (data: BatchStartStopRequest) =>
  rawPost<ApiResponse<BatchStartStopResponse>>(
    '/tenant/admin/v1/plugin-installations/start/batch',
    data,
  );

export const batchStopPluginInstallations = (data: BatchStartStopRequest) =>
  rawPost<ApiResponse<BatchStartStopResponse>>(
    '/tenant/admin/v1/plugin-installations/stop/batch',
    data,
  );

// ==================== 插件安装记录管理 ====================

export const getPluginInstallations = (params?: PluginInstallationQuery) =>
  rawGet<ApiResponse<PluginInstallation[]>>('/tenant/admin/v1/plugin-installations', { params });

export const uninstallPluginInstallation = (tenantId: string, pluginId: string) =>
  rawDel<ApiResponse<void>>(
    `/tenant/admin/v1/plugin-installations/${tenantId}/${pluginId}`,
  );

// ==================== Skill 相关类型 ====================

export interface RemoteSkillInfo {
  plugin_id: string;
  name: string;
  description: string | null;
  version: string;
  author: string;
  plugin_type: 'skill';
  skill_type: 'knowledge' | 'script';
  tags: string[];
  downloads: number | null;
  icon: string | null;
  download_url: string;
}

export interface SkillPreviewResponse {
  skill_id: string;
  name: string;
  description: string | null;
  skill_type: 'knowledge' | 'script';
  documents: Record<string, string>;
}

// ==================== Skill API 函数 ====================

export const getRemoteSkills = (
  marketplaceId: string,
  params?: { keyword?: string; page?: number; page_size?: number }
) =>
  rawGet<ApiResponse<RemoteSkillInfo[]>>(
    `/tenant/admin/v1/marketplaces/${marketplaceId}/plugins`,
    { params: { ...params, type: 'skill' } }
  );

export async function syncSkillFromMarketplace(
  marketplaceId: string,
  skillId: string
): Promise<ApiResponse<PluginDefinition>> {
  return rawPost(`/tenant/admin/v1/marketplaces/${marketplaceId}/skills/${encodeURIComponent(skillId)}/sync`);
}

export async function getInstalledSkills(): Promise<ApiResponse<PluginDefinition[]>> {
  return rawGet('/tenant/admin/v1/plugins?plugin_type=skill');
}

export async function previewSkill(
  skillId: string
): Promise<ApiResponse<SkillPreviewResponse>> {
  return rawGet(`/ai/console/v1/skills/${encodeURIComponent(skillId)}/preview`);
}

export async function invokeSkillStream(
  request: {
    conversation_id: string;
    skill_ids: string[];
    user_message: string;
  },
  onChunk: (chunk: string) => void,
  onComplete: (fullMessage: string) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch('/ai/console/v1/skills/invoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      onError(`HTTP ${response.status}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError('无法读取响应流');
      return;
    }

    const decoder = new TextDecoder();
    let fullMessage = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(line => line.startsWith('data: '));

      for (const line of lines) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'chunk' && data.content) {
            fullMessage += data.content;
            onChunk(data.content);
          } else if (data.type === 'complete') {
            onComplete(fullMessage || data.message || '');
          } else if (data.type === 'error') {
            onError(data.error || '调用失败');
          }
        } catch (e) {
          // 忽略解析错误的行
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error.message : '网络错误');
  }
}

