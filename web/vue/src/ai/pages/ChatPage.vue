<script setup lang="ts">
/**
 * AI 对话页面
 *
 * 使用 Vercel AI SDK 协议与后端通信
 * 集成 ai-elements 组件构建对话界面
 * 右侧集成可伸缩会话列表
 */
import { computed, ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Conversation } from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageActions, MessageAction } from "@/components/ai-elements/message";
import { PromptInput, PromptInputTextarea, PromptInputSubmit } from "@/components/ai-elements/prompt-input";
import { MessageResponse } from "@/components/ai-elements/message";
import { ThinkingBlock } from "@/components/ai-elements/thinking";
import { MessageFeedback } from "@/components/ai-elements/metadata";
import { FilePreview } from "@/components/ai-elements/file";
import { useChat } from "@/ai/composables";
import { useConversationStore } from "@/ai/stores";
import { RotateCcw, Square, Trash2, PanelRight, Plus, Loader2 } from "lucide-vue-next";
import { Button } from "@/components";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components";
import ToolCallItem from "@/ai/components/ToolCallItem.vue";
import AiModelSelector from "@/ai/components/AiModelSelector.vue";
import type { UIMessagePart, ToolCallPart, ToolResultPart, ThinkingPart } from "@/ai/types";
import type { Conversation as ConversationType } from "@/ai/types";
import { notifyError, getErrorMessage } from "@/framework/utils/feedback";

const route = useRoute();
const router = useRouter();

// 会话 Store
const conversationStore = useConversationStore();

// 从 query 参数获取会话 ID
const conversationIdFromQuery = computed(() => route.query.conversationId as string | undefined);

// 当前模型配置（响应式）
const currentModel = computed(() => conversationStore.currentModel);

// 当前会话 ID（响应式）
const activeConversationId = ref<string | undefined>(undefined);

// 右侧会话列表面板状态
const panelOpen = ref(true);

// 删除确认弹窗状态
const deleteDialogOpen = ref(false);
const conversationToDelete = ref<ConversationType | null>(null);
const deleteLoading = ref(false);

// 文件预览状态
const previewFile = ref<{
  mediaType: string;
  url: string;
  filename?: string;
} | null>(null);

// 使用 useChat composable
const { messages, isLoading, error, sendMessage, stop, regenerate, setInput, reload } = useChat({
  api: "/api/ai/console/v1/chat-messages",
  id: activeConversationId,
  model: currentModel,
  onError: (err) => {
    notifyError(getErrorMessage(err, "对话发生错误"));
  },
});

// 监听 query 参数变化，切换会话
watch(
  conversationIdFromQuery,
  (newId) => {
    if (newId && newId !== activeConversationId.value) {
      activeConversationId.value = newId;
      reload();
    } else if (!newId && activeConversationId.value) {
      activeConversationId.value = undefined;
      reload();
    }
  },
  { immediate: true }
);

// 页面加载时，加载会话列表并选中当前会话
onMounted(async () => {
  if (conversationStore.conversations.length === 0) {
    await conversationStore.fetchConversations();
  }
  if (conversationIdFromQuery.value) {
    conversationStore.selectConversationById(conversationIdFromQuery.value);
    activeConversationId.value = conversationIdFromQuery.value;
  }
});

// 本地输入状态（与 PromptInput 绑定）
const localInput = ref("");

// 同步本地输入到 useChat 的 input
watch(localInput, (value) => {
  setInput(value);
});

// 发送消息
const handleSubmit = async () => {
  const text = localInput.value.trim();
  if (!text || isLoading.value) return;

  localInput.value = "";
  await sendMessage(text);
};

// 停止生成
const handleStop = async () => {
  await stop();
};

// 重新生成最后一条消息
const handleRegenerate = async () => {
  if (messages.value.length > 0 && !isLoading.value) {
    const lastMessage = messages.value[messages.value.length - 1];
    if (lastMessage.role === "assistant") {
      await regenerate(lastMessage.id);
    }
  }
};

// 清空对话
const handleClear = () => {
  reload();
};

// 切换会话列表面板
const togglePanel = () => {
  panelOpen.value = !panelOpen.value;
};

// 选择会话
const handleSelectConversation = (conversation: ConversationType) => {
  conversationStore.selectConversation(conversation);
  router.push({ name: "AIChat", query: { conversationId: conversation.id } });
};

// 开始新对话
const handleNewChat = () => {
  conversationStore.selectConversation(null);
  router.push({ name: "AIChat" });
};

// 打开删除确认弹窗
const handleDeleteClick = (conversation: ConversationType) => {
  conversationToDelete.value = conversation;
  deleteDialogOpen.value = true;
};

// 确认删除会话
const handleConfirmDelete = async () => {
  if (!conversationToDelete.value) return;

  deleteLoading.value = true;
  try {
    await conversationStore.removeConversation(conversationToDelete.value.id);
    deleteDialogOpen.value = false;
    conversationToDelete.value = null;
    if (conversationStore.activeConversationId === null) {
      activeConversationId.value = undefined;
      reload();
    }
  } catch (error) {
    notifyError(getErrorMessage(error, "删除会话失败"));
  } finally {
    deleteLoading.value = false;
  }
};

