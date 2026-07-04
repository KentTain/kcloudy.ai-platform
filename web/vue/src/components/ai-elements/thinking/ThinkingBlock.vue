<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'
import { useVModel } from '@vueuse/core'
import { BrainIcon, ChevronDownIcon } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import { Markdown } from 'vue-stream-markdown'
import type { ReasoningStepType } from '@/ai/types'
import 'vue-stream-markdown/index.css'

interface Props {
  class?: HTMLAttributes['class']
  thinking: string
  title?: string
  stepType?: ReasoningStepType
  open?: boolean
  defaultOpen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  defaultOpen: false,
  stepType: 'reasoning',
})

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
}>()

const isOpen = useVModel(props, 'open', emit, {
  defaultValue: props.defaultOpen,
  passive: true,
})

// 步骤类型颜色映射
const stepTypeColors: Record<ReasoningStepType, { bg: string, text: string, icon: string }> = {
  reasoning: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-600 dark:text-blue-400',
    icon: 'text-blue-500',
  },
  decision: {
    bg: 'bg-purple-500/10',
    text: 'text-purple-600 dark:text-purple-400',
    icon: 'text-purple-500',
  },
  tool_selection: {
    bg: 'bg-orange-500/10',
    text: 'text-orange-600 dark:text-orange-400',
    icon: 'text-orange-500',
  },
  tool_execution: {
    bg: 'bg-green-500/10',
    text: 'text-green-600 dark:text-green-400',
    icon: 'text-green-500',
  },
  result_analysis: {
    bg: 'bg-cyan-500/10',
    text: 'text-cyan-600 dark:text-cyan-400',
    icon: 'text-cyan-500',
  },
  error_handling: {
    bg: 'bg-red-500/10',
    text: 'text-red-600 dark:text-red-400',
    icon: 'text-red-500',
  },
}

const colors = computed(() => stepTypeColors[props.stepType])

// 步骤类型显示名称
const stepTypeLabels: Record<ReasoningStepType, string> = {
  reasoning: '推理',
  decision: '决策',
  tool_selection: '工具选择',
  tool_execution: '工具执行',
  result_analysis: '结果分析',
  error_handling: '错误处理',
}

const stepLabel = computed(() => stepTypeLabels[props.stepType])

// 内容长度限制（10k 字符）
const MAX_THINKING_LENGTH = 10000
const displayContent = computed(() => {
  if (props.thinking.length > MAX_THINKING_LENGTH) {
    return props.thinking.substring(0, MAX_THINKING_LENGTH) + '...(内容过长已截断)'
  }
  return props.thinking
})
</script>

<template>
  <Collapsible
    v-model:open="isOpen"
    :class="cn('not-prose mb-4', props.class)"
  >
    <CollapsibleTrigger
      :class="cn(
        'flex w-full items-center gap-2 text-sm transition-colors hover:text-foreground rounded-lg px-3 py-2',
        colors.bg,
        colors.text,
      )"
    >
      <BrainIcon :class="cn('size-4', colors.icon)" />

      <div class="flex flex-1 items-center gap-2">
        <span class="font-medium">{{ title || stepLabel }}</span>
        <span class="text-muted-foreground text-xs">({{ thinking.length }} 字符)</span>
      </div>

      <ChevronDownIcon
        :class="cn(
          'size-4 transition-transform',
          isOpen ? 'rotate-180' : 'rotate-0',
        )"
      />
    </CollapsibleTrigger>

    <CollapsibleContent
      :class="cn(
        'mt-2 text-sm text-muted-foreground',
        'data-[state=closed]:fade-out-0 data-[state=closed]:slide-out-to-top-2',
        'data-[state=open]:slide-in-from-top-2',
        'outline-none data-[state=closed]:animate-out data-[state=open]:animate-in',
        'border-l-2 pl-4 ml-2',
        colors.icon.replace('text-', 'border-'),
      )"
    >
      <Markdown :content="displayContent" />
    </CollapsibleContent>
  </Collapsible>
</template>
