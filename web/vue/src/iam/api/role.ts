import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse, PaginatedListResponse, Permission, Role } from "../types";
import type { RolePaginatedQuery } from "../types";

export interface RoleCreate {
  code: string;
  name: string;
  description?: string;
}

export interface RoleUpdate {
  name?: string;
  description?: string;
}

export interface AssignPermissionsParams {
  permission_ids: string[];
}

/**
 * 获取角色列表
 */
export const getRoles = (params?: RolePaginatedQuery) =>
  get<ApiResponse<PaginatedListResponse<Role>>>("/iam/admin/v1/roles", { params });

/**
 * 获取角色详情（含权限）
 */
export const getRole = (id: string) =>
  get<ApiResponse<Role>>(`/iam/admin/v1/roles/${id}`);

/**
 * 创建角色
 */
export const createRole = (data: RoleCreate) =>
  post<ApiResponse<Role>>("/iam/admin/v1/roles", data);

/**
 * 更新角色
 */
export const updateRole = (id: string, data: RoleUpdate) =>
  put<ApiResponse<Role>>(`/iam/admin/v1/roles/${id}`, data);

/**
 * 删除角色
 */
export const deleteRole = (id: string) =>
  del<ApiResponse<void>>(`/iam/admin/v1/roles/${id}`);

/**
 * 为角色分配权限
 */
export const assignRolePermissions = (role_id: string, data: AssignPermissionsParams) =>
  post<ApiResponse<void>>(`/iam/admin/v1/roles/${role_id}/permissions`, data);

/**
 * 获取角色权限
 */
export const getRolePermissions = (role_id: string) =>
  get<ApiResponse<Permission[]>>(`/iam/admin/v1/roles/${role_id}/permissions`);

/**
 * 获取角色成员列表
 */
export const getRoleMembers = (role_id: string) =>
  get<ApiResponse<{ user_id: string; username: string; nickname?: string; email?: string; phone?: string; status: string }[]>>(`/iam/admin/v1/roles/${role_id}/members`);

/**
 * 为角色添加成员
 */
export const addRoleMembers = (role_id: string, user_ids: string[]) =>
  post<ApiResponse<{ added: number }>>(`/iam/admin/v1/roles/${role_id}/members`, { user_ids });

/**
 * 移除角色成员
 */
export const removeRoleMember = (role_id: string, user_id: string) =>
  del<ApiResponse<void>>(`/iam/admin/v1/roles/${role_id}/members/${user_id}`);

/**
 * 获取角色菜单
 */
export const getRoleMenus = (role_id: string) =>
  get<ApiResponse<string[]>>(`/iam/admin/v1/roles/${role_id}/menus`);

/**
 * 为角色分配菜单
 */
export const assignRoleMenus = (role_id: string, menu_ids: string[]) =>
  post<ApiResponse<void>>(`/iam/admin/v1/roles/${role_id}/menus`, { menu_ids });