// 格式化日期
const formatDate = (date: Date): string => {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } else if (days === 1) {
    return "昨天";
  } else if (days < 7) {
    return `${days} 天前`;
  } else {
    return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
  }
};

// 判断会话是否为当前活跃会话
const isActiveConversation = (conversation: ConversationType): boolean => {
  return conversation.id === activeConversationId.value;
};

// 从消息部分提取文本内容
const getTextFromParts = (parts: Array<{ type: string; text?: string }>): string => {
  return parts
    .filter((p) => p.type === "text")
    .map((p) => p.text ?? "")
    .join("");
};

// 检查是否有工具调用部分
const hasToolParts = (parts: UIMessagePart[]): boolean => {
  return parts.some((p) => p.type === "tool-call" || p.type === "tool-result");
};

// 从消息部分提取文本部分
const getTextParts = (parts: UIMessagePart[]): Array<{ type: string; text?: string }> => {
  return parts.filter((p) => p.type === "text");
};

// 从消息部分提取工具调用部分
const getToolParts = (parts: UIMessagePart[]): (ToolCallPart | ToolResultPart)[] => {
  return parts.filter((p) => p.type === "tool-call" || p.type === "tool-result") as (ToolCallPart | ToolResultPart)[];
};

// 从消息部分提取思考部分
const getThinkingParts = (parts: UIMessagePart[]): ThinkingPart[] => {
  return parts.filter((p) => p.type === "thinking") as ThinkingPart[];
};

// 合并工具调用和工具结果（按 toolCallId 配对）
const mergeToolParts = (parts: (ToolCallPart | ToolResultPart)[]): (ToolCallPart | ToolResultPart)[] => {
  const toolCallMap = new Map<string, { call?: ToolCallPart; result?: ToolResultPart }>();

  for (const part of parts) {
    const id = part.toolCallId;
    const existing = toolCallMap.get(id) || {};

    if (part.type === "tool-call") {
      existing.call = part;
    } else if (part.type === "tool-result") {
      existing.result = part;
    }

    toolCallMap.set(id, existing);
  }

  const merged: (ToolCallPart | ToolResultPart)[] = [];
  for (const [, data] of toolCallMap) {
    if (data.call && data.result) {
      merged.push({
        ...data.call,
        // @ts-expect-error 扩展字段用于传递 result
        _result: data.result.result,
      });
    } else if (data.result) {
      merged.push(data.result);
    } else if (data.call) {
      merged.push(data.call);
    }
  }

  return merged;
};
</script>

