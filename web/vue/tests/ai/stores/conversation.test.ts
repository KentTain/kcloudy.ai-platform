/**
 * 会话状态管理 Store 测试
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useConversationStore } from "@/ai/stores/conversation";

// Mock API
vi.mock("@/ai/api/conversation", () => ({
  getConversations: vi.fn(() =>
    Promise.resolve([
      {
        id: "conv-1",
        title: "会话1",
        createdAt: "2025-01-01T00:00:00Z",
        updatedAt: "2025-01-01T00:00:00Z",
        messageCount: 5,
      },
      {
        id: "conv-2",
        title: "会话2",
        createdAt: "2025-01-02T00:00:00Z",
        updatedAt: "2025-01-02T00:00:00Z",
        messageCount: 3,
      },
    ])
  ),
  getConversation: vi.fn((id: string) =>
    Promise.resolve({
      id,
      title: "会话详情",
      createdAt: "2025-01-01T00:00:00Z",
      updatedAt: "2025-01-01T00:00:00Z",
      messageCount: 5,
    })
  ),
  createConversation: vi.fn((params?: { title?: string }) =>
    Promise.resolve({
      id: "conv-new",
      title: params?.title || "新会话",
      createdAt: "2025-01-03T00:00:00Z",
      updatedAt: "2025-01-03T00:00:00Z",
      messageCount: 0,
    })
  ),
  updateConversation: vi.fn((id: string, params: { title?: string }) =>
    Promise.resolve({
      id,
      title: params.title || "更新后的会话",
      createdAt: "2025-01-01T00:00:00Z",
      updatedAt: "2025-01-03T00:00:00Z",
      messageCount: 5,
    })
  ),
  deleteConversation: vi.fn(() => Promise.resolve()),
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

  describe("addConversation", () => {
    it("创建新会话并设为活跃", async () => {
      const store = useConversationStore();

      const conversation = await store.addConversation();

      expect(conversation.id).toBe("conv-new");
      expect(store.conversations).toHaveLength(1);
      expect(store.conversations[0].id).toBe("conv-new");
      expect(store.activeConversation?.id).toBe("conv-new");
    });

    it("创建新会话并添加到列表开头", async () => {
      const store = useConversationStore();
      await store.fetchConversations();

      await store.addConversation({ title: "自定义标题" });

      expect(store.conversations).toHaveLength(3);
      expect(store.conversations[0].id).toBe("conv-new");
    });

    it("使用自定义标题创建会话", async () => {
      const store = useConversationStore();

      await store.addConversation({ title: "我的新会话" });

      expect(store.conversations[0].title).toBe("我的新会话");
    });
  });

  describe("editConversation", () => {
    it("更新会话标题", async () => {
      const store = useConversationStore();
      await store.fetchConversations();

      const updated = await store.editConversation("conv-1", { title: "新标题" });

      expect(updated.title).toBe("新标题");
      expect(store.conversations[0].title).toBe("新标题");
    });

    it("更新当前活跃会话时同步更新", async () => {
      const store = useConversationStore();
      await store.fetchConversations();
      store.selectConversation(store.conversations[0]);

      await store.editConversation("conv-1", { title: "更新标题" });

      expect(store.activeConversation?.title).toBe("更新标题");
    });

    it("更新非活跃会话不影响活跃会话", async () => {
      const store = useConversationStore();
      await store.fetchConversations();
      store.selectConversation(store.conversations[0]);

      await store.editConversation("conv-2", { title: "更新会话2" });

      expect(store.activeConversation?.id).toBe("conv-1");
      expect(store.conversations[1].title).toBe("更新会话2");
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
