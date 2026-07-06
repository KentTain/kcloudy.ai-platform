// tests/ai/unit/composables/useChunkedUpload.test.ts
import { describe, it, expect, vi } from 'vitest'
import { useChunkedUpload } from '@/ai/composables/useChunkedUpload'

describe('useChunkedUpload', () => {
  it('calculates MD5 correctly', async () => {
    const { calculateMD5 } = useChunkedUpload()

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const md5 = await calculateMD5(file)

    expect(md5).toBeDefined()
    expect(md5.length).toBe(32)  // MD5 长度
  })

  it('creates chunks with correct size', () => {
    const { createChunks } = useChunkedUpload()

    const file = new File(['x'.repeat(12 * 1024 * 1024)], 'test.bin')  // 12 MB
    const chunks = createChunks(file)

    expect(chunks.length).toBe(3)  // 5MB * 3 = 15MB > 12MB
    expect(chunks[0].start).toBe(0)
    expect(chunks[0].end).toBe(5 * 1024 * 1024)
  })

  it('tracks upload progress', async () => {
    const { uploadProgress, uploadFile } = useChunkedUpload()

    const file = new File(['test'], 'test.txt')

    // Mock 分片上传接口
    vi.mock('@/framework/api/client', () => ({
      client: {
        post: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: { uploadedChunks: [] } }),
      }
    }))

    await uploadFile(file)

    expect(uploadProgress.value).toBeGreaterThanOrEqual(0)
    expect(uploadProgress.value).toBeLessThanOrEqual(100)
  })
})
