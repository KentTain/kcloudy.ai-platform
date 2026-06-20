import { get } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { MenuListResponse } from "@/iam/types";

/**
 * 获取所有菜单（树形）
 */
export const getMenus = () => get<ApiResponse<MenuListResponse>>("/iam/admin/v1/menus");
