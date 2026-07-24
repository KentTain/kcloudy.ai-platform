/**
 * 文档库成员管理 API
 */

import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { LibraryMember, PaginatedQuery } from "../types";

export const getMembers = (libraryId: string, params?: PaginatedQuery) =>
  get<ApiResponse<LibraryMember[]>>(`/document/console/v1/libraries/${libraryId}/members`, { params });

export const getMember = (libraryId: string, memberId: string) =>
  get<ApiResponse<LibraryMember>>(`/document/console/v1/libraries/${libraryId}/members/${memberId}`);

export const createMember = (libraryId: string, data: Partial<LibraryMember>) =>
  post<ApiResponse<LibraryMember>>(`/document/console/v1/libraries/${libraryId}/members`, data);

export const updateMember = (libraryId: string, memberId: string, data: Partial<LibraryMember>) =>
  put<ApiResponse<LibraryMember>>(`/document/console/v1/libraries/${libraryId}/members/${memberId}`, data);

export const deleteMember = (libraryId: string, memberId: string) =>
  del<ApiResponse<void>>(`/document/console/v1/libraries/${libraryId}/members/${memberId}`);
