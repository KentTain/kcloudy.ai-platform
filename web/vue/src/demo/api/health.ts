import { get } from "@/framework/api/client";

export interface HealthStatus {
  status: string;
  timestamp: string;
}

/**
 * 获取健康检查状态
 */
export const getHealth = (): Promise<HealthStatus> => get<HealthStatus>("/health");
