/**
 * Tenant 模块类型定义
 */

// 从 framework 导入统一类型
import type { ApiResponse } from "@/framework/api/types";
import type { BasePaginatedQuery } from "@/framework/types";

// 重新导出统一类型
export type { ApiResponse, BasePaginatedQuery };

// 导出管理员类型
export type {
  AdminLoginRequest,
  AdminLoginResponse,
  AdminInfo,
} from "./admin";

// 导出资源类型
export type {
  ResourceConfig,
  DatabaseConfig,
  StorageConfig,
  CacheConfig,
  QueueConfig,
  PubsubConfig,
  ConnectionTestResult,
  ResourcePaginatedQuery,
  ResourceCreate,
  ResourceUpdate,
} from "./resource";

// 导出模块管理类型
export type {
  ModuleStatus,
  Module,
  ModuleMenu,
  ModulePermission,
  ModuleRole,
  ModulePaginatedQuery,
  ModuleMenuListResponse,
  TenantModule,
  TenantResource,
  ModuleCreate,
  ModuleUpdate,
  MenuCreate,
  MenuUpdate,
  PermissionCreate,
  PermissionUpdate,
  RoleCreate,
  RoleUpdate,
  AssignModuleParams,
} from "./admin";

// 导出插件市场类型
export type {
  Marketplace,
  MarketplaceCreate,
  MarketplaceUpdate,
  MarketplaceTestResult,
  RemotePlugin,
  SyncPluginsRequest,
  SyncResult,
} from "./marketplace";

// 资源配置引用
export interface ResourceConfigReference {
  id: string;
  name: string;
}

// 租户实体
export interface Tenant {
  id: string;
  name: string;
  code: string;
  status: "active" | "inactive";
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  expired_at?: string;
  settings?: Record<string, any>;
  // 资源配置关联
  db_config?: ResourceConfigReference | null;
  storage_config?: ResourceConfigReference | null;
  cache_config?: ResourceConfigReference | null;
  queue_config?: ResourceConfigReference | null;
  pubsub_config?: ResourceConfigReference | null;
  created_at: string;
  updated_at?: string;
}

// 租户统计（单个租户详情）
export interface TenantStatsResponse {
  tenant_id: string;
  user_count: number;
  storage_usage: number;
  active_users: number;
}

// 租户列表统计
export interface TenantListStats {
  total_count: number;
  inactive_count: number;
  expired_count: number;
}

// 租户列表项（包含分页和统计）
export interface TenantListData {
  items: Tenant[];
  total: number;
  stats: TenantListStats;
}

// 带统计的租户列表响应（继承自 ApiResponse）
export interface TenantListResponse extends ApiResponse<TenantListData> {}

// 用户租户信息
export interface UserTenantResponse {
  tenant_id: string;
  tenant_name: string;
  tenant_code: string;
  role_ids: string[];
  role_names: string[];
  department_id?: string;
  department_name?: string;
  is_current: boolean;
}

// 切换租户响应
export interface SwitchTenantResponse {
  tenant_id: string;
  tenant_name: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

// 租户查询参数
export interface TenantPaginatedQuery extends BasePaginatedQuery {
  status?: string;
}

// 创建租户参数
export interface TenantCreate {
  name: string;
  code: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  expired_at?: string;
  settings?: Record<string, any>;
  // 资源配置关联
  db_config_id?: string;
  storage_config_id?: string;
  cache_config_id?: string;
  queue_config_id?: string;
  pubsub_config_id?: string;
}

// 更新租户参数
export interface TenantUpdate {
  name?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  expired_at?: string;
  settings?: Record<string, any>;
  status?: "active" | "inactive";
  // 资源配置关联
  db_config_id?: string;
  storage_config_id?: string;
  cache_config_id?: string;
  queue_config_id?: string;
  pubsub_config_id?: string;
}
