/**
 * 会话状态管理
 *
 * 管理会话列表、当前会话和当前选择的模型
 */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { deleteConversation, getConversations } from "@/ai/api/conversation";
import type { ConversationListItem } from "@/ai/api/conversation";
import type { Conversation, ModelConfig } from "@/ai/types";

/**
 * 将 ConversationListItem 转换为 Conversation
 */
const toItem = (item: ConversationListItem): Conversation => ({
  id: item.id,
  title: item.name,
  createdAt: new Date(item.created_at),
  updatedAt: new Date(item.created_at),
  messageCount: item.message_count,
});

/**
 * 默认模型配置
 */
const DEFAULT_MODEL: ModelConfig = {
  provider: "openai",
  name: "gpt-4o-mini",
};

/**
 * localStorage 存储键
 */
const STORAGE_KEY = "selected_model";

/**
 * 会话状态管理 Store
 */
export const useConversationStore = defineStore("conversation", () => {
  // 会话列表
  const conversations = ref<Conversation[]>([]);
  // 当前活跃会话
  const activeConversation = ref<Conversation | null>(null);
  // 当前选择的模型（从 localStorage 恢复）
  const currentModel = ref<ModelConfig>(
    JSON.parse(localStorage.getItem(STORAGE_KEY) || "null") ?? { ...DEFAULT_MODEL }
  );
  // 加载状态
  const loading = ref(false);
  // 错误信息
  const error = ref<string | null>(null);

  // 当前会话 ID
  const activeConversationId = computed(() => activeConversation.value?.id ?? null);

  // 是否有待处理的请求
  const isPending = computed(() => loading.value);

  /**
   * 获取会话列表
   */
  const fetchConversations = async () => {
    loading.value = true;
    error.value = null;

    try {
      const response = await getConversations();
      conversations.value = response.conversations.map(toItem);
    } catch (e) {
      error.value = e instanceof Error ? e.message : "获取会话列表失败";
    } finally {
      loading.value = false;
    }
  };

  /**
   * 选择会话
   */
  const selectConversation = (conversation: Conversation | null) => {
    activeConversation.value = conversation;
  };

  /**
   * 选择会话（通过 ID）
   */
  const selectConversationById = (id: string | null) => {
    if (!id) {
      activeConversation.value = null;
      return;
    }
    const conversation = conversations.value.find((c) => c.id === id);
    activeConversation.value = conversation ?? null;
  };

  /**
   * 删除会话
   */
  const removeConversation = async (id: string) => {
    await deleteConversation(id);
    conversations.value = conversations.value.filter((c) => c.id !== id);
    // 如果删除的是当前会话，清空活跃会话
    if (activeConversation.value?.id === id) {
      activeConversation.value = null;
    }
  };

  /**
   * 设置当前模型
   */
  const setModel = (model: ModelConfig) => {
    currentModel.value = model;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(model));
  };

  /**
   * 重置为默认模型
   */
  const resetModel = () => {
    currentModel.value = { ...DEFAULT_MODEL };
    localStorage.removeItem(STORAGE_KEY);
  };

  /**
   * 清空错误
   */
  const clearError = () => {
    error.value = null;
  };

  return {
    // 状态
    conversations,
    activeConversation,
    activeConversationId,
    currentModel,
    loading,
    isPending,
    error,

    // 方法
    fetchConversations,
    selectConversation,
    selectConversationById,
    removeConversation,
    setModel,
    resetModel,
    clearError,
  };
});

export default useConversationStore;
