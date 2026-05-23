/**
 * IAM 模块类型定义
 */

// 用户类型
export interface User {
  id: string;
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

// 租户类型
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
}

// 统一 API 响应类型
export interface ApiResponse<T> {
  code: number;
  msg: string;
  data: T;
}

// 分页结果
export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
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

// 租户相关类型
export interface CreateTenantParams {
  name: string;
  code: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  expired_at?: string;
  settings?: Record<string, any>;
}

export interface UpdateTenantParams {
  name?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  expired_at?: string;
  settings?: Record<string, any>;
  status?: "active" | "inactive";
}

export interface TenantQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  status?: string;
}

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
