<script setup lang="ts">
import type { FilePart } from '@/ai/types'
import FileAttachment from './FileAttachment.vue'

interface Props {
  part: FilePart
}
defineProps<Props>()
</script>

<template>
  <FileAttachment
    :media-type="part.mediaType"
    :url="part.url"
    :filename="part.filename"
    :size="part.size"
  />
</template>
