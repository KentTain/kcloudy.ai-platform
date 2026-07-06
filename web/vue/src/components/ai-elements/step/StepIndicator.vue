<!-- src/components/ai-elements/step/StepIndicator.vue -->
<script setup lang="ts">
import { CheckIcon, LoaderIcon } from 'lucide-vue-next'

interface Step {
  title: string
  description?: string
  status: 'pending' | 'active' | 'done'
}

defineProps<{
  steps: Step[]
}>()
</script>

<template>
  <div class="space-y-3">
    <div
      v-for="(step, index) in steps"
      :key="index"
      class="step-item flex items-start gap-3"
    >
      <!-- 步骤图标 -->
      <div
        class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
        :class="{
          'bg-primary text-primary-foreground': step.status === 'active',
          'bg-green-500 text-white': step.status === 'done',
          'bg-muted text-muted-foreground': step.status === 'pending',
        }"
      >
        <CheckIcon v-if="step.status === 'done'" class="check-icon size-5" />
        <LoaderIcon v-else-if="step.status === 'active'" class="spinner-icon size-5 animate-spin" />
        <span v-else class="text-sm font-medium">{{ index + 1 }}</span>
      </div>

      <!-- 步骤内容 -->
      <div class="flex-1 min-w-0">
        <div class="text-sm font-medium">{{ step.title }}</div>
        <div v-if="step.description" class="mt-0.5 text-xs text-muted-foreground">
          {{ step.description }}
        </div>
      </div>
    </div>
  </div>
</template>
