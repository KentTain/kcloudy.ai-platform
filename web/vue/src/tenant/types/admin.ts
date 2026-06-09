/**
 * 管理员认证类型定义
 */

// 管理员登录请求
export interface AdminLoginRequest {
  username: string;
  password: string;
}

// 管理员登录响应
export interface AdminLoginResponse {
  token: string;
  username: string;
  is_default: boolean;
}

// 管理员信息
export interface AdminInfo {
  id: string;
  username: string;
  is_default: boolean;
  is_active: boolean;
}

/**
 * 模块管理类型定义
 */

import type {
  CacheConfig,
  DatabaseConfig,
  PubsubConfig,
  QueueConfig,
  StorageConfig,
} from "./resource";

// 模块状态
export type ModuleStatus = "active" | "inactive";

// 模块实体
export interface Module {
  id: string;
  name: string;
  code: string;
  description?: string;
  icon?: string;
  is_active: boolean;
  is_need: boolean; // 是否为必须模块
  tenant_count?: number; // 已分配的租户数量
  created_at: string;
  updated_at?: string;
}

// 模块菜单
export interface ModuleMenu {
  id: string;
  module_id: string;
  parent_id?: string;
  name: string;
  code: string;
  path: string;
  icon?: string;
  sort: number;
  children?: ModuleMenu[];
  created_at: string;
  updated_at?: string;
}

// 模块权限
export interface ModulePermission {
  id: string;
  module_id: string;
  name: string;
  code: string; // 格式: module:resource:action
  resource: string;
  action: "read" | "write" | "delete";
  description?: string;
  created_at: string;
  updated_at?: string;
}

// 模块角色
export interface ModuleRole {
  id: string;
  module_id: string;
  name: string;
  code: string;
  description?: string;
  is_system: boolean; // 是否为系统内置角色
  permission_ids: string[];
  created_at: string;
  updated_at?: string;
}

// 租户模块分配
export interface TenantModule {
  id: string;
  tenant_id: string;
  module_id: string;
  module?: Module;
  is_active: boolean;
  expired_at?: string;
  assigned_at: string;
}

// 租户资源绑定
export interface TenantResource {
  tenant_id: string;
  database_id?: string;
  storage_id?: string;
  cache_id?: string;
  queue_id?: string;
  pubsub_id?: string;
  database_config?: DatabaseConfig;
  storage_config?: StorageConfig;
  cache_config?: CacheConfig;
  queue_config?: QueueConfig;
  pubsub_config?: PubsubConfig;
}

// 模块查询参数
export interface ModuleQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  is_active?: boolean;
}

// 创建模块参数
export interface CreateModuleParams {
  name: string;
  code: string;
  description?: string;
  icon?: string;
  is_active?: boolean;
  is_need?: boolean;
}

// 更新模块参数
export interface UpdateModuleParams {
  name?: string;
  description?: string;
  icon?: string;
  is_active?: boolean;
}

// 创建菜单参数
export interface CreateMenuParams {
  parent_id?: string;
  name: string;
  code: string;
  path: string;
  icon?: string;
  sort?: number;
}

// 更新菜单参数
export interface UpdateMenuParams {
  parent_id?: string;
  name?: string;
  code?: string;
  path?: string;
  icon?: string;
  sort?: number;
}

// 创建权限参数
export interface CreatePermissionParams {
  name: string;
  code: string;
  resource: string;
  action: "read" | "write" | "delete";
  description?: string;
}

// 更新权限参数
export interface UpdatePermissionParams {
  name?: string;
  code?: string;
  resource?: string;
  action?: "read" | "write" | "delete";
  description?: string;
}

// 创建角色参数
export interface CreateRoleParams {
  name: string;
  code: string;
  description?: string;
  permission_ids?: string[];
}

// 更新角色参数
export interface UpdateRoleParams {
  name?: string;
  description?: string;
  permission_ids?: string[];
}

// 分配模块参数
export interface AssignModuleParams {
  module_id: string;
  expired_at?: string;
}
