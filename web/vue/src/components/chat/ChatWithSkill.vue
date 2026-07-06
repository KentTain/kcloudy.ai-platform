<script setup lang="ts">
import { ref } from 'vue';
import { Button } from '@/components';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Wand2, Send, Loader2 } from 'lucide-vue-next';
import SkillInvocationPanel from '@/ai/components/SkillInvocationPanel.vue';
import { notifyError } from '@/framework/utils/feedback';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  skill_ids?: string[];
}

interface Props {
  conversationId: string;
}

const props = defineProps<Props>();

const messages = ref<Message[]>([]);
const inputMessage = ref('');
const sending = ref(false);
const showSkillPanel = ref(false);

const handleSend = async () => {
  if (!inputMessage.value.trim() || sending.value) return;

  const userMessage = inputMessage.value;
  inputMessage.value = '';

  // 添加用户消息
  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: userMessage,
  });

  sending.value = true;

  // 添加助手消息占位
  const assistantMessage: Message = {
    id: (Date.now() + 1).toString(),
    role: 'assistant',
    content: '',
  };
  messages.value.push(assistantMessage);

  // 调用普通对话 API（非 Skill）
  try {
    const response = await fetch('/ai/console/v1/chat-messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: props.conversationId,
        message: userMessage,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      assistantMessage.content = data.data?.content || data.data?.message || '响应为空';
    } else {
      // 移除占位消息
      const index = messages.value.indexOf(assistantMessage);
      if (index > -1) {
        messages.value.splice(index, 1);
      }
      notifyError('发送消息失败');
    }
  } catch (error) {
    // 移除占位消息
    const index = messages.value.indexOf(assistantMessage);
    if (index > -1) {
      messages.value.splice(index, 1);
    }
    notifyError('网络错误');
  } finally {
    sending.value = false;
  }
};

const handleSkillInvoked = (message: string) => {
  // 添加 Skill 调用结果为助手消息
  messages.value.push({
    id: Date.now().toString(),
    role: 'assistant',
    content: message,
    skill_ids: [],
  });
  showSkillPanel.value = false;
};
</script>

<template>
  <div class="flex h-full">
    <!-- 主聊天区域 -->
    <div class="flex flex-1 flex-col">
      <!-- 消息列表 -->
      <ScrollArea class="flex-1 p-4">
        <div class="space-y-4">
          <div
            v-for="message in messages"
            :key="message.id"
            class="flex"
            :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div
              class="max-w-[80%] rounded-lg p-3"
              :class="
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              "
            >
              <p class="whitespace-pre-wrap text-sm">{{ message.content }}</p>
            </div>
          </div>
          <div v-if="sending" class="flex justify-start">
            <div class="rounded-lg bg-muted p-3">
              <Loader2 class="h-4 w-4 animate-spin" />
            </div>
          </div>
        </div>
      </ScrollArea>

      <!-- 输入区域 -->
      <div class="border-t p-4">
        <div class="mb-2 flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            :class="{ 'bg-accent': showSkillPanel }"
            @click="showSkillPanel = !showSkillPanel"
          >
            <Wand2 class="mr-1 h-4 w-4" />
            Skills
          </Button>
        </div>

        <div class="flex gap-2">
          <Input
            v-model="inputMessage"
            placeholder="输入消息或使用 Skill..."
            :disabled="sending"
            @keydown.enter="handleSend"
          />
          <Button :disabled="!inputMessage.trim() || sending" @click="handleSend">
            <Send class="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>

    <!-- Skill 调用面板 -->
    <div v-if="showSkillPanel" class="w-96">
      <SkillInvocationPanel
        :conversation-id="conversationId"
        @invoked="handleSkillInvoked"
        @close="showSkillPanel = false"
      />
    </div>
  </div>
</template>
