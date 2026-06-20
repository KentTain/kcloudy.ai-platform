import { del, get, post, put } from "@/framework/api/client";
import type { Success, SuccessExtra } from "@/framework/types";
import type { Permission, Role, RolePaginatedQuery } from "@/iam/types";

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
  get<SuccessExtra<Role[]>>("/iam/admin/v1/roles", { params });

/**
 * 获取角色详情（含权限）
 */
export const getRole = (id: string) =>
  get<Success<Role>>(`/iam/admin/v1/roles/${id}`);

/**
 * 创建角色
 */
export const createRole = (data: RoleCreate) =>
  post<Success<Role>>("/iam/admin/v1/roles", data);

/**
 * 更新角色
 */
export const updateRole = (id: string, data: RoleUpdate) =>
  put<Success<Role>>(`/iam/admin/v1/roles/${id}`, data);

/**
 * 删除角色
 */
export const deleteRole = (id: string) =>
  del<Success<void>>(`/iam/admin/v1/roles/${id}`);

/**
 * 为角色分配权限
 */
export const assignRolePermissions = (role_id: string, data: AssignPermissionsParams) =>
  post<Success<void>>(`/iam/admin/v1/roles/${role_id}/permissions`, data);

/**
 * 获取角色权限
 */
export const getRolePermissions = (role_id: string) =>
  get<Success<Permission[]>>(`/iam/admin/v1/roles/${role_id}/permissions`);

/**
 * 获取角色成员列表
 */
export const getRoleMembers = (role_id: string) =>
  get<Success<{ user_id: string; username: string; nickname?: string; email?: string; phone?: string; status: string }[]>>(`/iam/admin/v1/roles/${role_id}/members`);

/**
 * 为角色添加成员
 */
export const addRoleMembers = (role_id: string, user_ids: string[]) =>
  post<Success<{ added: number }>>(`/iam/admin/v1/roles/${role_id}/members`, { user_ids });

/**
 * 移除角色成员
 */
export const removeRoleMember = (role_id: string, user_id: string) =>
  del<Success<void>>(`/iam/admin/v1/roles/${role_id}/members/${user_id}`);

/**
 * 获取角色菜单
 */
export const getRoleMenus = (role_id: string) =>
  get<Success<string[]>>(`/iam/admin/v1/roles/${role_id}/menus`);

/**
 * 为角色分配菜单
 */
export const assignRoleMenus = (role_id: string, menu_ids: string[]) =>
  post<Success<void>>(`/iam/admin/v1/roles/${role_id}/menus`, { menu_ids });
