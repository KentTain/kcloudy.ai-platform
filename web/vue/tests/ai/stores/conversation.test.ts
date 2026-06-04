/**
 * 会话状态管理 Store 测试
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useConversationStore } from "@/ai/stores/conversation";

// Mock API
vi.mock("@/ai/api/conversation", () => ({
  getConversations: vi.fn(() =>
    Promise.resolve({
      conversations: [
        {
          id: "conv-1",
          name: "会话1",
          created_at: "2025-01-01T00:00:00Z",
          message_count: 5,
        },
        {
          id: "conv-2",
          name: "会话2",
          created_at: "2025-01-02T00:00:00Z",
          message_count: 3,
        },
      ],
    })
  ),
  deleteConversation: vi.fn(() => Promise.resolve({ success: true })),
}));

describe("Conversation Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("初始状态", () => {
    it("初始化时为空会话列表", () => {
      const store = useConversationStore();

      expect(store.conversations).toEqual([]);
      expect(store.activeConversation).toBeNull();
      expect(store.loading).toBe(false);
      expect(store.error).toBeNull();
    });

    it("初始化时有默认模型配置", () => {
      const store = useConversationStore();

      expect(store.currentModel).toEqual({
        provider: "openai",
        name: "gpt-4o-mini",
      });
    });

    it("activeConversationId 返回 null 当无活跃会话时", () => {
      const store = useConversationStore();

      expect(store.activeConversationId).toBeNull();
    });

    it("isPending 返回 loading 状态", () => {
      const store = useConversationStore();

      expect(store.isPending).toBe(false);
      store.loading = true;
      expect(store.isPending).toBe(true);
    });
  });

  describe("fetchConversations", () => {
    it("成功获取会话列表", async () => {
      const store = useConversationStore();

      await store.fetchConversations();

      expect(store.conversations).toHaveLength(2);
      expect(store.conversations[0].title).toBe("会话1");
      expect(store.conversations[1].title).toBe("会话2");
      expect(store.loading).toBe(false);
      expect(store.error).toBeNull();
    });

    it("获取会话列表时设置 loading 状态", async () => {
      const store = useConversationStore();

      const promise = store.fetchConversations();
      expect(store.loading).toBe(true);

      await promise;
      expect(store.loading).toBe(false);
    });

    it("获取失败时设置错误信息", async () => {
      const { getConversations } = await import("@/ai/api/conversation");
      vi.mocked(getConversations).mockRejectedValueOnce(new Error("网络错误"));

      const store = useConversationStore();

      await store.fetchConversations();

      expect(store.error).toBe("网络错误");
      expect(store.loading).toBe(false);
    });
  });

  describe("selectConversation", () => {
    it("选择会话", async () => {
      const store = useConversationStore();
      await store.fetchConversations();

      store.selectConversation(store.conversations[0]);

      expect(store.activeConversation).toEqual(store.conversations[0]);
      expect(store.activeConversationId).toBe("conv-1");
    });

    it("取消选择会话", async () => {
      const store = useConversationStore();
      await store.fetchConversations();
      store.selectConversation(store.conversations[0]);

      store.selectConversation(null);

      expect(store.activeConversation).toBeNull();
      expect(store.activeConversationId).toBeNull();
    });
  });

  describe("selectConversationById", () => {
    it("通过 ID 选择会话", async () => {
      const store = useConversationStore();
      await store.fetchConversations();

      store.selectConversationById("conv-2");

      expect(store.activeConversation?.id).toBe("conv-2");
      expect(store.activeConversation?.title).toBe("会话2");
    });

    it("ID 不存在时设置 null", async () => {
      const store = useConversationStore();
      await store.fetchConversations();
      store.selectConversation(store.conversations[0]);

      store.selectConversationById("non-existent");

      expect(store.activeConversation).toBeNull();
    });

    it("传入 null 时清空活跃会话", async () => {
      const store = useConversationStore();
      await store.fetchConversations();
      store.selectConversation(store.conversations[0]);

      store.selectConversationById(null);

      expect(store.activeConversation).toBeNull();
    });
  });

  describe("removeConversation", () => {
    it("删除会话", async () => {
      const store = useConversationStore();
      await store.fetchConversations();

      await store.removeConversation("conv-1");

      expect(store.conversations).toHaveLength(1);
      expect(store.conversations[0].id).toBe("conv-2");
    });

    it("删除当前活跃会话时清空活跃状态", async () => {
      const store = useConversationStore();
      await store.fetchConversations();
      store.selectConversation(store.conversations[0]);

      await store.removeConversation("conv-1");

      expect(store.activeConversation).toBeNull();
    });

    it("删除非活跃会话不影响活跃状态", async () => {
      const store = useConversationStore();
      await store.fetchConversations();
      store.selectConversation(store.conversations[0]);

      await store.removeConversation("conv-2");

      expect(store.activeConversation?.id).toBe("conv-1");
    });
  });

  describe("模型配置管理", () => {
    it("setModel 更新模型配置", () => {
      const store = useConversationStore();

      store.setModel({ provider: "anthropic", name: "claude-3-opus" });

      expect(store.currentModel).toEqual({
        provider: "anthropic",
        name: "claude-3-opus",
      });
    });

    it("resetModel 重置为默认模型", () => {
      const store = useConversationStore();
      store.setModel({ provider: "anthropic", name: "claude-3-opus" });

      store.resetModel();

      expect(store.currentModel).toEqual({
        provider: "openai",
        name: "gpt-4o-mini",
      });
    });
  });

  describe("clearError", () => {
    it("清空错误信息", async () => {
      const { getConversations } = await import("@/ai/api/conversation");
      vi.mocked(getConversations).mockRejectedValueOnce(new Error("测试错误"));

      const store = useConversationStore();
      await store.fetchConversations();
      expect(store.error).toBe("测试错误");

      store.clearError();

      expect(store.error).toBeNull();
    });
  });
});
