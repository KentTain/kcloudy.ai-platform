/**
 * 用户菜单 API 客户端
 */
import { get } from "@/framework/api/client";

/**
 * 用户菜单响应类型
 * 与后端 UserMenuVo 对齐
 */
export interface UserMenuVo {
  id: string;
  code: string;
  name: string;
  icon: string | null;
  path: string | null;
  sort_order: number;
  children: UserMenuVo[];
}

/**
 * 用户菜单列表响应
 */
interface UserMenusResponse {
  data: UserMenuVo[];
}

/**
 * 获取当前用户菜单
 */
export const getUserMenus = () =>
  get<UserMenusResponse>("/console/v1/iam/users/menus");
