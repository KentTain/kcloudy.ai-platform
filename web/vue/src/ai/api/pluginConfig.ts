/**
 * 插件配置管理 API
 *
 * 提供插件配置、测试连接、启动、停止等操作接口。
 * 对应后端 plugin_config_controller，路由前缀：/ai/console/v1/plugins/installations
 */

import { rawPost } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";

// ==================== 类型定义 ====================

/**
 * 配置插件请求
 */
export interface ConfigPluginRequest {
  /** 插件能力配置，如 API Key、Endpoint 等 */
  plugin_config?: Record<string, unknown>;
  /** 运行时配置，如超时时间、重试次数等 */
  runtime_config?: Record<string, unknown>;
}

/**
 * 配置插件响应
 */
export interface ConfigPluginResponse {
  /** 插件 ID */
  plugin_id: string;
  /** 配置验证状态：null=未测试, true=验证通过, false=验证失败 */
  validated: boolean | null;
  /** 配置保存或验证的消息 */
  message?: string;
}

/**
 * 测试插件配置连接响应
 */
export interface TestPluginResponse {
  /** 插件 ID */
  plugin_id: string;
  /** 配置验证结果 */
  validated: boolean;
  /** 验证结果消息 */
  message: string;
}

/**
 * 启动插件响应
 */
export interface StartPluginResponse {
  /** 插件 ID */
  plugin_id: string;
  /** 插件状态：ACTIVE */
  status: string;
  /** 运行端口 */
  port?: number | null;
  /** 警告信息（如配置未验证） */
  warning?: string | null;
}

/**
 * 停止插件响应
 */
export interface StopPluginResponse {
  /** 插件 ID */
  plugin_id: string;
  /** 插件状态：INACTIVE */
  status: string;
}

// ==================== API 函数 ====================

const CONSOLE_BASE = "/ai/console/v1/plugins/installations";

/**
 * 配置插件
 *
 * 保存插件的能力配置和运行时配置
 */
export async function configPlugin(
  pluginId: string,
  data: ConfigPluginRequest,
): Promise<ApiResponse<ConfigPluginResponse>> {
  return rawPost(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/config`, data);
}

/**
 * 测试插件配置连接
 *
 * 使用已保存的配置测试插件是否能正常连接
 */
export async function testPlugin(
  pluginId: string,
): Promise<ApiResponse<TestPluginResponse>> {
  return rawPost(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/test`);
}

/**
 * 启动插件
 *
 * 启动状态为 INACTIVE 的插件，创建插件进程并更新状态为 ACTIVE
 */
export async function startPlugin(
  pluginId: string,
): Promise<ApiResponse<StartPluginResponse>> {
  return rawPost(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/start`);
}

/**
 * 停止插件
 *
 * 停止状态为 ACTIVE 的插件，终止插件进程并更新状态为 INACTIVE
 */
export async function stopPlugin(
  pluginId: string,
): Promise<ApiResponse<StopPluginResponse>> {
  return rawPost(`${CONSOLE_BASE}/${encodeURIComponent(pluginId)}/stop`);
}
