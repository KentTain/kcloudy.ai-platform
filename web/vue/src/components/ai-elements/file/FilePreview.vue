<!-- src/components/ai-elements/file/FilePreview.vue -->
<script setup lang="ts">
import { computed } from 'vue'
import { FileIcon, DownloadIcon } from 'lucide-vue-next'
import { Dialog, DialogContent, Button } from '@/components'
import PdfViewer from './PdfViewer.vue'
import ImageViewer from './ImageViewer.vue'

const props = defineProps<{
  mediaType: string
  url: string
  filename?: string
}>()

const isOpen = defineModel<boolean>('open')

const isOfficeDocument = computed(() => {
  return [
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  ].includes(props.mediaType)
})

const getOfficeViewerUrl = (url: string): string => {
  return `https://docs.google.com/viewer?url=${encodeURIComponent(url)}&embedded=true`
}

const downloadFile = () => {
  window.open(props.url, '_blank')
}
</script>

<template>
  <Dialog v-model:open="isOpen">
    <DialogContent class="max-w-4xl max-h-[80vh]">
      <!-- PDF 预览 -->
      <PdfViewer
        v-if="mediaType === 'application/pdf'"
        :url="url"
      />

      <!-- 图片预览 -->
      <ImageViewer
        v-else-if="mediaType.startsWith('image/')"
        :url="url"
        :zoom="true"
        :rotate="true"
      />

      <!-- Office 文档预览 -->
      <iframe
        v-else-if="isOfficeDocument"
        :src="getOfficeViewerUrl(url)"
        class="w-full h-[600px]"
      />

      <!-- 其他文件：下载 -->
      <div v-else class="text-center py-8">
        <FileIcon class="size-12 mx-auto mb-4 text-muted-foreground" />
        <p class="text-muted-foreground">该文件类型暂不支持预览</p>
        <Button @click="downloadFile" class="mt-4">
          <DownloadIcon class="size-4 mr-2" />
          下载文件
        </Button>
      </div>
    </DialogContent>
  </Dialog>
</template>
