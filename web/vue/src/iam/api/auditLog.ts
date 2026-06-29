/**
 * 审计日志 API
 */

import { get } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { AuditLog, AuditLogOptions, AuditLogPaginatedQuery } from "@/iam/types";

/**
 * 获取审计日志列表
 */
export const getAuditLogs = (params?: AuditLogPaginatedQuery) =>
  get<ApiResponse<AuditLog[]>>("/iam/admin/v1/audit-logs", { params });

/**
 * 获取审计日志筛选选项
 */
export const getAuditOptions = () =>
  get<ApiResponse<AuditLogOptions>>("/iam/admin/v1/audit-logs/options");
