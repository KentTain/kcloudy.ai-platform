import { rawDel, rawGet, rawPost, rawPut } from "@/framework/api/client";
import type { ApiResponse, AssignModuleParams, TenantModule, TenantResource } from "@/tenant/types";

// ==================== 租户模块分配 ====================

/**
 * 获取租户已分配的模块列表
 */
export const getTenantModules = (tenantId: string) =>
  rawGet<ApiResponse<TenantModule[]>>(`/tenant/admin/v1/tenants/${tenantId}/modules`);

/**
 * 为租户分配模块
 */
export const assignModuleToTenant = (tenantId: string, data: AssignModuleParams) =>
  rawPost<ApiResponse<TenantModule>>(`/tenant/admin/v1/tenants/${tenantId}/modules`, data);

/**
 * 取消租户模块分配
 */
export const unassignModuleFromTenant = (tenantId: string, moduleId: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/tenants/${tenantId}/modules/${moduleId}`);

// ==================== 租户资源绑定 ====================

/**
 * 获取租户资源绑定
 */
export const getTenantResources = (tenantId: string) =>
  rawGet<ApiResponse<TenantResource>>(`/tenant/admin/v1/tenants/${tenantId}/resources`);

/**
 * 更新租户资源绑定
 */
export const updateTenantResources = (tenantId: string, data: Partial<TenantResource>) =>
  rawPut<ApiResponse<void>>(`/tenant/admin/v1/tenants/${tenantId}/resources`, data);
