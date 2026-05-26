/**
 * IAM 模块入口
 *
 * 提供身份认证与访问管理功能：
 * - 用户管理
 * - 角色管理
 * - 权限管理
 * - 部门管理
 */

// 导出所有类型
export type {
  User,
  Role,
  Permission,
  Department,
  LoginRequest,
  LoginResponse,
  ApiResponse,
  PageResult,
  CreateUserParams,
  UpdateUserParams,
  UserQueryParams,
  CreateRoleParams,
  UpdateRoleParams,
  RoleQueryParams,
  PermissionQueryParams,
  CreateDepartmentParams,
  UpdateDepartmentParams,
  DepartmentQueryParams,
} from "./types";

// 导出认证 API
export {
  login,
  logout,
  refreshToken,
  getCurrentUser,
  updateProfile,
  changePassword,
} from "./api";

// 导出用户管理 API
export {
  getUsers,
  getUser,
  createUser,
  updateUser,
  deleteUser,
  resetUserPassword,
  updateUserStatus,
} from "./api";

// 导出角色管理 API
export {
  getRoles,
  getRole,
  createRole,
  updateRole,
  deleteRole,
} from "./api";

// 导出权限管理 API
export {
  getPermissions,
  getPermission,
} from "./api";

// 导出部门管理 API
export {
  getDepartments,
  getDepartmentTree,
  getDepartment,
  createDepartment,
  updateDepartment,
  deleteDepartment,
} from "./api";
