<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  mediaType: string
  url: string
  filename?: string
  size?: number
}

const props = defineProps<Props>()

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

const displaySize = computed(() => {
  return props.size ? formatSize(props.size) : ''
})

const handlePreview = () => {
  window.open(props.url, '_blank')
}
</script>

<template>
  <div class="flex items-center gap-3 rounded-lg border p-3">
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">{{ filename || 'File' }}</div>
      <div class="text-xs text-muted-foreground flex items-center gap-2">
        <span>{{ mediaType }}</span>
        <span v-if="displaySize">• {{ displaySize }}</span>
      </div>
    </div>
    <button class="text-sm text-primary hover:underline" data-testid="file-link" @click="handlePreview">预览</button>
  </div>
</template>
