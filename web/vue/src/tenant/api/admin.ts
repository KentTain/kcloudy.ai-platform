import { rawGet, rawPost } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { AdminInfo, AdminLoginRequest, AdminLoginResponse } from "@/tenant/types";

/**
 * 管理员登录
 */
export const adminLogin = (data: AdminLoginRequest) =>
  rawPost<ApiResponse<AdminLoginResponse>>("/tenant/admin/v1/auth/login", data);

/**
 * 管理员登出
 */
export const adminLogout = () => rawPost<ApiResponse<void>>("/tenant/admin/v1/auth/logout");

/**
 * 获取当前管理员信息
 */
export const getCurrentAdmin = () => rawGet<ApiResponse<AdminInfo>>("/tenant/admin/v1/admin/me");
