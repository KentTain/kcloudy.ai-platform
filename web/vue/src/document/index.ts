/**
 * 企业知识库管理模块入口
 */

import type { ModuleDescriptor } from "@/framework/module/types";

export const documentModule: ModuleDescriptor = {
  name: "document",
  version: "1.0.0",
  getRoutes: () => [],
  icon: "book-open",
};

export default documentModule;
