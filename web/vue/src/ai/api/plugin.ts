/**
 * AI 插件管理 API
 *
 * 提供插件列表查询、安装、启动、停止等操作接口
 */

import { rawDel, rawGet, rawPost, rawPut, rawApiClient } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";

// ==================== 类型定义 ====================

/**
 * 插件信息
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
 */
export interface PluginPaginatedListResponse {
  plugins: PluginInfo[];
}

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
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/**
 * 插件凭证架构项
 */
export interface PluginCredentialsSchema {
  credentials_name: string;
  credential_form_schema: Record<string, unknown>;
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
  limit?: number;
  offset?: number;
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
}): Promise<ApiResponse<unknown>> {
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
): Promise<ApiResponse<PluginCredentialsSchema[]>> {
  return rawGet(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials-schema`);
}

/**
 * 创建插件凭证
 */
export async function createPluginCredential(
  pluginId: string,
  data: { name: string; config: Record<string, unknown> }
): Promise<ApiResponse<PluginCredential>> {
  return rawPost(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/credentials`, data);
}

/**
 * 更新插件凭证
 */
export async function updatePluginCredential(
  pluginId: string,
  credentialId: string,
  data: { name?: string; config?: Record<string, unknown> }
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

// ==================== Admin API (管理端) ====================

const ADMIN_BASE = "/ai/admin/v1/plugins";

/**
 * 管理端获取插件列表
 */
export async function adminGetPluginList(params?: {
  status?: string;
  plugin_id?: string;
  plugin_type?: string;
  limit?: number;
  offset?: number;
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

