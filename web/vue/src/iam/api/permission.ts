import { get } from "@/framework/api/client";
import type { ApiResponse, PageResult, Permission, PermissionGroup } from "../types";

export interface PermissionQueryParams {
  page?: number;
  page_size?: number;
  resource?: string;
  keyword?: string;
}

/**
 * 获取权限列表
 */
export const getPermissions = (params?: PermissionQueryParams) =>
  get<ApiResponse<PageResult<Permission>>>("/admin/v1/iam/permissions", { params });

/**
 * 获取所有权限（不分页）
 */
export const getAllPermissions = async () => {
  const response = await getPermissions({ page: 1, page_size: 1000 });
  return {
    ...response,
    data: response.data.items,
  } as ApiResponse<Permission[]>;
};

/**
 * 按资源分组获取权限
 */
export const getPermissionsByResource = () =>
  get<ApiResponse<PermissionGroup[]>>("/admin/v1/iam/permissions/grouped");

/**
 * 获取权限详情
 */
export const getPermission = async (id: string) => {
  const response = await getAllPermissions();
  const permission = response.data.find((item) => item.id === id);
  if (!permission) {
    throw new Error("Permission not found");
  }
  return {
    ...response,
    data: permission,
  } as ApiResponse<Permission>;
};
