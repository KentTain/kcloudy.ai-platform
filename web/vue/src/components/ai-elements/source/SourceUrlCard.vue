<script setup lang="ts">
import { GlobeIcon, ExternalLinkIcon, EyeIcon } from 'lucide-vue-next'
import { Button } from '@/components'

interface Props {
  sourceId: string
  url: string
  title?: string
}
const props = defineProps<Props>()

const handleClick = () => {
  // 记录点击行为（可以发送到元数据系统）
  console.log('Source clicked:', props.sourceId)

  // 跳转到新标签页
  window.open(props.url, '_blank')
}

const handlePreview = (event: Event) => {
  event.stopPropagation()
  // 触发预览弹窗（简化实现）
  alert('预览功能：' + props.url)
}
</script>

<template>
  <div
    class="source-card group flex items-center gap-3 rounded-lg border p-3 hover:bg-muted/50 transition-colors cursor-pointer"
    @click="handleClick"
  >
    <GlobeIcon class="size-5 text-muted-foreground flex-shrink-0" />

    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">
        {{ title || url }}
      </div>
      <div v-if="title" class="text-xs text-muted-foreground truncate">
        {{ url }}
      </div>
    </div>

    <!-- 预览按钮 -->
    <Button
      variant="ghost"
      size="sm"
      data-testid="preview-button"
      class="opacity-0 group-hover:opacity-100 transition-opacity"
      @click="handlePreview"
    >
      <EyeIcon class="size-4" />
    </Button>

    <ExternalLinkIcon class="size-4 text-muted-foreground flex-shrink-0" />
  </div>
</template>
