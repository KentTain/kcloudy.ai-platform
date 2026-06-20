import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { User, Role, Organization, RoleOption, UserStats, UserPaginatedQuery } from "@/iam/types";

export interface UserCreate {
  username: string;
  password: string;
  email?: string;
  phone?: string;
  nickname?: string;
}

export interface UserUpdate {
  nickname?: string;
  avatar?: string;
  email?: string;
  phone?: string;
}

/**
 * 获取用户列表
 */
export const getUsers = (params?: UserPaginatedQuery) =>
  get<ApiResponse<User[]>>("/iam/admin/v1/users", { params });

/**
 * 获取用户详情
 */
export const getUser = (id: string) =>
  get<ApiResponse<User>>(`/iam/admin/v1/users/${id}`);

/**
 * 创建用户
 */
export const createUser = (data: UserCreate) =>
  post<ApiResponse<User>>("/iam/admin/v1/users", data);

/**
 * 更新用户
 */
export const updateUser = (id: string, data: UserUpdate) =>
  put<ApiResponse<User>>(`/iam/admin/v1/users/${id}`, data);

/**
 * 删除用户
 */
export const deleteUser = (id: string) =>
  del<ApiResponse<void>>(`/iam/admin/v1/users/${id}`);

/**
 * 停用用户
 */
export const disableUser = (id: string) =>
  post<ApiResponse<void>>(`/iam/admin/v1/users/${id}/disable`);

/**
 * 激活用户
 */
export const enableUser = (id: string) =>
  post<ApiResponse<void>>(`/iam/admin/v1/users/${id}/enable`);

/**
 * 锁定用户
 */
export const lockUser = (id: string) =>
  post<ApiResponse<void>>(`/iam/admin/v1/users/${id}/lock`);

/**
 * 分配角色
 */
export const assignUserRoles = (user_id: string, role_ids: string[]) =>
  post<ApiResponse<void>>(`/iam/admin/v1/users/${user_id}/roles`, { role_ids });

/**
 * 分配组织
 */
export const assignUserOrganizations = (user_id: string, organization_ids: string[]) =>
  post<ApiResponse<void>>(`/iam/admin/v1/users/${user_id}/organizations`, { organization_ids });

/**
 * 获取用户角色
 */
export const getUserRoles = (user_id: string) =>
  get<ApiResponse<Role[]>>(`/iam/admin/v1/users/${user_id}/roles`);

/**
 * 获取用户组织
 */
export const getUserOrganizations = (user_id: string) =>
  get<ApiResponse<Organization[]>>(`/iam/admin/v1/users/${user_id}/organizations`);

export const resetUserPassword = (id: string, data: { new_password?: string } = {}) =>
  post<ApiResponse<{ password: string }>>(`/iam/admin/v1/users/${id}/reset-password`, data);

export const updateUserStatus = (id: string, status: User["status"]) =>
  put<ApiResponse<User>>(`/iam/admin/v1/users/${id}/status`, { status });

/**
 * 获取用户统计
 */
export const getUserStats = () =>
  get<ApiResponse<UserStats>>("/iam/admin/v1/users/stats");

/**
 * 获取角色选项列表（不分页，供下拉选择用）
 */
export const getRoleOptions = () =>
  get<ApiResponse<RoleOption[]>>("/iam/admin/v1/roles/options");
