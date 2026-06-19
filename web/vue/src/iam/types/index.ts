/**
 * IAM 模块类型定义
 */

// 从 framework 导入统一类型
import type {
  ApiResponse as ApiResponseBase,
  BaseQuery,
  BasePaginatedQuery,
  PaginatedListResponse,
} from "@/framework/types";

// 重新导出统一类型
export type { BaseQuery, BasePaginatedQuery, PaginatedListResponse };
export type ApiResponse<T = unknown> = ApiResponseBase<T>;

/**
 * @deprecated 使用 PaginatedListResponse<T> 替代
 */
export type PageResult<T> = PaginatedListResponse<T>;

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
  // 扩展字段
  dept_id?: string;
  dept_name?: string;
  dept_path?: string;
  role_ids?: string[];
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
  // 扩展字段
  direct_member_count?: number;
  total_member_count?: number;
  path?: string;
  children_count?: number;
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
export interface UserCreate {
  username: string;
  email?: string;
  phone?: string;
  nickname?: string;
  password: string;
  role_ids?: string[];
  department_id?: string;
}

export interface UserUpdate {
  email?: string;
  phone?: string;
  nickname?: string;
  avatar?: string;
  role_ids?: string[];
  department_id?: string;
  status?: "active" | "inactive" | "locked";
}

/**
 * 用户分页查询参数
 */
export interface UserPaginatedQuery extends BasePaginatedQuery {
  status?: string;
  keyword?: string;
  department_id?: string;
  role_id?: string;
  dept_id?: string;
  include_children?: boolean;
}

// 角色相关类型
export interface RoleCreate {
  name: string;
  code: string;
  description?: string;
  permission_ids?: string[];
}

export interface RoleUpdate {
  name?: string;
  description?: string;
  permission_ids?: string[];
}

/**
 * 角色分页查询参数
 */
export interface RolePaginatedQuery extends BasePaginatedQuery {
  include_system?: boolean;
}

/**
 * 权限分页查询参数
 */
export interface PermissionPaginatedQuery extends BasePaginatedQuery {
  resource?: string;
}

// 部门相关类型
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
  parent_id?: string;
  sort_order?: number;
  leader_id?: string;
  status?: "active" | "inactive";
}

/**
 * 部门查询参数（非分页）
 */
export interface DepartmentQuery extends BaseQuery {
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

/**
 * 登录历史分页查询参数
 */
export interface LoginHistoryPaginatedQuery extends BasePaginatedQuery {
  start_date?: string;
  end_date?: string;
}

// 菜单类型（从 framework 导入并重新导出）
import type { MenuTreeNode } from "@/framework/stores/menu";
export type { MenuTreeNode };

// 菜单列表响应
export interface MenuListResponse {
  menus: MenuTreeNode[];
}

// ============================================
// 新增类型（iam-page-refactor）
// ============================================

/** 角色成员类型 */
export interface RoleMember {
  user_id: string;
  username: string;
  nickname?: string;
  email?: string;
  phone?: string;
  status: string;
}

/** 用户统计数据 */
export interface UserStats {
  total: number;
  enabled: number;
  disabled: number;
  multi_role: number;
}

/** 角色选项（下拉框用） */
export interface RoleOption {
  id: string;
  code: string;
  name: string;
  description?: string;
}

/** 组织树节点 */
export interface OrgTreeNode {
  id: string;
  name: string;
  code?: string;
  parent_id?: string;
  tree_level?: number;
  tree_leaf?: boolean;
  tree_sort?: number;
  has_org_num?: number;
  has_user_num?: number;
  children?: OrgTreeNode[];
}

/** 人员选择项 */
export interface PeopleItem {
  user_id: string;
  username: string;
  nickname?: string;
  email?: string;
  phone?: string;
  status: string;
  is_leader?: boolean;
}

/** 部门详情（含统计信息） */
export interface DepartmentDetail {
  id: string;
  name: string;
  code?: string;
  parent_id?: string;
  sort_order: number;
  leader_id?: string;
  status: string;
  created_at: string;
  path: string;
  direct_member_count: number;
  total_member_count: number;
  children_count: number;
}
