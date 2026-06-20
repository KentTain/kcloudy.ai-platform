import { get } from "@/framework/api/client";
import type { Success } from "@/framework/types";
import type { MenuListResponse } from "@/iam/types";

/**
 * 获取所有菜单（树形）
 */
export const getMenus = () => get<Success<MenuListResponse>>("/iam/admin/v1/menus");
