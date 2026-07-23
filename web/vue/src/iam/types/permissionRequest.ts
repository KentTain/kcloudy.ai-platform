/**
 * 权限申请类型定义
 */

import type { BasePaginatedQuery } from "@/framework/types";

/** 权限申请项 */
export interface PermissionRequestItem {
  id: string;
  tenant_id: string;
  applicant_id: string;
  applicant_name: string;
  resource: string;
  action: string;
  reason: string;
  status: "pending" | "approved" | "rejected";
  approver_id?: string;
  approver_name?: string;
  approved_at?: string;
  reject_reason?: string;
  created_at: string;
  updated_at: string;
}

/** 创建权限申请 */
export interface PermissionRequestCreate {
  resource: string;
  action: string;
  reason: string;
}

/** 权限申请查询参数 */
export interface PermissionRequestQuery extends BasePaginatedQuery {
  status?: string;
  applicant_id?: string;
  approver_id?: string;
  resource?: string;
}

/** 审批操作数据 */
export interface PermissionRequestApproval {
  reason?: string;
}
