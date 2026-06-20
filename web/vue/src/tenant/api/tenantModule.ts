import { rawDel, rawGet, rawPost, rawPut } from "@/framework/api/client";
import type { Success } from "@/framework/types";
import type { AssignModuleParams, TenantModule, TenantResource } from "@/tenant/types";

// ==================== 租户模块分配 ====================

/**
 * 获取租户已分配的模块列表
 */
export const getTenantModules = (tenantId: string) =>
  rawGet<Success<TenantModule[]>>(`/tenant/admin/v1/tenants/${tenantId}/modules`);

/**
 * 为租户分配模块
 */
export const assignModuleToTenant = (tenantId: string, data: AssignModuleParams) =>
  rawPost<Success<TenantModule>>(`/tenant/admin/v1/tenants/${tenantId}/modules`, data);

/**
 * 取消租户模块分配
 */
export const unassignModuleFromTenant = (tenantId: string, moduleId: string) =>
  rawDel<Success<void>>(`/tenant/admin/v1/tenants/${tenantId}/modules/${moduleId}`);

// ==================== 租户资源绑定 ====================

/**
 * 获取租户资源绑定
 */
export const getTenantResources = (tenantId: string) =>
  rawGet<Success<TenantResource>>(`/tenant/admin/v1/tenants/${tenantId}/resources`);

/**
 * 更新租户资源绑定
 */
export const updateTenantResources = (tenantId: string, data: Partial<TenantResource>) =>
  rawPut<Success<void>>(`/tenant/admin/v1/tenants/${tenantId}/resources`, data);
