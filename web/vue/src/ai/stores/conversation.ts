/**
 * 会话状态管理
 *
 * 管理会话列表、当前会话和当前选择的模型
 */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import {
  createConversation,
  deleteConversation,
  getConversations,
  updateConversation,
} from "@/ai/api/conversation";
import type { CreateConversationParams, UpdateConversationParams } from "@/ai/api/conversation";
import type { Conversation, ModelConfig } from "@/ai/types";

/**
 * 默认模型配置
 */
const DEFAULT_MODEL: ModelConfig = {
  provider: "openai",
  name: "gpt-4o-mini",
};

/**
 * 会话状态管理 Store
 */
export const useConversationStore = defineStore("conversation", () => {
  // 会话列表
  const conversations = ref<Conversation[]>([]);
  // 当前活跃会话
  const activeConversation = ref<Conversation | null>(null);
  // 当前选择的模型
  const currentModel = ref<ModelConfig>({ ...DEFAULT_MODEL });
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
      conversations.value = await getConversations();
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
   * 创建新会话
   */
  const addConversation = async (params?: CreateConversationParams) => {
    const conversation = await createConversation(params);
    conversations.value.unshift(conversation);
    activeConversation.value = conversation;
    return conversation;
  };

  /**
   * 更新会话
   */
  const editConversation = async (id: string, params: UpdateConversationParams) => {
    const conversation = await updateConversation(id, params);
    const index = conversations.value.findIndex((c) => c.id === id);
    if (index !== -1) {
      conversations.value[index] = conversation;
    }
    // 更新当前活跃会话
    if (activeConversation.value?.id === id) {
      activeConversation.value = conversation;
    }
    return conversation;
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
  };

  /**
   * 重置为默认模型
   */
  const resetModel = () => {
    currentModel.value = { ...DEFAULT_MODEL };
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
    addConversation,
    editConversation,
    removeConversation,
    setModel,
    resetModel,
    clearError,
  };
});

export default useConversationStore;
