/**
 * 权限管理 API（角色 + 资源 ACL）
 */

import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { LibraryRole, ResourceAcl, PaginatedQuery } from "../types";

// ── 文档库角色 ──────────────────────────────────────────────────

export const getRoles = (libraryId: string, params?: PaginatedQuery) =>
  get<ApiResponse<LibraryRole[]>>(`/document/console/v1/libraries/${libraryId}/roles`, { params });

export const getRole = (libraryId: string, roleId: string) =>
  get<ApiResponse<LibraryRole>>(`/document/console/v1/libraries/${libraryId}/roles/${roleId}`);

export const createRole = (libraryId: string, data: Partial<LibraryRole>) =>
  post<ApiResponse<LibraryRole>>(`/document/console/v1/libraries/${libraryId}/roles`, data);

export const updateRole = (libraryId: string, roleId: string, data: Partial<LibraryRole>) =>
  put<ApiResponse<LibraryRole>>(`/document/console/v1/libraries/${libraryId}/roles/${roleId}`, data);

export const deleteRole = (libraryId: string, roleId: string) =>
  del<ApiResponse<void>>(`/document/console/v1/libraries/${libraryId}/roles/${roleId}`);

// ── 资源 ACL ────────────────────────────────────────────────────

export const getResourceAcls = (libraryId: string, params?: PaginatedQuery) =>
  get<ApiResponse<ResourceAcl[]>>(`/document/console/v1/libraries/${libraryId}/resource-acls`, { params });

export const createResourceAcl = (libraryId: string, data: Partial<ResourceAcl>) =>
  post<ApiResponse<ResourceAcl>>(`/document/console/v1/libraries/${libraryId}/resource-acls`, data);

export const deleteResourceAcl = (libraryId: string, aclId: string) =>
  del<ApiResponse<void>>(`/document/console/v1/libraries/${libraryId}/resource-acls/${aclId}`);
