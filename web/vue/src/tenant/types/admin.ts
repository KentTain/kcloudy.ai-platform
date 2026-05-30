/**
 * 管理员认证类型定义
 */

// 管理员登录请求
export interface AdminLoginRequest {
  username: string;
  password: string;
}

// 管理员登录响应
export interface AdminLoginResponse {
  token: string;
  username: string;
  is_default: boolean;
}

// 管理员信息
export interface AdminInfo {
  id: string;
  username: string;
  is_default: boolean;
  is_active: boolean;
}
