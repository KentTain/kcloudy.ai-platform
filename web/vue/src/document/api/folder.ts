/**
 * 文件夹管理 API
 */

import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { Folder, PaginatedQuery } from "../types";

export const getFolders = (params?: PaginatedQuery & { library_id?: string }) =>
  get<ApiResponse<Folder[]>>("/document/console/v1/folders", { params });

export const getFolder = (id: string) =>
  get<ApiResponse<Folder>>(`/document/console/v1/folders/${id}`);

export const createFolder = (data: Partial<Folder>) =>
  post<ApiResponse<Folder>>("/document/console/v1/folders", data);

export const updateFolder = (id: string, data: Partial<Folder>) =>
  put<ApiResponse<Folder>>(`/document/console/v1/folders/${id}`, data);

export const deleteFolder = (id: string) =>
  del<ApiResponse<void>>(`/document/console/v1/folders/${id}`);
