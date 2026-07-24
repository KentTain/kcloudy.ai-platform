/**
 * 文档库管理模块入口
 */

import type { ModuleDescriptor } from "@/framework/module/types";
import { documentRoutes } from "./router";

export const documentModule: ModuleDescriptor = {
  name: "document",
  version: "1.0.0",
  getRoutes: () => documentRoutes,
  icon: "book-open",
};

export default documentModule;
