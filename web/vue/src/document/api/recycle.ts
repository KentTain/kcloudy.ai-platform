/**
 * 回收站管理 API
 */

import { del, get, post } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { RecycleItem, PaginatedQuery } from "../types";

export const getRecycleItems = (libraryId: string, params?: PaginatedQuery) =>
  get<ApiResponse<RecycleItem[]>>(`/document/console/v1/libraries/${libraryId}/recycle`, { params });

export const restoreRecycleItem = (libraryId: string, itemId: string) =>
  post<ApiResponse<void>>(`/document/console/v1/libraries/${libraryId}/recycle/${itemId}/restore`);

export const permanentDeleteRecycleItem = (libraryId: string, itemId: string) =>
  del<ApiResponse<void>>(`/document/console/v1/libraries/${libraryId}/recycle/${itemId}`);

export const emptyRecycle = (libraryId: string) =>
  del<ApiResponse<void>>(`/document/console/v1/libraries/${libraryId}/recycle`);
