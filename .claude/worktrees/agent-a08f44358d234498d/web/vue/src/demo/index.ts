import type { ModuleDescriptor } from "@/framework/module/types";
import { demoRoutes } from "./router";

/**
 * Demo 模块描述符
 */
export const demoModule: ModuleDescriptor = {
  name: "demo",
  version: "1.0.0",
  getRoutes: () => demoRoutes,
  icon: "database",
};

export default demoModule;