<template>
  <AppPage title="AI 对话" variant="workbench" description="与 AI 助手进行对话">
    <div class="flex h-full gap-4">
      <!-- 左侧：对话区域 -->
      <div class="flex min-w-0 flex-1 flex-col">
        <Conversation class="flex-1 rounded-lg border bg-background p-4">
          <!-- 空状态 -->
          <div
            v-if="messages.length === 0"
            data-testid="empty-state"
            class="flex h-full flex-col items-center justify-center gap-4 text-muted-foreground"
          >
            <div class="text-4xl">💬</div>
            <div class="text-lg font-medium">开始对话</div>
            <div class="text-sm">在下方输入您的问题，AI 助手将为您解答</div>
          </div>

          <!-- 消息列表 -->
          <div v-else class="flex flex-col gap-4 pb-4">
            <template v-for="message in messages" :key="message.id">
              <Message :from="message.role" :data-testid="message.role === 'user' ? 'user-message' : 'assistant-message'">
                <MessageContent>
                  <!-- 思考过程展示（仅在 assistant 消息中显示） -->
                  <template v-if="message.role === 'assistant' && getThinkingParts(message.parts).length > 0">
                    <ThinkingBlock
                      v-for="(thinkingPart, index) in getThinkingParts(message.parts)"
                      :key="index"
                      :thinking="thinkingPart.thinking"
                      :title="thinkingPart.title"
                      :step-type="thinkingPart.stepType"
                    />
                  </template>
                  <!-- 工具调用展示（仅在 assistant 消息中显示） -->
                  <template v-if="message.role === 'assistant' && hasToolParts(message.parts)">
                    <div class="mb-3">
                      <ToolCallItem
                        v-for="toolPart in mergeToolParts(getToolParts(message.parts))"
                        :key="toolPart.toolCallId"
                        :part="toolPart"
                      />
                    </div>
                  </template>
                  <!-- 文本内容 -->
                  <MessageResponse
                    v-if="getTextParts(message.parts).length > 0"
                    :content="getTextFromParts(message.parts)"
                  />
                </MessageContent>
                <MessageActions v-if="message.role === 'assistant'">
                  <!-- 反馈组件 -->
                  <MessageFeedback :message-id="message.id" />

                  <!-- 重新生成按钮 -->
                  <MessageAction tooltip="重新生成" @click="handleRegenerate">
                    <RotateCcw class="size-4" />
                  </MessageAction>
                </MessageActions>
              </Message>
            </template>
          </div>
        </Conversation>

        <!-- 错误提示 -->
        <div
          v-if="error"
          class="mt-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
        >
          {{ error.message }}
        </div>

        <!-- 输入区域 -->
        <div class="mt-4">
          <PromptInput class="rounded-lg border bg-background" @submit="handleSubmit">
            <PromptInputTextarea
              v-model="localInput"
              placeholder="输入您的问题..."
              :disabled="isLoading"
              data-testid="chat-input"
            />
            <div class="flex items-center justify-between gap-2 border-t p-2">
              <div class="flex items-center gap-2">
                <!-- 模型选择器 -->
                <AiModelSelector data-testid="model-selector" />
              </div>
              <div class="flex items-center gap-1">
                <!-- 会话列表面板切换 -->
                <Button
                  variant="ghost"
                  size="icon"
                  class="size-8"
                  data-testid="toggle-panel-btn"
                  :title="panelOpen ? '收起会话列表' : '展开会话列表'"
                  @click="togglePanel"
                >
                  <PanelRight class="size-4" :class="{ 'text-primary': panelOpen }" />
                </Button>
                <!-- 清空按钮 -->
                <Button
                  variant="ghost"
                  size="icon"
                  class="size-8"
                  title="清空对话"
                  :disabled="messages.length === 0 || isLoading"
                  @click="handleClear"
                >
                  <Trash2 class="size-4" />
                </Button>
              </div>
              <div class="flex items-center gap-2">
                <!-- 停止按钮 -->
                <Button
                  v-if="isLoading"
                  variant="secondary"
                  size="sm"
                  data-testid="stop-generate-btn"
                  @click="handleStop"
                >
                  <Square class="mr-1 size-4" />
                  停止
                </Button>
                <!-- 发送按钮 -->
                <PromptInputSubmit
                  :status="isLoading ? 'submitted' : undefined"
                  :disabled="!localInput.trim()"
                  data-testid="send-button"
                />
              </div>
            </div>
          </PromptInput>
        </div>
      </div>

      <!-- 右侧：会话列表面板 -->
      <Transition
        enter-active-class="transition-[width,opacity] duration-200 ease-out"
        leave-active-class="transition-[width,opacity] duration-200 ease-in"
        enter-from-class="!w-0 opacity-0"
        leave-to-class="!w-0 opacity-0"
      >
        <div v-if="panelOpen" class="flex w-72 shrink-0 flex-col overflow-hidden rounded-lg border bg-background">
          <!-- 面板头部（固定不滚动） -->
          <div class="shrink-0 border-b px-3 py-2">
            <span class="text-sm font-medium">会话列表</span>
          </div>
          <!-- 新建会话按钮（固定不滚动） -->
          <div class="shrink-0 border-b px-2 py-1.5">
            <Button variant="ghost" size="sm" class="w-full justify-start gap-2" data-testid="new-chat-btn" @click="handleNewChat">
              <Plus class="size-4" />
              新建会话
            </Button>
          </div>

          <!-- 加载状态 -->
          <div v-if="conversationStore.loading" class="flex flex-1 items-center justify-center py-8">
            <Loader2 class="size-5 animate-spin text-muted-foreground" />
          </div>

          <!-- 空状态 -->
          <div
            v-else-if="conversationStore.conversations.length === 0"
            class="flex flex-1 flex-col items-center justify-center gap-2 py-8 text-muted-foreground"
          >
            <span class="text-sm">暂无会话</span>
          </div>

          <!-- 会话列表 -->
          <div v-else class="flex-1 overflow-y-auto">
            <div
              v-for="conversation in conversationStore.conversations"
              :key="conversation.id"
              class="group flex cursor-pointer items-center justify-between gap-2 border-b px-3 py-2.5 transition-colors last:border-b-0 hover:bg-accent"
              :class="{ 'bg-accent/50': isActiveConversation(conversation) }"
              data-testid="conversation-item"
              @click="handleSelectConversation(conversation)"
            >
              <div class="min-w-0 flex-1">
                <div class="truncate text-sm" :class="{ 'font-medium': isActiveConversation(conversation) }">
                  {{ conversation.title }}
                </div>
                <div class="mt-0.5 text-xs text-muted-foreground">
                  {{ formatDate(conversation.createdAt) }}
                </div>
              </div>
              <!-- 删除按钮 -->
              <Button
                variant="ghost"
                size="icon"
                class="size-6 shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
                data-testid="delete-conversation"
                @click.stop="handleDeleteClick(conversation)"
              >
                <Trash2 class="size-3 text-muted-foreground hover:text-destructive" />
              </Button>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 删除确认弹窗 -->
    <Dialog v-model:open="deleteDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>确认删除</DialogTitle>
          <DialogDescription>
            确定要删除会话「{{ conversationToDelete?.title }}」吗？此操作无法撤销。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" :disabled="deleteLoading" @click="deleteDialogOpen = false">
            取消
          </Button>
          <Button
            variant="destructive"
            :disabled="deleteLoading"
            @click="handleConfirmDelete"
          >
            <Loader2 v-if="deleteLoading" class="mr-2 size-4 animate-spin" />
            删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>
