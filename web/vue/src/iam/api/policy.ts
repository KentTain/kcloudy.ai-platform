/**
 * 企业 Policy API
 */

import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type {
  PolicyItem,
  PolicyCreate,
  PolicyUpdate,
  PolicyQuery,
} from "@/iam/types/policy";

/**
 * 获取 Policy 列表
 */
export const getPolicies = (params?: PolicyQuery) =>
  get<ApiResponse<PolicyItem[]>>("/iam/admin/v1/policies", { params });

/**
 * 获取 Policy 详情
 */
export const getPolicy = (id: string) =>
  get<ApiResponse<PolicyItem>>(`/iam/admin/v1/policies/${id}`);

/**
 * 创建 Policy
 */
export const createPolicy = (data: PolicyCreate) =>
  post<ApiResponse<PolicyItem>>("/iam/admin/v1/policies", data);

/**
 * 更新 Policy
 */
export const updatePolicy = (id: string, data: PolicyUpdate) =>
  put<ApiResponse<PolicyItem>>(`/iam/admin/v1/policies/${id}`, data);

/**
 * 删除 Policy
 */
export const deletePolicy = (id: string) =>
  del<ApiResponse<void>>(`/iam/admin/v1/policies/${id}`);

/**
 * 启用 Policy
 */
export const enablePolicy = (id: string) =>
  post<ApiResponse<void>>(`/iam/admin/v1/policies/${id}/enable`);

/**
 * 停用 Policy
 */
export const disablePolicy = (id: string) =>
  post<ApiResponse<void>>(`/iam/admin/v1/policies/${id}/disable`);
