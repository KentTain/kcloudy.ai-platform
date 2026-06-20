import { get, post, put } from "@/framework/api/client";
import { resetUserPassword } from "./user";
import type { Success, PaginatedListResponse } from "@/framework/types";
import type {
  LoginHistory,
  LoginHistoryPaginatedQuery,
  LoginRequest,
  LoginResponse,
  UserUpdate,
  User,
} from "@/iam/types";

/**
 * 用户登录
 */
export const login = (data: LoginRequest) =>
  post<Success<LoginResponse>>("/iam/console/v1/auth/login", data);

/**
 * 用户登出
 */
export const logout = () => post<Success<void>>("/iam/console/v1/auth/logout");

/**
 * 刷新 Token
 */
export const refreshToken = (refresh_token: string) =>
  post<Success<LoginResponse>>("/iam/console/v1/auth/token/refresh", { refresh_token });

/**
 * 获取当前用户信息
 */
export const getCurrentUser = () => get<Success<User>>("/iam/console/v1/users/me");

/**
 * 更新当前用户资料
 */
export const updateCurrentUser = (data: UserUpdate) =>
  put<Success<User>>("/iam/console/v1/users/me", data);

export const updateProfile = updateCurrentUser;

/**
 * 修改密码
 */
export const changePassword = (old_password: string, new_password: string) =>
  put<Success<void>>("/iam/console/v1/users/password", {
    old_password,
    new_password,
  });

/**
 * 重置密码（管理员）
 */
export const resetPassword = resetUserPassword;

/**
 * 获取登录历史
 */
export const getLoginHistory = (params?: LoginHistoryPaginatedQuery) =>
  get<Success<PaginatedListResponse<LoginHistory>>>("/iam/console/v1/auth/login-history", { params });
