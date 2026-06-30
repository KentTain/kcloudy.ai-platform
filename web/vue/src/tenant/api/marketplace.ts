import { rawDel, rawGet, rawPost, rawPut } from '@/framework/api/client';
import type { ApiResponse } from '@/framework/api/types';
import type {
  ApplyUpdateResult,
  Marketplace,
  MarketplaceCreate,
  MarketplaceTestResult,
  MarketplaceUpdate,
  PluginUpdateInfo,
  RemotePlugin,
  SyncPluginsRequest,
  SyncResultResponse,
} from '@/tenant/types/marketplace';

// ==================== 市场配置管理 ====================

export const getMarketplaces = () =>
  rawGet<ApiResponse<Marketplace[]>>('/tenant/admin/v1/marketplaces');

export const getMarketplace = (id: string) =>
  rawGet<ApiResponse<Marketplace>>(`/tenant/admin/v1/marketplaces/${id}`);

export const createMarketplace = (data: MarketplaceCreate) =>
  rawPost<ApiResponse<Marketplace>>('/tenant/admin/v1/marketplaces', data);

export const updateMarketplace = (id: string, data: MarketplaceUpdate) =>
  rawPut<ApiResponse<Marketplace>>(`/tenant/admin/v1/marketplaces/${id}`, data);

export const deleteMarketplace = (id: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/marketplaces/${id}`);

// ==================== 连接测试 ====================

export const testMarketplace = (id: string) =>
  rawPost<ApiResponse<MarketplaceTestResult>>(`/tenant/admin/v1/marketplaces/${id}/test`);

// ==================== 远程插件浏览 ====================

export const getRemotePlugins = (
  marketplaceId: string,
  params?: { page?: number; page_size?: number; keyword?: string; type?: string }
) =>
  rawGet<ApiResponse<RemotePlugin[]>>(`/tenant/admin/v1/marketplaces/${marketplaceId}/plugins`, { params });

// ==================== 同步 ====================

export const syncPlugins = (data: SyncPluginsRequest) =>
  rawPost<ApiResponse<SyncResultResponse>>('/tenant/admin/v1/marketplaces/sync', data);

// ==================== 更新 ====================

export const checkUpdates = (marketplaceId: string) =>
  rawGet<ApiResponse<PluginUpdateInfo[]>>('/tenant/admin/v1/marketplaces/updates', {
    params: { marketplace_id: marketplaceId },
  });

export const applyPluginUpdate = (pluginId: string, marketplaceId: string) =>
  rawPost<ApiResponse<ApplyUpdateResult>>(`/tenant/admin/v1/marketplaces/updates/${pluginId}`, {
    marketplace_id: marketplaceId,
  });
