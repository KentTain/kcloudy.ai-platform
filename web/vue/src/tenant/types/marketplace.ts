/** 插件市场类型定义 */

// ==================== 市场配置 ====================

export interface Marketplace {
  id: string;
  name: string;
  code: string;
  type: string;
  url: string;
  auth_type: string;
  is_enabled: boolean;
  last_sync_at?: string;
  last_sync_status?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MarketplaceCreate {
  name: string;
  code: string;
  type: string;
  url: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  description?: string;
}

export interface MarketplaceUpdate {
  name?: string;
  url?: string;
  auth_type?: string;
  auth_config?: Record<string, unknown>;
  is_enabled?: boolean;
  sync_config?: Record<string, unknown>;
  description?: string;
}

export interface MarketplaceTestResult {
  success: boolean;
  message: string;
  plugin_count?: number;
  latency_ms?: number;
}

// ==================== 远程插件 ====================

export interface RemotePlugin {
  plugin_id: string;
  name: string;
  description?: string;
  version: string;
  author: string;
  icon?: string;
  plugin_type: string;
  tags: string[];
  downloads?: number;
  download_url: string;
}

// ==================== 同步 ====================

export interface SyncPluginItem {
  plugin_id: string;
  plugin_type: string;
}

export interface SyncPluginsRequest {
  marketplace_id: string;
  plugins: SyncPluginItem[];
}

export interface SyncSuccessItem {
  plugin_id: string;
  version: string;
}

export interface SyncFailedItem {
  plugin_id: string;
  message: string;
}

export interface SyncSkippedItem {
  plugin_id: string;
  reason: string;
}

export interface SyncResultResponse {
  success: SyncSuccessItem[];
  failed: SyncFailedItem[];
  skipped: SyncSkippedItem[];
}

// ==================== 更新 ====================

export interface PluginUpdateInfo {
  plugin_id: string;
  current_version: string;
  latest_version: string;
  has_update: boolean;
}

export interface ApplyUpdateResult {
  plugin_id: string;
  old_version: string;
  new_version: string;
  status: string;
}
