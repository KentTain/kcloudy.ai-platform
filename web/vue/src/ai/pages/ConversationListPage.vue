<script setup lang="ts">
/**
 * 会话列表页面
 *
 * 展示用户的历史会话列表，支持切换会话和删除会话
 */
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import AppPage from "@/framework/layouts/components/AppPage.vue";
import { Button } from "@/components";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components";
import { useConversationStore } from "@/ai/stores";
import { MessageSquare, Trash2, Plus, Loader2 } from "lucide-vue-next";
import type { Conversation } from "@/ai/types";

const router = useRouter();
const conversationStore = useConversationStore();

// 删除确认弹窗状态
const deleteDialogOpen = ref(false);
const conversationToDelete = ref<Conversation | null>(null);
const deleteLoading = ref(false);

// 加载会话列表
onMounted(async () => {
  await conversationStore.fetchConversations();
});

// 切换会话 - 跳转到对话页面
const handleSelectConversation = (conversation: Conversation) => {
  conversationStore.selectConversation(conversation);
  router.push({ name: "AIChat", query: { conversationId: conversation.id } });
};

// 开始新对话
const handleNewChat = () => {
  conversationStore.selectConversation(null);
  router.push({ name: "AIChat" });
};

// 打开删除确认弹窗
const handleDeleteClick = (conversation: Conversation) => {
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
  } catch (error) {
    console.error("删除会话失败:", error);
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
</script>

<template>
  <AppPage title="会话列表" description="管理您的对话历史">
    <div class="flex h-full flex-col">
      <!-- 顶部操作栏 -->
      <div class="mb-4 flex items-center justify-between">
        <div class="text-sm text-muted-foreground">
          共 {{ conversationStore.conversations.length }} 个会话
        </div>
        <Button @click="handleNewChat">
          <Plus class="mr-1 size-4" />
          新对话
        </Button>
      </div>

      <!-- 加载状态 -->
      <div
        v-if="conversationStore.loading"
        class="flex flex-1 items-center justify-center"
      >
        <Loader2 class="size-8 animate-spin text-muted-foreground" />
      </div>

      <!-- 空状态 -->
      <div
        v-else-if="conversationStore.conversations.length === 0"
        class="flex flex-1 flex-col items-center justify-center gap-4 text-muted-foreground"
      >
        <MessageSquare class="size-16 opacity-50" />
        <div class="text-lg font-medium">暂无会话记录</div>
        <div class="text-sm">开始您的第一次对话吧</div>
        <Button variant="outline" @click="handleNewChat">
          <Plus class="mr-1 size-4" />
          开始新对话
        </Button>
      </div>

      <!-- 会话列表 -->
      <div v-else class="flex-1 overflow-y-auto">
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="conversation in conversationStore.conversations"
            :key="conversation.id"
            class="group relative cursor-pointer rounded-lg border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-accent"
            data-testid="conversation-item"
            @click="handleSelectConversation(conversation)"
          >
            <!-- 会话标题 -->
            <div class="mb-2 flex items-start justify-between gap-2">
              <div class="flex-1 truncate font-medium">
                {{ conversation.title }}
              </div>
              <!-- 删除按钮 -->
              <Button
                variant="ghost"
                size="icon"
                class="size-8 shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
                data-testid="delete-conversation"
                @click.stop="handleDeleteClick(conversation)"
              >
                <Trash2 class="size-4 text-muted-foreground hover:text-destructive" />
              </Button>
            </div>

            <!-- 会话信息 -->
            <div class="flex items-center gap-3 text-sm text-muted-foreground">
              <span class="flex items-center gap-1">
                <MessageSquare class="size-3" />
                {{ conversation.messageCount ?? 0 }} 条消息
              </span>
              <span>{{ formatDate(conversation.createdAt) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误提示 -->
      <div
        v-if="conversationStore.error"
        class="mt-4 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
      >
        {{ conversationStore.error }}
      </div>
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
