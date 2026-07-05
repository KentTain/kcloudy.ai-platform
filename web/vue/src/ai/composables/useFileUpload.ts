import { ref } from 'vue'
import type { FilePart } from '@/ai/types'

export function useFileUpload() {
  const uploadProgress = ref(0)
  const isUploading = ref(false)

  const uploadFile = async (file: File): Promise<FilePart> => {
    isUploading.value = true
    uploadProgress.value = 0

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/ai/console/v1/files/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()

      uploadProgress.value = 100

      return {
        type: 'file',
        mediaType: file.type || 'application/octet-stream',
        url: result.data.url,
        filename: file.name,
        size: file.size,
      }
    } finally {
      isUploading.value = false
    }
  }

  return {
    uploadFile,
    uploadProgress,
    isUploading,
  }
}
