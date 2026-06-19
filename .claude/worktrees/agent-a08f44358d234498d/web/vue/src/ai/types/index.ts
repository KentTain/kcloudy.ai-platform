/**
 * AI 模块类型定义
 * 基于 Vercel AI SDK 标准协议
 */

/**
 * UI 消息部分类型
 */
export type UIMessagePartType = "text" | "image" | "tool-call" | "tool-result";

/**
 * UI 消息部分基础接口
 */
export interface UIMessagePartBase {
  type: UIMessagePartType;
}

/**
 * 文本消息部分
 */
export interface TextPart extends UIMessagePartBase {
  type: "text";
  text: string;
}

/**
 * 图像消息部分
 */
export interface ImagePart extends UIMessagePartBase {
  type: "image";
  image: string; // base64 或 URL
}

/**
 * 工具调用消息部分
 */
export interface ToolCallPart extends UIMessagePartBase {
  type: "tool-call";
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
}

/**
 * 工具结果消息部分
 */
export interface ToolResultPart extends UIMessagePartBase {
  type: "tool-result";
  toolCallId: string;
  toolName: string;
  result: unknown;
}

/**
 * UI 消息部分联合类型
 */
export type UIMessagePart = TextPart | ImagePart | ToolCallPart | ToolResultPart;

/**
 * 消息角色
 */
export type MessageRole = "user" | "assistant" | "system";

/**
 * UI 消息 - AI SDK 标准 UI 消息格式
 */
export interface UIMessage {
  /** 消息唯一标识 */
  id: string;
  /** 消息角色 */
  role: MessageRole;
  /** 消息部分数组 */
  parts: UIMessagePart[];
  /** 创建时间 */
  createdAt?: Date;
}

/**
 * AppUI 消息 - 扩展的 UI 消息，用于前端显示
 */
export interface AppUIMessage extends UIMessage {
  /** 是否正在流式传输 */
  isStreaming?: boolean;
  /** 错误信息 */
  error?: string;
}

/**
 * 模型配置
 */
export interface ModelConfig {
  /** 模型提供商 */
  provider: string;
  /** 模型名称 */
  name: string;
  /** 补全参数 */
  completionParams?: Record<string, unknown>;
}

/**
 * AI 对话请求 - AI SDK 标准请求格式
 */
export interface AIChatRequest {
  /** 会话 ID */
  id?: string;
  /** 消息列表 */
  messages: UIMessage[];
  /** 触发类型 */
  trigger?: "submit-message" | "regenerate";
  /** 消息 ID（用于 regenerate） */
  messageId?: string;
  /** 请求体扩展 */
  body?: {
    /** 模型配置 */
    model?: ModelConfig;
  };
}

/**
 * AI 对话响应
 */
export interface AIChatResponse {
  /** 会话 ID */
  id: string;
  /** 消息 ID */
  messageId: string;
  /** 是否完成 */
  done: boolean;
}

/**
 * 会话信息
 */
export interface Conversation {
  /** 会话 ID */
  id: string;
  /** 会话标题 */
  title: string;
  /** 创建时间 */
  createdAt: Date;
  /** 更新时间 */
  updatedAt: Date;
  /** 消息数量 */
  messageCount?: number;
}
