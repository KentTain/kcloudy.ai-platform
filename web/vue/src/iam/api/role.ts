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
  get<ApiResponse<PageResult<Role>>>("/v1/iam/role", { params });

/**
 * 获取角色详情（含权限）
 */
export const getRole = (id: string) =>
  get<ApiResponse<Role>>(`/v1/iam/role/${id}`);

/**
 * 创建角色
 */
export const createRole = (data: CreateRoleParams) =>
  post<ApiResponse<Role>>("/v1/iam/role", data);

/**
 * 更新角色
 */
export const updateRole = (id: string, data: UpdateRoleParams) =>
  put<ApiResponse<Role>>(`/v1/iam/role/${id}`, data);

/**
 * 删除角色
 */
export const deleteRole = (id: string) =>
  del<ApiResponse<void>>(`/v1/iam/role/${id}`);

/**
 * 为角色分配权限
 */
export const assignRolePermissions = (role_id: string, data: AssignPermissionsParams) =>
  post<ApiResponse<void>>(`/v1/iam/role/${role_id}/permissions`, data);

/**
 * 获取角色权限
 */
export const getRolePermissions = (role_id: string) =>
  get<ApiResponse<Permission[]>>(`/v1/iam/role/${role_id}/permissions`);
