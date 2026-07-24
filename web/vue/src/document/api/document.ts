/**
 * 文档管理 API
 */

import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { Document, PaginatedQuery } from "../types";

export const getDocuments = (params?: PaginatedQuery & { library_id?: string; folder_id?: string }) =>
  get<ApiResponse<Document[]>>("/document/console/v1/documents", { params });

export const getDocument = (id: string) =>
  get<ApiResponse<Document>>(`/document/console/v1/documents/${id}`);

export const createDocument = (data: Partial<Document>) =>
  post<ApiResponse<Document>>("/document/console/v1/documents", data);

export const updateDocument = (id: string, data: Partial<Document>) =>
  put<ApiResponse<Document>>(`/document/console/v1/documents/${id}`, data);

export const deleteDocument = (id: string) =>
  del<ApiResponse<void>>(`/document/console/v1/documents/${id}`);
