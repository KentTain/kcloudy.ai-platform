import type { ModuleDescriptor } from "@/framework/module/types";
import { aiRoutes } from "./router";

// 导出类型定义
export type {
  UIMessagePart,
  TextPart,
  ImagePart,
  ToolCallPart,
  ToolResultPart,
  UIMessage,
  AppUIMessage,
  ModelConfig,
  AIChatRequest,
  AIChatResponse,
  Conversation,
} from "./types";

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
