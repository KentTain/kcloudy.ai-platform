<script setup lang="ts">
import type { FilePart } from '@/ai/types'
import { useFileUpload } from '@/ai/composables/useFileUpload'
import { ref } from 'vue'

const emit = defineEmits<{
  uploaded: [FilePart]
}>()

const { uploadFile, isUploading } = useFileUpload()
const fileInput = ref<HTMLInputElement>()

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file) {
    const filePart = await uploadFile(file)
    emit('uploaded', filePart)
  }

  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const handleButtonClick = () => {
  fileInput.value?.click()
}
</script>

<template>
  <div>
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      @change="handleFileSelect"
    />
    <button
      class="rounded-md border p-2 hover:bg-muted/50 transition-colors disabled:opacity-50"
      :disabled="isUploading"
      @click="handleButtonClick"
    >
      <span v-if="isUploading">上传中...</span>
      <span v-else>上传文件</span>
    </button>
  </div>
</template>
