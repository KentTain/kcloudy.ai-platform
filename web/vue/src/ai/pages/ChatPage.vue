<script setup lang="ts">
/**
 * AI 对话页面
 *
 * 使用 Vercel AI SDK 协议与后端通信
 * 集成 ai-elements 组件构建对话界面
 */
import { computed, ref, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Conversation } from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageActions, MessageAction } from "@/components/ai-elements/message";
import { PromptInput, PromptInputTextarea, PromptInputSubmit } from "@/components/ai-elements/prompt-input";
import { MessageResponse } from "@/components/ai-elements/message";
import { useChat } from "@/ai/composables";
import { useConversationStore } from "@/ai/stores";
import { RotateCcw, Square, Trash2, List } from "lucide-vue-next";
import { Button } from "@/components";
import ToolCallItem from "@/ai/components/ToolCallItem.vue";
import AiModelSelector from "@/ai/components/AiModelSelector.vue";
import type { UIMessagePart, ToolCallPart, ToolResultPart } from "@/ai/types";
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
      // 重置聊天状态并加载新会话
      reload();
    } else if (!newId && activeConversationId.value) {
      // 清空会话
      activeConversationId.value = undefined;
      reload();
    }
  },
  { immediate: true }
);

// 页面加载时，如果有 conversationId，设置到 store
onMounted(async () => {
  if (conversationIdFromQuery.value) {
    // 确保 conversations 已加载
    if (conversationStore.conversations.length === 0) {
      await conversationStore.fetchConversations();
    }
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

  // 返回合并后的列表
  // 如果同时有 call 和 result，优先返回 call（包含 args），但状态由 result 决定
  const merged: (ToolCallPart | ToolResultPart)[] = [];
  for (const [, data] of toolCallMap) {
    if (data.call && data.result) {
      // 合并：使用 call 的 args 和 result 的结果
      // 创建一个扩展的 tool-call 部分，包含 result 信息
      merged.push({
        ...data.call,
        // @ts-expect-error 扩展字段用于传递 result
        _result: data.result.result,
      });
    } else if (data.result) {
      // 只有 result
      merged.push(data.result);
    } else if (data.call) {
      // 只有 call（还在执行中）
      merged.push(data.call);
    }
  }

  return merged;
};
</script>

<template>
  <AppPage title="AI 对话" variant="workbench" description="与 AI 助手进行对话">
    <div class="flex h-full flex-col">
      <!-- 对话区域 -->
      <Conversation class="flex-1 rounded-lg border bg-background p-4">
        <!-- 空状态 -->
        <div
          v-if="messages.length === 0"
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
              <AiModelSelector />
            </div>
            <div class="flex items-center gap-1">
              <!-- 会话列表按钮 -->
              <Button
                variant="ghost"
                size="icon"
                class="size-8"
                title="会话列表"
                @click="router.push({ name: 'ConversationList' })"
              >
                <List class="size-4" />
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
  </AppPage>
</template>
