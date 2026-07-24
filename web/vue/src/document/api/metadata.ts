/**
 * 元数据管理 API
 */

import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { MetadataField, ResourceMetadata, PaginatedQuery } from "../types";

// ── 元数据字段 ──────────────────────────────────────────────────

export const getMetadataFields = (libraryId: string, params?: PaginatedQuery) =>
  get<ApiResponse<MetadataField[]>>(`/document/console/v1/libraries/${libraryId}/metadata-fields`, { params });

export const createMetadataField = (libraryId: string, data: Partial<MetadataField>) =>
  post<ApiResponse<MetadataField>>(`/document/console/v1/libraries/${libraryId}/metadata-fields`, data);

export const updateMetadataField = (libraryId: string, fieldId: string, data: Partial<MetadataField>) =>
  put<ApiResponse<MetadataField>>(`/document/console/v1/libraries/${libraryId}/metadata-fields/${fieldId}`, data);

export const deleteMetadataField = (libraryId: string, fieldId: string) =>
  del<ApiResponse<void>>(`/document/console/v1/libraries/${libraryId}/metadata-fields/${fieldId}`);

// ── 资源元数据 ──────────────────────────────────────────────────

export const getResourceMetadata = (libraryId: string, params?: PaginatedQuery & { resource_type?: string; resource_id?: string }) =>
  get<ApiResponse<ResourceMetadata[]>>(`/document/console/v1/libraries/${libraryId}/resource-metadata`, { params });
