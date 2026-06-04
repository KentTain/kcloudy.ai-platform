<script setup lang="ts">
/**
 * AI 对话页面
 *
 * 使用 Vercel AI SDK 协议与后端通信
 * 集成 ai-elements 组件构建对话界面
 */
import { computed, ref, watch } from "vue";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Conversation } from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageActions, MessageAction } from "@/components/ai-elements/message";
import { PromptInput, PromptInputTextarea, PromptInputSubmit } from "@/components/ai-elements/prompt-input";
import { MessageResponse } from "@/components/ai-elements/message";
import { useChat } from "@/ai/composables";
import { useConversationStore } from "@/ai/stores";
import { RotateCcw, Square, Trash2 } from "lucide-vue-next";
import { Button } from "@/components/ui/button";

// 会话 Store
const conversationStore = useConversationStore();

// 当前模型配置（响应式）
const currentModel = computed(() => conversationStore.currentModel);

// 使用 useChat composable
const { messages, isLoading, error, sendMessage, stop, regenerate, setInput, reload } = useChat({
  api: "/api/v1/chat-messages",
  model: currentModel,
  onError: (err) => {
    console.error("Chat error:", err);
  },
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
            <Message :from="message.role">
              <MessageContent>
                <MessageResponse :content="getTextFromParts(message.parts)" />
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
          />
          <div class="flex items-center justify-between gap-2 border-t p-2">
            <div class="flex items-center gap-1">
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
              />
            </div>
          </div>
        </PromptInput>
      </div>
    </div>
  </AppPage>
</template>
