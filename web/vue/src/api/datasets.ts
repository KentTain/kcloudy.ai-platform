import type { CreateDatasetRequest, Dataset } from "@/types";
import client from "./client";

export async function getDatasets(): Promise<Dataset[]> {
  const response = await client.get<{ code: number; msg: string; data: Dataset[] }>("/v1/datasets");
  return response.data.data;
}

export async function getDataset(id: string): Promise<Dataset> {
  const response = await client.get<{ code: number; msg: string; data: Dataset }>(
    `/v1/datasets/${id}`
  );
  return response.data.data;
}

export async function createDataset(data: CreateDatasetRequest): Promise<Dataset> {
  const response = await client.post<{ code: number; msg: string; data: Dataset }>(
    "/v1/datasets",
    data
  );
  return response.data.data;
}

export async function deleteDataset(id: string): Promise<void> {
  await client.delete(`/v1/datasets/${id}`);
}
