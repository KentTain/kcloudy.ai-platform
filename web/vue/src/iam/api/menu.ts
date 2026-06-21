import { get } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { MenuListResponse, Permission } from "@/iam/types";

/**
 * 获取所有菜单（树形）
 */
export const getMenus = () => get<ApiResponse<MenuListResponse>>("/iam/admin/v1/menus");

/**
 * 获取菜单关联的权限列表
 */
export const getMenuPermissions = (menuId: string) =>
  get<ApiResponse<Permission[]>>(`/iam/admin/v1/menus/${menuId}/permissions`);
