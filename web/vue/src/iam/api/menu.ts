import { get } from "@/framework/api/client";
import type { ApiResponse, MenuListResponse } from "../types";

/**
 * 获取所有菜单（树形）
 */
export const getMenus = () => get<ApiResponse<MenuListResponse>>("/v1/iam/menu");
