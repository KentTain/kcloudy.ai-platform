/**
 * 标签管理 API
 */

import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { Tag, TagGroup, PaginatedQuery } from "../types";

// ── 标签 ────────────────────────────────────────────────────────

export const getTags = (params?: PaginatedQuery) =>
  get<ApiResponse<Tag[]>>("/document/admin/v1/tags", { params });

export const getTag = (id: string) =>
  get<ApiResponse<Tag>>(`/document/admin/v1/tags/${id}`);

export const createTag = (data: Partial<Tag>) =>
  post<ApiResponse<Tag>>("/document/admin/v1/tags", data);

export const updateTag = (id: string, data: Partial<Tag>) =>
  put<ApiResponse<Tag>>(`/document/admin/v1/tags/${id}`, data);

export const deleteTag = (id: string) =>
  del<ApiResponse<void>>(`/document/admin/v1/tags/${id}`);

// ── 标签组 ──────────────────────────────────────────────────────

export const getTagGroups = (params?: PaginatedQuery) =>
  get<ApiResponse<TagGroup[]>>("/document/admin/v1/tag-groups", { params });

export const createTagGroup = (data: Partial<TagGroup>) =>
  post<ApiResponse<TagGroup>>("/document/admin/v1/tag-groups", data);

export const updateTagGroup = (id: string, data: Partial<TagGroup>) =>
  put<ApiResponse<TagGroup>>(`/document/admin/v1/tag-groups/${id}`, data);

export const deleteTagGroup = (id: string) =>
  del<ApiResponse<void>>(`/document/admin/v1/tag-groups/${id}`);
