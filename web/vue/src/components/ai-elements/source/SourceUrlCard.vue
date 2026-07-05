<script setup lang="ts">
interface Props {
  sourceId: string
  url: string
  title?: string
}
defineProps<Props>()
</script>

<template>
  <a
    :href="url"
    target="_blank"
    rel="noopener noreferrer"
    class="flex items-center gap-3 rounded-lg border p-3 hover:bg-muted/50 transition-colors"
  >
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">{{ title || url }}</div>
      <div v-if="title" class="text-xs text-muted-foreground truncate">{{ url }}</div>
    </div>
  </a>
</template>
