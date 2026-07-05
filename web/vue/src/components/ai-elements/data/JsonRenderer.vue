<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  content: any
}
const props = defineProps<Props>()

const formattedJson = computed(() => {
  return JSON.stringify(props.content, null, 2)
})
</script>

<template>
  <div class="rounded-lg border bg-muted/30 p-4">
    <pre class="text-xs overflow-x-auto">{{ formattedJson }}</pre>
  </div>
</template>
