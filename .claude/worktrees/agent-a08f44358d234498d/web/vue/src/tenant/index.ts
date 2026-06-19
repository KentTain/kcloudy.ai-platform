import type { ModuleDescriptor } from "@/framework/module/types";
import { tenantRoutes } from "./router";

/**
 * Tenant 模块描述符
 */
export const tenantModule: ModuleDescriptor = {
  name: "tenant",
  version: "1.0.0",
  getRoutes: () => tenantRoutes,
  icon: "building",
};

export * from "./api/tenant";
export * from "./types";
