import { rawDel, rawGet, rawPost, rawPut } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type {
  MenuCreate,
  ModuleCreate,
  PermissionCreate,
  RoleCreate,
  Module,
  ModuleMenu,
  ModuleMenuListResponse,
  ModulePermission,
  ModulePaginatedQuery,
  ModuleRole,
  MenuUpdate,
  ModuleUpdate,
  PermissionUpdate,
  RoleUpdate,
} from "@/tenant/types";

// ==================== 模块管理 ====================

/**
 * 获取模块列表
 */
export const getModules = (params?: ModulePaginatedQuery) =>
  rawGet<ApiResponse<Module[]>>("/tenant/admin/v1/modules", { params });

/**
 * 获取模块详情
 */
export const getModule = (id: string) => rawGet<ApiResponse<Module>>(`/tenant/admin/v1/modules/${id}`);

/**
 * 创建模块
 */
export const createModule = (data: ModuleCreate) =>
  rawPost<ApiResponse<Module>>("/tenant/admin/v1/modules", data);

/**
 * 更新模块
 */
export const updateModule = (id: string, data: ModuleUpdate) =>
  rawPut<ApiResponse<Module>>(`/tenant/admin/v1/modules/${id}`, data);

/**
 * 删除模块
 */
export const deleteModule = (id: string) => rawDel<ApiResponse<void>>(`/tenant/admin/v1/modules/${id}`);

// ==================== 模块菜单 ====================

/**
 * 获取模块菜单树
 */
export const getModuleMenus = (moduleId: string) =>
  rawGet<ApiResponse<ModuleMenuListResponse>>(`/tenant/admin/v1/modules/${moduleId}/menus`);

/**
 * 创建模块菜单
 */
export const createModuleMenu = (moduleId: string, data: MenuCreate) =>
  rawPost<ApiResponse<ModuleMenu>>(`/tenant/admin/v1/modules/${moduleId}/menus`, data);

/**
 * 更新模块菜单
 */
export const updateModuleMenu = (moduleId: string, menuId: string, data: MenuUpdate) =>
  rawPut<ApiResponse<ModuleMenu>>(`/tenant/admin/v1/modules/${moduleId}/menus/${menuId}`, data);

/**
 * 删除模块菜单
 */
export const deleteModuleMenu = (moduleId: string, menuId: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/modules/${moduleId}/menus/${menuId}`);

// ==================== 模块权限 ====================

/**
 * 获取模块权限列表
 */
export const getModulePermissions = (moduleId: string) =>
  rawGet<ApiResponse<ModulePermission[]>>(`/tenant/admin/v1/modules/${moduleId}/permissions`);

/**
 * 创建模块权限
 */
export const createModulePermission = (moduleId: string, data: PermissionCreate) =>
  rawPost<ApiResponse<ModulePermission>>(`/tenant/admin/v1/modules/${moduleId}/permissions`, data);

/**
 * 更新模块权限
 */
export const updateModulePermission = (
  moduleId: string,
  permissionId: string,
  data: PermissionUpdate
) =>
  rawPut<ApiResponse<ModulePermission>>(
    `/tenant/admin/v1/modules/${moduleId}/permissions/${permissionId}`,
    data
  );

/**
 * 删除模块权限
 */
export const deleteModulePermission = (moduleId: string, permissionId: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/modules/${moduleId}/permissions/${permissionId}`);

// ==================== 模块角色 ====================

/**
 * 获取模块角色列表
 */
export const getModuleRoles = (moduleId: string) =>
  rawGet<ApiResponse<ModuleRole[]>>(`/tenant/admin/v1/modules/${moduleId}/roles`);

/**
 * 获取模块角色详情
 */
export const getModuleRole = (moduleId: string, roleId: string) =>
  rawGet<ApiResponse<ModuleRole>>(`/tenant/admin/v1/modules/${moduleId}/roles/${roleId}`);

/**
 * 创建模块角色
 */
export const createModuleRole = (moduleId: string, data: RoleCreate) =>
  rawPost<ApiResponse<ModuleRole>>(`/tenant/admin/v1/modules/${moduleId}/roles`, data);

/**
 * 更新模块角色
 */
export const updateModuleRole = (moduleId: string, roleId: string, data: RoleUpdate) =>
  rawPut<ApiResponse<ModuleRole>>(`/tenant/admin/v1/modules/${moduleId}/roles/${roleId}`, data);

/**
 * 删除模块角色
 */
export const deleteModuleRole = (moduleId: string, roleId: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/modules/${moduleId}/roles/${roleId}`);

/**
 * 更新角色权限
 */
export const updateRolePermissions = (moduleId: string, roleId: string, permissionIds: string[]) =>
  rawPut<ApiResponse<void>>(`/tenant/admin/v1/modules/${moduleId}/roles/${roleId}/permissions`, {
    permission_ids: permissionIds,
  });
