import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse, PageResult, User, Role, Department } from "../types";

export interface UserQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  status?: string;
  department_id?: string;
  role_id?: string;
}

export interface CreateUserParams {
  username: string;
  password: string;
  email?: string;
  phone?: string;
  nickname?: string;
}

export interface UpdateUserParams {
  nickname?: string;
  avatar?: string;
  email?: string;
  phone?: string;
}

/**
 * 获取用户列表
 */
export const getUsers = (params?: UserQueryParams) =>
  get<ApiResponse<PageResult<User>>>("/v1/iam/user", { params });

/**
 * 获取用户详情
 */
export const getUser = (id: string) =>
  get<ApiResponse<User>>(`/v1/iam/user/${id}`);

/**
 * 创建用户
 */
export const createUser = (data: CreateUserParams) =>
  post<ApiResponse<User>>("/v1/iam/user", data);

/**
 * 更新用户
 */
export const updateUser = (id: string, data: UpdateUserParams) =>
  put<ApiResponse<User>>(`/v1/iam/user/${id}`, data);

/**
 * 删除用户
 */
export const deleteUser = (id: string) =>
  del<ApiResponse<void>>(`/v1/iam/user/${id}`);

/**
 * 停用用户
 */
export const disableUser = (id: string) =>
  post<ApiResponse<void>>(`/v1/iam/user/${id}/disable`);

/**
 * 激活用户
 */
export const enableUser = (id: string) =>
  post<ApiResponse<void>>(`/v1/iam/user/${id}/enable`);

/**
 * 锁定用户
 */
export const lockUser = (id: string) =>
  post<ApiResponse<void>>(`/v1/iam/user/${id}/lock`);

/**
 * 分配角色
 */
export const assignUserRoles = (user_id: string, role_ids: string[]) =>
  post<ApiResponse<void>>(`/v1/iam/user/${user_id}/roles`, { role_ids });

/**
 * 分配部门
 */
export const assignUserDepartments = (user_id: string, department_ids: string[]) =>
  post<ApiResponse<void>>(`/v1/iam/user/${user_id}/departments`, { department_ids });

/**
 * 获取用户角色
 */
export const getUserRoles = (user_id: string) =>
  get<ApiResponse<Role[]>>(`/v1/iam/user/${user_id}/roles`);

/**
 * 获取用户部门
 */
export const getUserDepartments = (user_id: string) =>
  get<ApiResponse<Department[]>>(`/v1/iam/user/${user_id}/departments`);

export const resetUserPassword = (id: string, data: { new_password?: string } = {}) =>
  post<ApiResponse<{ password: string }>>(`/v1/iam/user/${id}/reset-password`, data);

export const updateUserStatus = (id: string, status: User["status"]) =>
  put<ApiResponse<User>>(`/v1/iam/user/${id}/status`, { status });
