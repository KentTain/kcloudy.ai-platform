/**
 * 企业 Policy 类型定义
 */

import type { BasePaginatedQuery } from "@/framework/types";

/** Policy 项 */
export interface PolicyItem {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  type: "allow" | "deny";
  effect: "allow" | "deny";
  resources: string[];
  actions: string[];
  conditions?: Record<string, unknown>;
  priority: number;
  is_enabled: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

/** 创建 Policy */
export interface PolicyCreate {
  name: string;
  description?: string;
  type: "allow" | "deny";
  effect: "allow" | "deny";
  resources: string[];
  actions: string[];
  conditions?: Record<string, unknown>;
  priority?: number;
  is_enabled?: boolean;
}

/** 更新 Policy */
export interface PolicyUpdate {
  name?: string;
  description?: string;
  type?: "allow" | "deny";
  effect?: "allow" | "deny";
  resources?: string[];
  actions?: string[];
  conditions?: Record<string, unknown>;
  priority?: number;
  is_enabled?: boolean;
}

/** Policy 查询参数 */
export interface PolicyQuery extends BasePaginatedQuery {
  type?: string;
  is_enabled?: boolean;
  keyword?: string;
}
