import client from "./client";

export interface HealthStatus {
  status: string;
  timestamp?: string;
}

export async function checkHealth(): Promise<HealthStatus> {
  const response = await client.get<HealthStatus>("/health");
  return response.data;
}
