<script setup lang="ts">
import type { SourceUrlPart, SourceDocumentPart } from '@/ai/types'
import SourceUrlCard from './SourceUrlCard.vue'
import SourceDocumentCard from './SourceDocumentCard.vue'

interface Props {
  part: SourceUrlPart | SourceDocumentPart
}
defineProps<Props>()
</script>

<template>
  <SourceUrlCard
    v-if="part.type === 'source-url'"
    :source-id="part.sourceId"
    :url="part.url"
    :title="part.title"
  />
  <SourceDocumentCard
    v-else-if="part.type === 'source-document'"
    :source-id="part.sourceId"
    :media-type="part.mediaType"
    :url="part.url"
    :title="part.title"
  />
</template>
