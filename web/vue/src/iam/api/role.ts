import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse, PageResult, Permission, Role } from "../types";

export interface RoleQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  include_system?: boolean;
}

export interface CreateRoleParams {
  code: string;
  name: string;
  description?: string;
}

export interface UpdateRoleParams {
  name?: string;
  description?: string;
}

export interface AssignPermissionsParams {
  permission_ids: string[];
}

/**
 * 获取角色列表
 */
export const getRoles = (params?: RoleQueryParams) =>
  get<ApiResponse<PageResult<Role>>>("/iam/admin/v1/roles", { params });

/**
 * 获取角色详情（含权限）
 */
export const getRole = (id: string) =>
  get<ApiResponse<Role>>(`/iam/admin/v1/roles/${id}`);

/**
 * 创建角色
 */
export const createRole = (data: CreateRoleParams) =>
  post<ApiResponse<Role>>("/iam/admin/v1/roles", data);

/**
 * 更新角色
 */
export const updateRole = (id: string, data: UpdateRoleParams) =>
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
