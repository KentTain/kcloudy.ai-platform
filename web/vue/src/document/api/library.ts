/**
 * 文档库管理 API
 */

import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { Library, PaginatedQuery } from "../types";

export const getLibraries = (params?: PaginatedQuery & { library_type?: string }) =>
  get<ApiResponse<Library[]>>("/document/console/v1/libraries", { params });

export const getLibrary = (id: string) =>
  get<ApiResponse<Library>>(`/document/console/v1/libraries/${id}`);

export const createLibrary = (data: Partial<Library>) =>
  post<ApiResponse<Library>>("/document/console/v1/libraries", data);

export const updateLibrary = (id: string, data: Partial<Library>) =>
  put<ApiResponse<Library>>(`/document/console/v1/libraries/${id}`, data);

export const deleteLibrary = (id: string) =>
  del<ApiResponse<void>>(`/document/console/v1/libraries/${id}`);
