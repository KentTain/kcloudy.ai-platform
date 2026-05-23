import { get, post, put } from "@/framework/api/client";
import { resetUserPassword } from "./user";
import type {
  ApiResponse,
  LoginHistory,
  LoginHistoryQueryParams,
  LoginRequest,
  LoginResponse,
  PageResult,
  UpdateUserParams,
  User,
} from "../types";

/**
 * 用户登录
 */
export const login = (data: LoginRequest) =>
  post<ApiResponse<LoginResponse>>("/v1/iam/auth/login", data);

/**
 * 用户登出
 */
export const logout = () => post<ApiResponse<void>>("/v1/iam/auth/logout");

/**
 * 刷新 Token
 */
export const refreshToken = (refresh_token: string) =>
  post<ApiResponse<LoginResponse>>("/v1/iam/auth/token/refresh", { refresh_token });

/**
 * 获取当前用户信息
 */
export const getCurrentUser = () => get<ApiResponse<User>>("/v1/iam/user/me");

/**
 * 更新当前用户资料
 */
export const updateCurrentUser = (data: UpdateUserParams) =>
  put<ApiResponse<User>>("/v1/iam/user/me", data);

export const updateProfile = updateCurrentUser;

/**
 * 修改密码
 */
export const changePassword = (old_password: string, new_password: string) =>
  put<ApiResponse<void>>("/v1/iam/user/password", {
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
export const getLoginHistory = (params?: LoginHistoryQueryParams) =>
  get<ApiResponse<PageResult<LoginHistory>>>("/v1/iam/auth/login-history", params as Record<string, unknown>);
