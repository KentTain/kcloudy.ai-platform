import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse, Department, DepartmentUser } from "../types";
import type { DepartmentQuery } from "../types";

export interface DepartmentCreate {
  name: string;
  code?: string;
  parent_id?: string;
  sort_order?: number;
  leader_id?: string;
}

export interface DepartmentUpdate {
  name?: string;
  code?: string;
  sort_order?: number;
  leader_id?: string;
  status?: string;
}

/**
 * 获取部门列表
 */
export const getDepartments = (params?: DepartmentQuery) =>
  get<ApiResponse<Department[]>>("/iam/admin/v1/departments", { params });

/**
 * 获取部门树形结构
 */
export const getDepartmentTree = () =>
  get<ApiResponse<Department[]>>("/iam/admin/v1/departments/tree");

/**
 * 获取部门详情
 */
export const getDepartment = (id: string) =>
  get<ApiResponse<Department>>(`/iam/admin/v1/departments/${id}`);

/**
 * 创建部门
 */
export const createDepartment = (data: DepartmentCreate) =>
  post<ApiResponse<Department>>("/iam/admin/v1/departments", data);

/**
 * 更新部门
 */
export const updateDepartment = (id: string, data: DepartmentUpdate) =>
  put<ApiResponse<Department>>(`/iam/admin/v1/departments/${id}`, data);

/**
 * 删除部门
 */
export const deleteDepartment = (id: string) =>
  del<ApiResponse<void>>(`/iam/admin/v1/departments/${id}`);

/**
 * 设置部门负责人
 */
export const setDepartmentLeader = (id: string, leader_id: string) =>
  updateDepartment(id, { leader_id });

/**
 * 获取部门用户
 */
export const getDepartmentUsers = (id: string) =>
  get<ApiResponse<DepartmentUser[]>>(`/iam/admin/v1/departments/${id}/users`);

export const addDepartmentUser = (department_id: string, user_id: string, is_leader = false) =>
  post<ApiResponse<DepartmentUser>>(`/iam/admin/v1/departments/${department_id}/users`, {
    user_id,
    is_leader,
  });

export const removeDepartmentUser = (department_id: string, user_id: string) =>
  del<ApiResponse<void>>(`/iam/admin/v1/departments/${department_id}/users/${user_id}`);
