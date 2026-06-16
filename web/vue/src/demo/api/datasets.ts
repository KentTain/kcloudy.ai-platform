import { del, get, post, put } from "@/framework/api/client";
import type { ApiResponse } from "@/framework/types";

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface DatasetCreate {
  name: string;
  description?: string;
}

export interface DatasetUpdate {
  name?: string;
  description?: string;
}

/**
 * 获取知识库列表
 */
export const getDatasets = (): Promise<Dataset[]> =>
  get<ApiResponse<Dataset[]>>("/v1/datasets").then((res) => res.data);

/**
 * 获取知识库详情
 */
export const getDataset = (id: string): Promise<Dataset> =>
  get<ApiResponse<Dataset>>(`/v1/datasets/${id}`).then((res) => res.data);

/**
 * 创建知识库
 */
export const createDataset = (params: DatasetCreate): Promise<Dataset> =>
  post<ApiResponse<Dataset>>("/v1/datasets", params).then((res) => res.data);

/**
 * 更新知识库
 */
export const updateDataset = (id: string, params: DatasetUpdate): Promise<Dataset> =>
  put<ApiResponse<Dataset>>(`/v1/datasets/${id}`, params).then((res) => res.data);

/**
 * 删除知识库
 */
export const deleteDataset = (id: string): Promise<void> => del(`/v1/datasets/${id}`);
