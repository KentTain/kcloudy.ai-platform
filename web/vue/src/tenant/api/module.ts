import { rawDel, rawGet, rawPost, rawPut } from "@/framework/api/client";
import type {
  ApiResponse,
  CreateMenuParams,
  CreateModuleParams,
  CreatePermissionParams,
  CreateRoleParams,
  Module,
  ModuleMenu,
  ModulePermission,
  ModuleQueryParams,
  ModuleRole,
  PageResult,
  UpdateMenuParams,
  UpdateModuleParams,
  UpdatePermissionParams,
  UpdateRoleParams,
} from "@/tenant/types";

// ==================== 模块管理 ====================

/**
 * 获取模块列表
 */
export const getModules = (params?: ModuleQueryParams) =>
  rawGet<ApiResponse<PageResult<Module>>>("/admin/v1/modules", { params });

/**
 * 获取模块详情
 */
export const getModule = (id: string) => rawGet<ApiResponse<Module>>(`/admin/v1/modules/${id}`);

/**
 * 创建模块
 */
export const createModule = (data: CreateModuleParams) =>
  rawPost<ApiResponse<Module>>("/admin/v1/modules", data);

/**
 * 更新模块
 */
export const updateModule = (id: string, data: UpdateModuleParams) =>
  rawPut<ApiResponse<Module>>(`/admin/v1/modules/${id}`, data);

/**
 * 删除模块
 */
export const deleteModule = (id: string) => rawDel<ApiResponse<void>>(`/admin/v1/modules/${id}`);

// ==================== 模块菜单 ====================

/**
 * 获取模块菜单树
 */
export const getModuleMenus = (moduleId: string) =>
  rawGet<ApiResponse<ModuleMenu[]>>(`/admin/v1/modules/${moduleId}/menus`);

/**
 * 创建模块菜单
 */
export const createModuleMenu = (moduleId: string, data: CreateMenuParams) =>
  rawPost<ApiResponse<ModuleMenu>>(`/admin/v1/modules/${moduleId}/menus`, data);

/**
 * 更新模块菜单
 */
export const updateModuleMenu = (moduleId: string, menuId: string, data: UpdateMenuParams) =>
  rawPut<ApiResponse<ModuleMenu>>(`/admin/v1/modules/${moduleId}/menus/${menuId}`, data);

/**
 * 删除模块菜单
 */
export const deleteModuleMenu = (moduleId: string, menuId: string) =>
  rawDel<ApiResponse<void>>(`/admin/v1/modules/${moduleId}/menus/${menuId}`);

// ==================== 模块权限 ====================

/**
 * 获取模块权限列表
 */
export const getModulePermissions = (moduleId: string) =>
  rawGet<ApiResponse<ModulePermission[]>>(`/admin/v1/modules/${moduleId}/permissions`);

/**
 * 创建模块权限
 */
export const createModulePermission = (moduleId: string, data: CreatePermissionParams) =>
  rawPost<ApiResponse<ModulePermission>>(`/admin/v1/modules/${moduleId}/permissions`, data);

/**
 * 更新模块权限
 */
export const updateModulePermission = (
  moduleId: string,
  permissionId: string,
  data: UpdatePermissionParams
) =>
  rawPut<ApiResponse<ModulePermission>>(
    `/admin/v1/modules/${moduleId}/permissions/${permissionId}`,
    data
  );

/**
 * 删除模块权限
 */
export const deleteModulePermission = (moduleId: string, permissionId: string) =>
  rawDel<ApiResponse<void>>(`/admin/v1/modules/${moduleId}/permissions/${permissionId}`);

// ==================== 模块角色 ====================

/**
 * 获取模块角色列表
 */
export const getModuleRoles = (moduleId: string) =>
  rawGet<ApiResponse<ModuleRole[]>>(`/admin/v1/modules/${moduleId}/roles`);

/**
 * 获取模块角色详情
 */
export const getModuleRole = (moduleId: string, roleId: string) =>
  rawGet<ApiResponse<ModuleRole>>(`/admin/v1/modules/${moduleId}/roles/${roleId}`);

/**
 * 创建模块角色
 */
export const createModuleRole = (moduleId: string, data: CreateRoleParams) =>
  rawPost<ApiResponse<ModuleRole>>(`/admin/v1/modules/${moduleId}/roles`, data);

/**
 * 更新模块角色
 */
export const updateModuleRole = (moduleId: string, roleId: string, data: UpdateRoleParams) =>
  rawPut<ApiResponse<ModuleRole>>(`/admin/v1/modules/${moduleId}/roles/${roleId}`, data);

/**
 * 删除模块角色
 */
export const deleteModuleRole = (moduleId: string, roleId: string) =>
  rawDel<ApiResponse<void>>(`/admin/v1/modules/${moduleId}/roles/${roleId}`);

/**
 * 更新角色权限
 */
export const updateRolePermissions = (moduleId: string, roleId: string, permissionIds: string[]) =>
  rawPut<ApiResponse<void>>(`/admin/v1/modules/${moduleId}/roles/${roleId}/permissions`, {
    permission_ids: permissionIds,
  });
