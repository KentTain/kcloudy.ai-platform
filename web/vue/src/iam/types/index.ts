/**
 * IAM 模块类型定义
 */

// 从 framework 导入统一类型并重新导出
export type { ApiResponse, PageResult } from "@/framework/types";

// 用户类型
export interface User {
  id: string;
  tenant_id: string;
  username: string;
  email?: string;
  phone?: string;
  nickname?: string;
  avatar?: string;
  status: "active" | "inactive" | "locked";
  profile_completed: boolean;
  is_email_verified: boolean;
  is_phone_verified: boolean;
  last_login_at?: string;
  created_at: string;
  roles: string[];
  permissions: string[];
  tenants?: UserTenant[];
}

// 用户租户类型
export interface UserTenant {
  id: string;
  name: string;
  code: string;
  is_default: boolean;
}

// 角色类型
export interface Role {
  id: string;
  tenant_id?: string;
  code: string;
  name: string;
  description?: string;
  is_system: boolean;
  created_at: string;
}

// 权限类型
export interface Permission {
  id: string;
  code: string;
  name: string;
  resource: string;
  action: string;
  description?: string;
  created_at: string;
}

// 权限分组类型
export interface PermissionGroup {
  resource: string;
  permissions: Permission[];
}

// 部门用户类型
export interface DepartmentUser extends User {
  department_id?: string;
  department_name?: string;
}

// 部门类型
export interface Department {
  id: string;
  tenant_id: string;
  parent_id?: string;
  name: string;
  code?: string;
  sort_order: number;
  leader_id?: string;
  status: "active" | "inactive";
  created_at: string;
  children?: Department[];
}

// 登录请求
export interface LoginRequest {
  account: string;
  password: string;
}

// 登录响应
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  need_complete_profile?: boolean;
  tenant_id?: string;
}

// 用户相关类型
export interface CreateUserParams {
  username: string;
  email?: string;
  phone?: string;
  nickname?: string;
  password: string;
  role_ids?: string[];
  department_id?: string;
}

export interface UpdateUserParams {
  email?: string;
  phone?: string;
  nickname?: string;
  avatar?: string;
  role_ids?: string[];
  department_id?: string;
  status?: "active" | "inactive" | "locked";
}

export interface UserQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  status?: string;
  department_id?: string;
  role_id?: string;
}

// 角色相关类型
export interface CreateRoleParams {
  name: string;
  code: string;
  description?: string;
  permission_ids?: string[];
}

export interface UpdateRoleParams {
  name?: string;
  description?: string;
  permission_ids?: string[];
}

export interface RoleQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
}

// 权限相关类型
export interface PermissionQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  resource?: string;
}

// 部门相关类型
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
  parent_id?: string;
  sort_order?: number;
  leader_id?: string;
  status?: "active" | "inactive";
}

export interface DepartmentQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  status?: string;
  parent_id?: string;
}

// 登录历史类型
export interface LoginHistory {
  id: string;
  user_id: string;
  login_at: string;
  ip_address: string;
  user_agent?: string;
  device_type?: "desktop" | "mobile" | "tablet";
  browser?: string;
  os?: string;
  status: "success" | "failed";
  location?: string;
}

// 登录历史查询参数
export interface LoginHistoryQueryParams {
  page?: number;
  page_size?: number;
  start_date?: string;
  end_date?: string;
}

// 菜单类型（从 framework 导入并重新导出）
export type { MenuTreeNode } from "@/framework/stores/menu";

// 菜单列表响应
export interface MenuListResponse {
  menus: MenuTreeNode[];
}
