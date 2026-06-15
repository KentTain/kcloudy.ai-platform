import { rawDel, rawGet, rawPost, rawPut } from "@/framework/api/client";
import type {
  ApiResponse,
  CreateTenantParams,
  PageResult,
  SwitchTenantVo,
  Tenant,
  TenantQueryParams,
  TenantStatsVo,
  UpdateTenantParams,
  UserTenantVo,
} from "../types";

/**
 * 获取租户列表（管理员）
 */
export const getTenants = (params?: TenantQueryParams) =>
  rawGet<ApiResponse<PageResult<Tenant>>>("/tenant/admin/v1/tenants", { params });

/**
 * 获取租户详情（管理员）
 */
export const getTenant = (id: string) => rawGet<ApiResponse<Tenant>>(`/tenant/admin/v1/tenants/${id}`);

/**
 * 创建租户（管理员）
 */
export const createTenant = (data: CreateTenantParams) =>
  rawPost<ApiResponse<Tenant>>("/tenant/admin/v1/tenants", data);

/**
 * 更新租户（管理员）
 */
export const updateTenant = (id: string, data: UpdateTenantParams) =>
  rawPut<ApiResponse<Tenant>>(`/tenant/admin/v1/tenants/${id}`, data);

/**
 * 删除租户（管理员）
 */
export const deleteTenant = (id: string) => rawDel<ApiResponse<void>>(`/tenant/admin/v1/tenants/${id}`);

/**
 * 激活租户
 */
export const activateTenant = (id: string) =>
  rawPost<ApiResponse<Tenant>>(`/tenant/admin/v1/tenants/${id}/activate`);

/**
 * 停用租户
 */
export const deactivateTenant = (id: string) =>
  rawPost<ApiResponse<Tenant>>(`/tenant/admin/v1/tenants/${id}/deactivate`);

/**
 * 获取租户统计
 */
export const getTenantStats = (id: string) =>
  rawGet<ApiResponse<TenantStatsVo>>(`/tenant/admin/v1/tenants/${id}/stats`);

/**
 * 获取当前租户（控制台）
 */
export const getCurrentTenant = () => rawGet<ApiResponse<Tenant>>("/tenant/console/v1/tenants/current");

/**
 * 获取用户可切换的租户列表
 */
export const getMyTenants = () => rawGet<ApiResponse<UserTenantVo[]>>("/tenant/console/v1/tenants");

/**
 * 切换当前租户
 */
export const switchTenant = (tenant_id: string) =>
  rawPost<ApiResponse<SwitchTenantVo>>(`/tenant/console/v1/tenants/${tenant_id}/switch`);
