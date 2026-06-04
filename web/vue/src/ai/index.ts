import type { ModuleDescriptor } from "@/framework/module/types";
import { aiRoutes } from "./router";

/**
 * AI 模块描述符
 *
 * 提供 AI 对话功能，使用 Vercel AI SDK 标准协议与后端通信
 */
export const aiModule: ModuleDescriptor = {
  name: "ai",
  version: "1.0.0",
  getRoutes: () => aiRoutes,
  icon: "message-square",
};

export default aiModule;
