/**
 * Tenant 模块类型定义
 */

// 从 framework 导入统一类型并重新导出
export type { ApiResponse, PageResult } from "@/framework/types";

// 导出管理员类型
export type {
  AdminLoginRequest,
  AdminLoginResponse,
  AdminInfo,
} from "./admin";

// 租户实体
export interface Tenant {
  id: string;
  name: string;
  code: string;
  status: "active" | "inactive";
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  expired_at?: string;
  settings?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

// 租户统计
export interface TenantStatsVo {
  tenant_id: string;
  user_count: number;
  storage_usage: number;
  active_users: number;
}

// 用户租户信息
export interface UserTenantVo {
  tenant_id: string;
  tenant_name: string;
  tenant_code: string;
  role_ids: string[];
  role_names: string[];
  department_id?: string;
  department_name?: string;
  is_current: boolean;
}

// 切换租户响应
export interface SwitchTenantVo {
  tenant_id: string;
  tenant_name: string;
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

// 租户查询参数
export interface TenantQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  status?: string;
}

// 创建租户参数
export interface CreateTenantParams {
  name: string;
  code: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  expired_at?: string;
  settings?: Record<string, any>;
}

// 更新租户参数
export interface UpdateTenantParams {
  name?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  expired_at?: string;
  settings?: Record<string, any>;
  status?: "active" | "inactive";
}
