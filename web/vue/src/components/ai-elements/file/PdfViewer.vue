<!-- src/components/ai-elements/file/PdfViewer.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Button } from '@/components'

const props = defineProps<{
  url: string
}>()

const currentPage = ref(1)
const totalPages = ref(0)

// 简化实现：实际项目中需要集成 pdfjs-dist
onMounted(async () => {
  // PDF.js 初始化逻辑
  totalPages.value = 1
})

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}
</script>

<template>
  <div data-testid="pdf-viewer" class="space-y-4">
    <div class="w-full border rounded-lg min-h-[600px] flex items-center justify-center bg-muted">
      <p class="text-muted-foreground">PDF 预览：{{ url }}</p>
    </div>

    <div class="flex items-center justify-center gap-4">
      <Button variant="outline" size="sm" @click="prevPage" :disabled="currentPage === 1">
        上一页
      </Button>
      <span class="text-sm">
        {{ currentPage }} / {{ totalPages }}
      </span>
      <Button variant="outline" size="sm" @click="nextPage" :disabled="currentPage === totalPages">
        下一页
      </Button>
    </div>
  </div>
</template>
