<script setup lang="ts">
import type { DataPart } from '@/ai/types'
import TableRenderer from './TableRenderer.vue'
import JsonRenderer from './JsonRenderer.vue'

interface Props {
  part: DataPart
}
defineProps<Props>()
</script>

<template>
  <TableRenderer
    v-if="part.type === 'table'"
    :content="part.content"
  />
  <JsonRenderer
    v-else-if="part.type === 'json'"
    :content="part.content"
  />
</template>
