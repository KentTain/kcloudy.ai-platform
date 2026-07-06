// src/ai/composables/useChunkedUpload.ts
import { ref } from 'vue'
import { client } from '@/framework/api/client'
import SparkMD5 from 'spark-md5'

export function useChunkedUpload() {
  const CHUNK_SIZE = 5 * 1024 * 1024  // 5 MB
  const MAX_CONCURRENT = 3  // 最多并发 3 个分片

  const uploadProgress = ref(0)
  const uploadStatus = ref<'idle' | 'uploading' | 'paused' | 'completed'>('idle')
  const uploadedChunks = ref<Set<number>>(new Set())

  /**
   * 计算文件 MD5（前 2MB）
   */
  const calculateMD5 = async (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const spark = new SparkMD5.ArrayBuffer()
      const reader = new FileReader()

      const chunk = file.slice(0, 2 * 1024 * 1024)

      reader.onload = (e) => {
        spark.append(e.target?.result as ArrayBuffer)
        resolve(spark.end())
      }

      reader.readAsArrayBuffer(chunk)
    })
  }

  /**
   * 创建分片列表
   */
  const createChunks = (file: File): Array<{ index: number; start: number; end: number }> => {
    const chunks = []
    let start = 0
    let index = 0

    while (start < file.size) {
      chunks.push({
        index,
        start,
        end: Math.min(start + CHUNK_SIZE, file.size),
      })
      start += CHUNK_SIZE
      index++
    }

    return chunks
  }

  /**
   * 上传单个分片
   */
  const uploadChunk = async (
    file: File,
    chunk: { index: number; start: number; end: number },
    fileId: string
  ) => {
    const chunkData = file.slice(chunk.start, chunk.end)

    const formData = new FormData()
    formData.append('file', chunkData)
    formData.append('file_id', fileId)
    formData.append('chunk_index', String(chunk.index))
    formData.append('total_chunks', String(Math.ceil(file.size / CHUNK_SIZE)))

    await client.post('/ai/console/v1/files/upload-chunk', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    uploadedChunks.value.add(chunk.index)
    updateProgress(file.size)
  }

  /**
   * 并发控制上传
   */
  const uploadWithConcurrency = async (
    file: File,
    chunks: Array<{ index: number; start: number; end: number }>,
    fileId: string
  ) => {
    const queue = [...chunks]
    const activeUploads: Promise<void>[] = []

    while (queue.length > 0 || activeUploads.length > 0) {
      while (activeUploads.length < MAX_CONCURRENT && queue.length > 0) {
        const chunk = queue.shift()!
        const promise = uploadChunk(file, chunk, fileId).then(() => {
          const index = activeUploads.indexOf(promise)
          if (index > -1) activeUploads.splice(index, 1)
        })
        activeUploads.push(promise)
      }

      if (activeUploads.length > 0) {
        await Promise.race(activeUploads)
      }
    }
  }

  /**
   * 更新进度
   */
  const updateProgress = (totalSize: number) => {
    const uploadedSize = uploadedChunks.value.size * CHUNK_SIZE
    uploadProgress.value = Math.min(100, Math.round((uploadedSize / totalSize) * 100))
  }

  /**
   * 主上传方法
   */
  const uploadFile = async (file: File): Promise<{ url: string }> => {
    uploadStatus.value = 'uploading'
    uploadProgress.value = 0
    uploadedChunks.value.clear()

    try {
      // 1. 计算文件 MD5
      const fileId = await calculateMD5(file)

      // 2. 检查断点续传
      const { data } = await client.get(`/ai/console/v1/files/upload-state/${fileId}`)

      if (data.uploadedChunks) {
        uploadedChunks.value = new Set(data.uploadedChunks)
      }

      // 3. 创建分片列表
      const chunks = createChunks(file)

      // 4. 过滤已上传的分片
      const pendingChunks = chunks.filter(c => !uploadedChunks.value.has(c.index))

      // 5. 并发上传
      await uploadWithConcurrency(file, pendingChunks, fileId)

      // 6. 合并分片
      const response = await client.post('/ai/console/v1/files/merge-chunks', {
        file_id: fileId,
        filename: file.name,
        total_chunks: chunks.length,
      })

      uploadStatus.value = 'completed'
      return { url: response.data.url }
    } catch (error) {
      uploadStatus.value = 'paused'
      throw error
    }
  }

  return {
    uploadFile,
    uploadProgress,
    uploadStatus,
    uploadedChunks,
    calculateMD5,
    createChunks,
  }
}
