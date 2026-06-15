import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse, Department, DepartmentUser } from "../types";

export interface DepartmentQueryParams {
  keyword?: string;
  status?: string;
}

export interface CreateDepartmentParams {
  name: string;
  code?: string;
  parent_id?: string;
  sort_order?: number;
  leader_id?: string;
}

export interface UpdateDepartmentParams {
  name?: string;
  code?: string;
  sort_order?: number;
  leader_id?: string;
  status?: string;
}

/**
 * 获取部门列表
 */
export const getDepartments = (params?: DepartmentQueryParams) =>
  get<ApiResponse<Department[]>>("/admin/v1/iam/departments", { params });

/**
 * 获取部门树形结构
 */
export const getDepartmentTree = () =>
  get<ApiResponse<Department[]>>("/admin/v1/iam/departments/tree");

/**
 * 获取部门详情
 */
export const getDepartment = (id: string) =>
  get<ApiResponse<Department>>(`/admin/v1/iam/departments/${id}`);

/**
 * 创建部门
 */
export const createDepartment = (data: CreateDepartmentParams) =>
  post<ApiResponse<Department>>("/admin/v1/iam/departments", data);

/**
 * 更新部门
 */
export const updateDepartment = (id: string, data: UpdateDepartmentParams) =>
  put<ApiResponse<Department>>(`/admin/v1/iam/departments/${id}`, data);

/**
 * 删除部门
 */
export const deleteDepartment = (id: string) =>
  del<ApiResponse<void>>(`/admin/v1/iam/departments/${id}`);

/**
 * 设置部门负责人
 */
export const setDepartmentLeader = (id: string, leader_id: string) =>
  updateDepartment(id, { leader_id });

/**
 * 获取部门用户
 */
export const getDepartmentUsers = (id: string) =>
  get<ApiResponse<DepartmentUser[]>>(`/admin/v1/iam/departments/${id}/users`);

export const addDepartmentUser = (department_id: string, user_id: string, is_leader = false) =>
  post<ApiResponse<DepartmentUser>>(`/admin/v1/iam/departments/${department_id}/users`, {
    user_id,
    is_leader,
  });

export const removeDepartmentUser = (department_id: string, user_id: string) =>
  del<ApiResponse<void>>(`/admin/v1/iam/departments/${department_id}/users/${user_id}`);
