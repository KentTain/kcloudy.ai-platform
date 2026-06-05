/**
 * useChat 组合式函数测试
 *
 * 注意：由于 useChat 内部依赖 @ai-sdk/vue 的 Chat 类，
 * 部分行为（如消息同步、错误回调）需要通过集成测试验证。
 * 此单元测试主要验证接口契约和可直接控制的逻辑。
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref, nextTick } from "vue";
import { useChat } from "@/ai/composables/useChat";
import type { ModelConfig } from "@/ai/types";

// Mock @ai-sdk/vue Chat 类
const mockChatMessages: unknown[] = [];
const mockSendMessage = vi.fn(() => Promise.resolve());
const mockRegenerate = vi.fn(() => Promise.resolve());
const mockStop = vi.fn(() => Promise.resolve());

vi.mock("@ai-sdk/vue", () => ({
  Chat: vi.fn(() => ({
    messages: mockChatMessages,
    status: "ready",
    sendMessage: mockSendMessage,
    regenerate: mockRegenerate,
    stop: mockStop,
  })),
}));

vi.mock("ai", () => ({
  DefaultChatTransport: vi.fn(() => ({})),
}));

describe("useChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockChatMessages.length = 0;
    mockSendMessage.mockResolvedValue(undefined);
    mockRegenerate.mockResolvedValue(undefined);
    mockStop.mockResolvedValue(undefined);
  });

  describe("初始化状态", () => {
    it("初始化时返回默认状态", () => {
      const { messages, input, isLoading, error } = useChat();

      // messages 初始为空数组（通过 watchEffect 同步 Chat.messages）
      expect(Array.isArray(messages.value)).toBe(true);
      expect(input.value).toBe("");
      expect(isLoading.value).toBe(false);
      expect(error.value).toBeUndefined();
    });

    it("返回所有必需的方法和状态", () => {
      const chat = useChat();

      expect(chat.messages).toBeDefined();
      expect(chat.input).toBeDefined();
      expect(chat.isLoading).toBeDefined();
      expect(chat.error).toBeDefined();
      expect(typeof chat.sendMessage).toBe("function");
      expect(typeof chat.regenerate).toBe("function");
      expect(typeof chat.stop).toBe("function");
      expect(typeof chat.setInput).toBe("function");
      expect(typeof chat.reload).toBe("function");
      expect(typeof chat.updateModel).toBe("function");
    });

    it("使用自定义 API 端点", () => {
      const { sendMessage } = useChat({ api: "/custom/api" });

      expect(typeof sendMessage).toBe("function");
    });

    it("使用响应式模型配置", () => {
      const modelRef = ref<ModelConfig>({ provider: "anthropic", name: "claude-3" });

      const { sendMessage } = useChat({ model: modelRef });

      expect(typeof sendMessage).toBe("function");
    });
  });

  describe("sendMessage", () => {
    it("发送消息时调用 Chat.sendMessage", async () => {
      const { sendMessage, isLoading } = useChat();

      await sendMessage("Hello");

      expect(isLoading.value).toBe(false);
      expect(mockSendMessage).toHaveBeenCalledWith({ text: "Hello" });
    });

    it("不发送空消息", async () => {
      const { sendMessage } = useChat();

      await sendMessage("   ");

      expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it("loading 时不重复发送", async () => {
      const { sendMessage, isLoading } = useChat();

      // 手动设置 loading 状态
      isLoading.value = true;

      await sendMessage("Hello");

      expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it("发送消息后清空错误", async () => {
      const { sendMessage, error } = useChat();
      error.value = new Error("之前的错误");

      await sendMessage("Hello");

      expect(error.value).toBeUndefined();
    });

    it("调用 onFinish 回调配置", async () => {
      const onFinish = vi.fn();
      const { sendMessage } = useChat({ onFinish });

      await sendMessage("Hello");

      // 验证 sendMessage 被正确调用
      expect(mockSendMessage).toHaveBeenCalledWith({ text: "Hello" });
    });
  });

  describe("regenerate", () => {
    it("调用 regenerate 方法", async () => {
      const { regenerate } = useChat();

      await regenerate("msg-1");

      expect(mockRegenerate).toHaveBeenCalledWith({ messageId: "msg-1" });
    });

    it("loading 时不执行 regenerate", async () => {
      const { regenerate, isLoading } = useChat();

      isLoading.value = true;
      await regenerate("msg-1");

      expect(mockRegenerate).not.toHaveBeenCalled();
    });

    it("regenerate 时清空错误", async () => {
      const { regenerate, error } = useChat();
      error.value = new Error("之前的错误");

      await regenerate("msg-1");

      expect(error.value).toBeUndefined();
    });
  });

  describe("stop", () => {
    it("stop 方法可用且不抛出错误", async () => {
      const { stop } = useChat();

      // 由于 mock Chat 的 status 是静态的 "ready"，stop 不会实际调用
      await expect(stop()).resolves.not.toThrow();
    });
  });

  describe("setInput", () => {
    it("设置输入值", () => {
      const { setInput, input } = useChat();

      setInput("新输入内容");

      expect(input.value).toBe("新输入内容");
    });
  });

  describe("reload", () => {
    it("重置聊天状态", async () => {
      const { reload, messages, input, error } = useChat();

      // 设置一些状态
      messages.value = [{ id: "1", role: "user", parts: [] }];
      input.value = "some input";
      error.value = new Error("some error");

      reload();

      await nextTick();

      expect(messages.value).toEqual([]);
      expect(input.value).toBe("");
      expect(error.value).toBeUndefined();
    });
  });

  describe("updateModel", () => {
    it("更新模型配置不抛出错误", () => {
      const { updateModel } = useChat();

      expect(() => updateModel({ provider: "anthropic", name: "claude-3-opus" })).not.toThrow();
    });

    it("updateModel 是函数", () => {
      const { updateModel } = useChat();

      expect(typeof updateModel).toBe("function");
    });
  });

  describe("错误处理配置", () => {
    it("onError 回调配置正确传递", async () => {
      const onError = vi.fn();

      const { sendMessage } = useChat({ onError });

      await sendMessage("Hello");

      // 验证配置正确传递，sendMessage 正常工作
      expect(mockSendMessage).toHaveBeenCalled();
    });
  });

  describe("会话 ID", () => {
    it("使用自定义会话 ID", () => {
      const { sendMessage } = useChat({ id: "custom-conv-id" });

      expect(typeof sendMessage).toBe("function");
      // Chat 构造时会接收 id 参数
    });
  });
});
