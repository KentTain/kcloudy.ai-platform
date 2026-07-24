/**
 * 人设管理 API
 */

import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/api/types";
import type { Persona, PaginatedQuery } from "../types";

export const getPersonas = (params?: PaginatedQuery) =>
  get<ApiResponse<Persona[]>>("/document/admin/v1/personas", { params });

export const getPersona = (id: string) =>
  get<ApiResponse<Persona>>(`/document/admin/v1/personas/${id}`);

export const createPersona = (data: Partial<Persona>) =>
  post<ApiResponse<Persona>>("/document/admin/v1/personas", data);

export const updatePersona = (id: string, data: Partial<Persona>) =>
  put<ApiResponse<Persona>>(`/document/admin/v1/personas/${id}`, data);

export const deletePersona = (id: string) =>
  del<ApiResponse<void>>(`/document/admin/v1/personas/${id}`);
