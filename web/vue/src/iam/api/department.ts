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
  get<ApiResponse<Department[]>>("/v1/iam/department", { params });

/**
 * 获取部门树形结构
 */
export const getDepartmentTree = () =>
  get<ApiResponse<Department[]>>("/v1/iam/department/tree");

/**
 * 获取部门详情
 */
export const getDepartment = (id: string) =>
  get<ApiResponse<Department>>(`/v1/iam/department/${id}`);

/**
 * 创建部门
 */
export const createDepartment = (data: CreateDepartmentParams) =>
  post<ApiResponse<Department>>("/v1/iam/department", data);

/**
 * 更新部门
 */
export const updateDepartment = (id: string, data: UpdateDepartmentParams) =>
  put<ApiResponse<Department>>(`/v1/iam/department/${id}`, data);

/**
 * 删除部门
 */
export const deleteDepartment = (id: string) =>
  del<ApiResponse<void>>(`/v1/iam/department/${id}`);

/**
 * 设置部门负责人
 */
export const setDepartmentLeader = (id: string, leader_id: string) =>
  updateDepartment(id, { leader_id });

/**
 * 获取部门用户
 */
export const getDepartmentUsers = (id: string) =>
  get<ApiResponse<DepartmentUser[]>>(`/v1/iam/department/${id}/users`);

export const addDepartmentUser = (department_id: string, user_id: string, is_leader = false) =>
  post<ApiResponse<DepartmentUser>>(`/v1/iam/department/${department_id}/users`, {
    user_id,
    is_leader,
  });

export const removeDepartmentUser = (department_id: string, user_id: string) =>
  del<ApiResponse<void>>(`/v1/iam/department/${department_id}/users/${user_id}`);
