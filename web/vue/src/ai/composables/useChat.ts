/**
 * useChat 组合式函数
 *
 * 封装 @ai-sdk/vue Chat 类，集成模型选择功能
 * 适配 @ai-sdk/vue v3.x API
 */
import { ref, type Ref, shallowRef, toValue } from "vue";
import { Chat } from "@ai-sdk/vue";
import { DefaultChatTransport, type UIMessage as AiUIMessage } from "ai";
import type { ModelConfig, UIMessage } from "@/ai/types";

/**
 * useChat 配置选项
 */
export interface UseChatOptions {
  /** API 端点，默认 /api/v1/chat-messages */
  api?: string;
  /** 会话 ID */
  id?: string;
  /** 当前模型 */
  model?: Ref<ModelConfig> | ModelConfig;
  /** 初始消息 */
  initialMessages?: UIMessage[];
  /** 请求完成回调 */
  onFinish?: (message: UIMessage) => void;
  /** 错误回调 */
  onError?: (error: Error) => void;
}

/**
 * useChat 返回值
 */
export interface UseChatReturn {
  /** 消息列表 */
  messages: Ref<UIMessage[]>;
  /** 输入文本 */
  input: Ref<string>;
  /** 是否正在加载 */
  isLoading: Ref<boolean>;
  /** 错误信息 */
  error: Ref<Error | undefined>;
  /** 发送消息 */
  sendMessage: (text: string) => Promise<void>;
  /** 重新生成 */
  regenerate: (messageId?: string) => Promise<void>;
  /** 停止生成 */
  stop: () => Promise<void>;
  /** 设置输入 */
  setInput: (value: string) => void;
  /** 重置聊天 */
  reload: () => void;
  /** 更新模型配置 */
  updateModel: (newModel: ModelConfig) => void;
}

/**
 * 将 ModelConfig 转换为普通对象
 */
function resolveModelConfig(model: Ref<ModelConfig> | ModelConfig | undefined): ModelConfig {
  if (!model) {
    return { provider: "openai", name: "gpt-4o-mini" };
  }
  return toValue(model);
}

/**
 * 封装 @ai-sdk/vue Chat 的组合式函数
 *
 * @param options 配置选项
 * @returns useChat 返回值
 */
export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const {
    api = "/api/v1/chat-messages",
    id,
    model,
    initialMessages = [],
    onFinish,
    onError,
  } = options;

  // 响应式状态
  const messages = ref<UIMessage[]>([...initialMessages]) as Ref<UIMessage[]>;
  const input = ref("");
  const isLoading = ref(false);
  const error = ref<Error | undefined>(undefined);

  // 获取当前模型配置
  const currentModel = resolveModelConfig(model);

  // 创建 Transport
  const transport = new DefaultChatTransport<AiUIMessage>({
    api,
    body: { model: currentModel },
  });

  // 创建 Chat 实例
  const chat = shallowRef(
    new Chat({
      id,
      transport,
      messages: initialMessages as AiUIMessage[],
      onFinish: (event) => {
        if (onFinish && event.message) {
          onFinish(event.message as UIMessage);
        }
      },
      onError: (err: Error) => {
        error.value = err;
        onError?.(err);
      },
    })
  );

  // 同步 Chat 实例的消息到响应式状态
  const syncMessages = () => {
    messages.value = [...(chat.value.messages as UIMessage[])];
  };

  // 发送消息
  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading.value) return;

    isLoading.value = true;
    error.value = undefined;

    try {
      await chat.value.sendMessage({ text });
      syncMessages();
    } finally {
      isLoading.value = false;
    }
  };

  // 重新生成
  const regenerate = async (messageId?: string) => {
    if (isLoading.value) return;

    isLoading.value = true;
    error.value = undefined;

    try {
      await chat.value.regenerate({ messageId });
      syncMessages();
    } finally {
      isLoading.value = false;
    }
  };

  // 停止生成
  const stop = async () => {
    if (chat.value.status === "streaming") {
      await chat.value.stop();
      syncMessages();
    }
  };

  // 设置输入
  const setInput = (value: string) => {
    input.value = value;
  };

  // 重置聊天
  const reload = () => {
    messages.value = [];
    error.value = undefined;
    input.value = "";
    // 重新创建 Chat 实例
    const newTransport = new DefaultChatTransport<AiUIMessage>({
      api,
      body: { model: currentModel },
    });
    chat.value = new Chat({
      id,
      transport: newTransport,
      messages: [],
      onFinish: (event) => {
        if (onFinish && event.message) {
          onFinish(event.message as UIMessage);
        }
      },
      onError: (err: Error) => {
        error.value = err;
        onError?.(err);
      },
    });
  };

  // 更新模型配置
  const updateModel = (newModel: ModelConfig) => {
    // 更新当前模型
    Object.assign(currentModel, newModel);
    // 重新创建 transport 和 chat 实例
    const newTransport = new DefaultChatTransport<AiUIMessage>({
      api,
      body: { model: currentModel },
    });
    chat.value = new Chat({
      id,
      transport: newTransport,
      messages: messages.value as AiUIMessage[],
      onFinish: (event) => {
        if (onFinish && event.message) {
          onFinish(event.message as UIMessage);
        }
      },
      onError: (err: Error) => {
        error.value = err;
        onError?.(err);
      },
    });
  };

  return {
    messages,
    input,
    isLoading,
    error,
    sendMessage,
    regenerate,
    stop,
    setInput,
    reload,
    updateModel,
  };
}

export default useChat;
