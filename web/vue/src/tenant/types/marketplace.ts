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

export interface SyncPluginsRequest {
  marketplace_id: string;
  plugin_ids: string[];
}

export interface SyncResult {
  success: string[];
  failed: Array<{ plugin_id: string; message: string }>;
  skipped: string[];
}
