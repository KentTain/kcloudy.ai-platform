<script setup lang="ts">
interface Props {
  sourceId: string
  mediaType: string
  url: string
  title?: string
}
const props = defineProps<Props>()
const handlePreview = () => {
  window.open(props.url, '_blank')
}
</script>

<template>
  <div class="flex items-center gap-3 rounded-lg border p-3">
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">{{ title || 'Document' }}</div>
      <div class="text-xs text-muted-foreground">{{ mediaType }}</div>
    </div>
    <button class="text-sm text-primary hover:underline" @click="handlePreview">预览</button>
  </div>
</template>
