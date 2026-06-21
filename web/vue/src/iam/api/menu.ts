import { get } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { MenuListResponse, PermissionListResponse } from "@/iam/types";

/**
 * 获取所有菜单（树形）
 */
export const getMenus = () => get<ApiResponse<MenuListResponse>>("/iam/admin/v1/menus");

/**
 * 获取菜单关联的权限列表
 */
export const getMenuPermissions = (menuId: string) =>
  get<ApiResponse<PermissionListResponse>>(`/iam/admin/v1/menus/${menuId}/permissions`);
