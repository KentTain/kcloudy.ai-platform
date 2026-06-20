import { del, get, post, put } from "@/framework/api/client";
import type { Success } from "@/framework/types";
import type { Department, DepartmentUser, DepartmentDetail, DepartmentQuery } from "@/iam/types";

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
  get<Success<Department[]>>("/iam/admin/v1/departments", { params });

/**
 * 获取部门树形结构
 */
export const getDepartmentTree = () =>
  get<Success<Department[]>>("/iam/admin/v1/departments/tree");

/**
 * 获取部门详情
 */
export const getDepartment = (id: string) =>
  get<Success<Department>>(`/iam/admin/v1/departments/${id}`);

/**
 * 创建部门
 */
export const createDepartment = (data: DepartmentCreate) =>
  post<Success<Department>>("/iam/admin/v1/departments", data);

/**
 * 更新部门
 */
export const updateDepartment = (id: string, data: DepartmentUpdate) =>
  put<Success<Department>>(`/iam/admin/v1/departments/${id}`, data);

/**
 * 删除部门
 */
export const deleteDepartment = (id: string) =>
  del<Success<void>>(`/iam/admin/v1/departments/${id}`);

/**
 * 设置部门负责人
 */
export const setDepartmentLeader = (id: string, leader_id: string) =>
  updateDepartment(id, { leader_id });

/**
 * 获取部门用户
 */
export const getDepartmentUsers = (id: string) =>
  get<Success<DepartmentUser[]>>(`/iam/admin/v1/departments/${id}/users`);

export const addDepartmentUser = (department_id: string, user_id: string, is_leader = false) =>
  post<Success<DepartmentUser>>(`/iam/admin/v1/departments/${department_id}/users`, {
    user_id,
    is_leader,
  });

export const removeDepartmentUser = (department_id: string, user_id: string) =>
  del<Success<void>>(`/iam/admin/v1/departments/${department_id}/users/${user_id}`);

/**
 * 批量添加部门成员
 */
export const batchAddDepartmentUsers = (department_id: string, user_ids: string[]) =>
  post<Success<{ added: number }>>(`/iam/admin/v1/departments/${department_id}/users/batch`, { user_ids });

/**
 * 启用部门成员
 */
export const enableDepartmentUser = (department_id: string, user_id: string) =>
  post<Success<{ user_id: string; status: string }>>(`/iam/admin/v1/departments/${department_id}/users/${user_id}/enable`);

/**
 * 停用部门成员
 */
export const disableDepartmentUser = (department_id: string, user_id: string) =>
  post<Success<{ user_id: string; status: string }>>(`/iam/admin/v1/departments/${department_id}/users/${user_id}/disable`);

/**
 * 获取部门详情（含统计信息）
 */
export const getDepartmentDetail = (id: string) =>
  get<Success<DepartmentDetail>>(`/iam/admin/v1/departments/${id}/detail`);

/**
 * 获取部门成员列表（详细版）
 */
export const getDepartmentMembers = (id: string) =>
  get<Success<DepartmentUser[]>>(`/iam/admin/v1/departments/${id}/members`);
