import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { Organization, OrganizationUser, OrganizationDetail, OrganizationQuery } from "@/iam/types";

export interface OrganizationCreate {
  name: string;
  code?: string;
  parent_id?: string;
  sort_order?: number;
  leader_id?: string;
}

export interface OrganizationUpdate {
  name?: string;
  code?: string;
  sort_order?: number;
  leader_id?: string;
  status?: string;
}

/**
 * 获取组织列表
 */
export const getOrganizations = (params?: OrganizationQuery) =>
  get<ApiResponse<Organization[]>>("/iam/admin/v1/organizations", { params });

/**
 * 获取组织树形结构
 */
export const getOrganizationTree = () =>
  get<ApiResponse<Organization[]>>("/iam/admin/v1/organizations/tree");

/**
 * 获取组织详情
 */
export const getOrganization = (id: string) =>
  get<ApiResponse<Organization>>(`/iam/admin/v1/organizations/${id}`);

/**
 * 创建组织
 */
export const createOrganization = (data: OrganizationCreate) =>
  post<ApiResponse<Organization>>("/iam/admin/v1/organizations", data);

/**
 * 更新组织
 */
export const updateOrganization = (id: string, data: OrganizationUpdate) =>
  put<ApiResponse<Organization>>(`/iam/admin/v1/organizations/${id}`, data);

/**
 * 删除组织
 */
export const deleteOrganization = (id: string) =>
  del<ApiResponse<void>>(`/iam/admin/v1/organizations/${id}`);

/**
 * 设置组织负责人
 */
export const setOrganizationLeader = (id: string, leader_id: string) =>
  updateOrganization(id, { leader_id });

/**
 * 获取组织用户
 */
export const getOrganizationUsers = (id: string) =>
  get<ApiResponse<OrganizationUser[]>>(`/iam/admin/v1/organizations/${id}/users`);

export const addOrganizationUser = (organization_id: string, user_id: string, is_leader = false) =>
  post<ApiResponse<OrganizationUser>>(`/iam/admin/v1/organizations/${organization_id}/users`, {
    user_id,
    is_leader,
  });

export const removeOrganizationUser = (organization_id: string, user_id: string) =>
  del<ApiResponse<void>>(`/iam/admin/v1/organizations/${organization_id}/users/${user_id}`);

/**
 * 批量添加组织成员
 */
export const batchAddOrganizationUsers = (organization_id: string, user_ids: string[]) =>
  post<ApiResponse<{ added: number }>>(`/iam/admin/v1/organizations/${organization_id}/users/batch`, { user_ids });

/**
 * 启用组织成员
 */
export const enableOrganizationUser = (organization_id: string, user_id: string) =>
  post<ApiResponse<{ user_id: string; status: string }>>(`/iam/admin/v1/organizations/${organization_id}/users/${user_id}/enable`);

/**
 * 停用组织成员
 */
export const disableOrganizationUser = (organization_id: string, user_id: string) =>
  post<ApiResponse<{ user_id: string; status: string }>>(`/iam/admin/v1/organizations/${organization_id}/users/${user_id}/disable`);

/**
 * 获取组织详情（含统计信息）
 */
export const getOrganizationDetail = (id: string) =>
  get<ApiResponse<OrganizationDetail>>(`/iam/admin/v1/organizations/${id}/detail`);

/**
 * 获取组织成员列表（详细版）
 */
export const getOrganizationMembers = (id: string) =>
  get<ApiResponse<OrganizationUser[]>>(`/iam/admin/v1/organizations/${id}/members`);
