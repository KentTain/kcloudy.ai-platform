/**
 * 权限申请 API
 */

import { get, post } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type {
  PermissionRequestItem,
  PermissionRequestCreate,
  PermissionRequestQuery,
  PermissionRequestApproval,
} from "@/iam/types/permissionRequest";

/**
 * 获取权限申请列表
 */
export const getPermissionRequests = (params?: PermissionRequestQuery) =>
  get<ApiResponse<PermissionRequestItem[]>>("/iam/console/v1/permission-requests", { params });

/**
 * 获取待审批列表
 */
export const getPendingApprovals = (params?: PermissionRequestQuery) =>
  get<ApiResponse<PermissionRequestItem[]>>("/iam/console/v1/permission-requests/pending", { params });

/**
 * 提交权限申请
 */
export const submitPermissionRequest = (data: PermissionRequestCreate) =>
  post<ApiResponse<PermissionRequestItem>>("/iam/console/v1/permission-requests", data);

/**
 * 审批通过
 */
export const approvePermissionRequest = (id: string, data?: PermissionRequestApproval) =>
  post<ApiResponse<void>>(`/iam/console/v1/permission-requests/${id}/approve`, data);

/**
 * 审批拒绝
 */
export const rejectPermissionRequest = (id: string, data: PermissionRequestApproval) =>
  post<ApiResponse<void>>(`/iam/console/v1/permission-requests/${id}/reject`, data);
