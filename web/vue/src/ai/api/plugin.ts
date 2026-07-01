/**
 * AI 插件管理 API
 *
 * 提供插件列表查询、安装、启动、停止等操作接口
 */

import { rawDel, rawGet, rawPatch, rawPost, rawPut, rawApiClient } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";

// ==================== 类型定义 ====================

/**
 * 可用插件信息（插件市场）
 */
export interface AvailablePlugin {
  plugin_id: string;
  plugin_unique_identifier: string;
  name: string;
  author: string;
  version: string;
  description?: string;
  icon?: string;
  plugin_type: string;
  runtime_type: string;
  is_installed: boolean;
  installation_status?: string;
  is_recommended: boolean;
  is_enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

/**
 * 插件信息（已安装）
 */
export interface PluginInfo {
  plugin_id: string;
  plugin_name: string;
  version: string;
  author: string;
  description?: string;
  icon?: string;
  status: string;
  plugin_type: string;
  runtime_type: string;
  auto_start: boolean;
  installed_at?: string;
  last_started_at?: string;
  last_stopped_at?: string;
  last_accessed_at?: string;
  process_id?: number;
  port?: number;
  call_count: number;
  error_count: number;
}

/**
 * 插件分页列表响应
 * 后端使用 ApiResponse.paginated() 返回，data 直接是插件数组
 */
export type PluginPaginatedListResponse = PluginInfo[];

/**
 * 插件安装响应
 */
export interface PluginInstallResponse {
  plugin_id: string;
  message: string;
}

/**
 * 插件操作响应（启动、停止等）
 */
export interface PluginOperationResponse {
  plugin_id: string;
  message: string;
  status: string;
}

/**
 * 插件凭证
 */
export interface PluginCredential {
  id: string;
  name: string;
  plugin_id: string;
  scope: string;
  provider_name?: string;
  credentials?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

/**
 * 插件凭证架构字段（与后端 PluginCredentialsSchemaVo 对齐）
 */
export interface PluginCredentialsSchemaField {
  name: string;
  label?: string;
  placeholder?: string;
  type?: "secret-input" | "text-input" | "select" | "number" | "boolean";
  required: boolean;
  description?: string;
  default?: string;
  options?: { label: string; value: string }[];
  help?: string;
  url?: string;
}

/**
 * 凭证验证结果
 */
export interface ValidateCredentialResult {
  success: boolean;
  error?: string;
}

// ==================== 配置管理类型 ====================

/**
 * 插件配置响应
 */
export interface PluginConfigResponse {
  plugin_id: string;
  plugin_config: Record<string, unknown>;  // 插件能力配置（只读）
  runtime_config: Record<string, unknown>;  // 运行时配置（可写）
}

/**
 * 更新插件配置请求
 */
export interface UpdatePluginConfigRequest {
  runtime_config: Record<string, unknown>;
}

// ==================== 运行时状态类型 ====================

/**
 * 插件运行时状态响应
 */
export interface RuntimeStateResponse {
  plugin_id: string;
  status: string;  // active/inactive/frozen
  process_id: number | null;
  port: number | null;
  work_directory: string | null;
  call_count: number;
  error_count: number;
  success_rate: number | null;
  health_status: string;  // healthy/unhealthy/unknown
  last_started_at: string | null;
  last_stopped_at: string | null;
  last_accessed_at: string | null;
  last_error: string | null;
}

/**
 * 插件统计数据
 */
export interface PluginStatistics {
  status_stats: {
    active: number;
    inactive: number;
    frozen: number;
    total: number;
  };
  usage_stats: {
    total_calls: number;
    total_errors: number;
    avg_success_rate: number;
  };
  runtime_stats: {
    total_memory_mb: number;
    total_cpu_percent: number;
  };
}

// ==================== Console API (用户端) ====================

const CONSOLE_BASE = "/ai/console/v1/plugins";

/**
 * 获取插件列表
 */
export async function getPluginList(params?: {
  status?: string;
  plugin_id?: string;
  plugin_type?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<PluginPaginatedListResponse>> {
  return rawGet(CONSOLE_BASE, { params });
}

/**
 * 获取可用插件列表
 */
export async function getAvailablePlugins(params?: {
  keyword?: string;
  type?: string;
  is_recommended?: boolean;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<AvailablePlugin[]>> {
  return rawGet(`${CONSOLE_BASE}/available`, { params });
}

/**
 * 创建插件安装任务
 */
export async function createPluginInstallation(data: {
  plugin_id: string;
  auto_start?: boolean;
  install_config?: Record<string, unknown>;
}): Promise<ApiResponse<{ task_id: string }>> {
  return rawPost(`${CONSOLE_BASE}/installations`, data);
}

/**
 * 获取安装任务列表
 */
export async function getInstallTasks(params?: {
  status?: string;
  plugin_id?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<unknown>> {
  return rawGet(`${CONSOLE_BASE}/install-tasks`, { params });
}

/**
 * 获取安装任务详情
 */
export async function getInstallTaskDetail(taskId: string): Promise<ApiResponse<unknown>> {
  return rawGet(`${CONSOLE_BASE}/install-tasks/${taskId}`);
}

/**
 * 获取插件详情
 */
export async function getPluginInfo(pluginId: string): Promise<ApiResponse<PluginInfo>> {
  return rawGet(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}`);
}

/**
 * 获取插件凭证列表
 */
export async function getPluginCredentials(
  pluginId: string,
  params?: { page?: number; page_size?: number; name?: string }
): Promise<ApiResponse<PluginCredential[]>> {
  return rawGet(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials`, { params });
}

/**
 * 获取凭证详情
 */
export async function getCredentialDetail(
  pluginId: string,
  credentialId: string
): Promise<ApiResponse<PluginCredential>> {
  return rawGet(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials/${credentialId}`);
}

/**
 * 获取插件凭证架构
 */
export async function getPluginCredentialsSchema(
  pluginId: string
): Promise<ApiResponse<PluginCredentialsSchemaField[]>> {
  return rawGet(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials-schema`);
}

/**
 * 创建插件凭证
 */
export async function createPluginCredential(
  pluginId: string,
  data: { name: string; credentials: Record<string, unknown> }
): Promise<ApiResponse<PluginCredential>> {
  return rawPost(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials`, { ...data, plugin_id: pluginId });
}

/**
 * 更新插件凭证
 */
export async function updatePluginCredential(
  pluginId: string,
  credentialId: string,
  data: { name?: string; credentials?: Record<string, unknown> }
): Promise<ApiResponse<PluginCredential>> {
  return rawPut(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials/${credentialId}`, data);
}

/**
 * 删除插件凭证
 */
export async function deletePluginCredential(
  pluginId: string,
  credentialId: string
): Promise<ApiResponse<boolean>> {
  return rawDel(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials/${credentialId}`);
}

/**
 * 验证插件凭证（前端提交的原始凭证）
 */
export async function validatePluginCredential(
  pluginId: string,
  data: { credentials: Record<string, unknown> }
): Promise<ApiResponse<ValidateCredentialResult>> {
  return rawPost(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials/validate`, data);
}

/**
 * 验证已存储的插件凭证
 */
export async function validateStoredCredential(
  pluginId: string,
  credentialId: string
): Promise<ApiResponse<ValidateCredentialResult>> {
  return rawPost(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials/${credentialId}/validate`);
}

// ==================== 配置管理 API ====================

/**
 * 获取插件配置
 */
export async function getPluginConfig(pluginId: string): Promise<ApiResponse<PluginConfigResponse>> {
  return rawGet(`${CONSOLE_BASE}/installations/config`, { params: { plugin_id: pluginId } });
}

/**
 * 更新插件配置
 */
export async function updatePluginConfig(
  pluginId: string,
  data: UpdatePluginConfigRequest
): Promise<ApiResponse<PluginConfigResponse>> {
  return rawPatch(`${CONSOLE_BASE}/installations/config`, data, { params: { plugin_id: pluginId } });
}

// ==================== 运行时状态 API ====================

/**
 * 获取插件运行时状态
 */
export async function getPluginRuntimeState(
  pluginId: string
): Promise<ApiResponse<RuntimeStateResponse>> {
  return rawGet(`${CONSOLE_BASE}/installations/runtime-state`, { params: { plugin_id: pluginId } });
}

/**
 * 获取插件统计数据
 */
export async function getPluginStatistics(): Promise<ApiResponse<PluginStatistics>> {
  return rawGet(`${CONSOLE_BASE}/installations/statistics`);
}

// ==================== 插件操作 API ====================

/**
 * 启动插件
 */
export async function startPluginQuery(pluginId: string): Promise<ApiResponse<PluginOperationResponse>> {
  return rawPost(`${CONSOLE_BASE}/installations/start`, null, { params: { plugin_id: pluginId } });
}

/**
 * 停止插件
 */
export async function stopPluginQuery(pluginId: string): Promise<ApiResponse<PluginOperationResponse>> {
  return rawPost(`${CONSOLE_BASE}/installations/stop`, null, { params: { plugin_id: pluginId } });
}

/**
 * 卸载插件
 */
export async function uninstallPluginQuery(pluginId: string): Promise<ApiResponse<PluginOperationResponse>> {
  return rawDel(`${CONSOLE_BASE}/installations`, { params: { plugin_id: pluginId } });
}

// ==================== Admin API (管理端) ====================

const ADMIN_BASE = "/ai/admin/v1/plugins";

/**
 * 管理端获取插件列表
 */
export async function adminGetPluginList(params?: {
  status?: string;
  plugin_id?: string;
  plugin_type?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<PluginPaginatedListResponse>> {
  return rawGet(ADMIN_BASE, { params });
}

/**
 * 上传安装插件
 */
export async function uploadPlugin(data: {
  plugin_file: File;
  auto_start?: boolean;
  install_config?: Record<string, unknown>;
}): Promise<ApiResponse<PluginInstallResponse>> {
  const formData = new FormData();
  formData.append("plugin_file", data.plugin_file);
  if (data.auto_start !== undefined) {
    formData.append("auto_start", String(data.auto_start));
  }
  if (data.install_config) {
    formData.append("install_config", JSON.stringify(data.install_config));
  }
  return rawApiClient.post(`${ADMIN_BASE}/upload`, formData, { headers: { "Content-Type": "multipart/form-data" } });
}

/**
 * 启动插件
 */
export async function startPlugin(pluginId: string): Promise<ApiResponse<PluginOperationResponse>> {
  return rawPost(`${ADMIN_BASE}/${encodeURIComponent(pluginId)}/start`);
}

/**
 * 停止插件
 */
export async function stopPlugin(pluginId: string): Promise<ApiResponse<PluginOperationResponse>> {
  return rawPost(`${ADMIN_BASE}/${encodeURIComponent(pluginId)}/stop`);
}

/**
 * 卸载插件
 */
export async function uninstallPlugin(pluginId: string): Promise<ApiResponse<PluginOperationResponse>> {
  return rawDel(`${ADMIN_BASE}/${encodeURIComponent(pluginId)}`);
}

/**
 * 管理端获取插件详情
 */
export async function adminGetPluginInfo(pluginId: string): Promise<ApiResponse<PluginInfo>> {
  return rawGet(`${ADMIN_BASE}/${encodeURIComponent(pluginId)}`);
}

/**
 * 升级插件
 */
export async function upgradePlugin(data: {
  plugin_id: string;
  plugin_file: File;
  auto_start?: boolean;
  install_config?: Record<string, unknown>;
}): Promise<ApiResponse<PluginInstallResponse>> {
  const formData = new FormData();
  formData.append("plugin_file", data.plugin_file);
  if (data.auto_start !== undefined) {
    formData.append("auto_start", String(data.auto_start));
  }
  if (data.install_config) {
    formData.append("install_config", JSON.stringify(data.install_config));
  }
  return rawApiClient.post(`${ADMIN_BASE}/${encodeURIComponent(data.plugin_id)}/upgrade`, formData, { headers: { "Content-Type": "multipart/form-data" } });
}

