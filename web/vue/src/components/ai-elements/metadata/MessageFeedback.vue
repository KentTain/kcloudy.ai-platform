<!-- src/components/ai-elements/metadata/MessageFeedback.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { ThumbsUpIcon, ThumbsDownIcon, MessageSquareIcon } from 'lucide-vue-next'
import { Button, Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components'
import { apiClient } from '@/framework/api/client'

const props = defineProps<{
  messageId: string
  rating?: number
  feedback?: string
}>()

const emit = defineEmits<{
  updated: [rating: number, feedback?: string]
}>()

const localRating = ref(props.rating)
const feedbackText = ref(props.feedback || '')
const showFeedbackDialog = ref(false)

const handleRate = async (rating: number) => {
  localRating.value = rating

  await apiClient.post('/ai/console/v1/metadata/feedback', {
    message_id: props.messageId,
    rating,
  })

  emit('updated', rating)
}

const submitFeedback = async () => {
  await apiClient.post('/ai/console/v1/metadata/feedback', {
    message_id: props.messageId,
    rating: localRating.value,
    feedback: feedbackText.value,
  })

  showFeedbackDialog.value = false
  emit('updated', localRating.value!, feedbackText.value)
}
</script>

<template>
  <div class="flex items-center gap-2">
    <!-- 👍 按钮 -->
    <Button
      variant="ghost"
      size="sm"
      data-testid="thumbs-up"
      :class="{ 'text-green-500': localRating === 2 }"
      @click="handleRate(2)"
    >
      <ThumbsUpIcon class="size-4" />
    </Button>

    <!-- 👎 按钮 -->
    <Button
      variant="ghost"
      size="sm"
      data-testid="thumbs-down"
      :class="{ 'text-red-500': localRating === 1 }"
      @click="handleRate(1)"
    >
      <ThumbsDownIcon class="size-4" />
    </Button>

    <!-- 反馈按钮 -->
    <Button
      variant="ghost"
      size="sm"
      data-testid="feedback-button"
      @click="showFeedbackDialog = true"
    >
      <MessageSquareIcon class="size-4" />
    </Button>

    <!-- 反馈弹窗 -->
    <Dialog v-model:open="showFeedbackDialog" data-testid="feedback-dialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>提交反馈</DialogTitle>
          <DialogDescription>
            告诉我们如何改进 AI 的回答
          </DialogDescription>
        </DialogHeader>

        <textarea
          v-model="feedbackText"
          class="w-full h-32 p-3 border rounded-lg resize-none"
          placeholder="请输入您的反馈..."
          maxlength="1000"
        />

        <DialogFooter>
          <Button variant="outline" @click="showFeedbackDialog = false">
            取消
          </Button>
          <Button @click="submitFeedback">
            提交
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
