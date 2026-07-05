import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useFileUpload } from '@/ai/composables/useFileUpload'

describe('useFileUpload', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        data: {
          url: 'https://minio.example.com/test.txt',
          mediaType: 'text/plain',
          filename: 'test.txt',
          size: 12,
        }
      })
    }))
  })

  it('uploads file successfully', async () => {
    const { uploadFile } = useFileUpload()

    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const result = await uploadFile(file)

    expect(result.type).toBe('file')
    expect(result.url).toBe('https://minio.example.com/test.txt')
    expect(result.mediaType).toBe('text/plain')
    expect(result.filename).toBe('test.txt')
  })

  it('tracks upload progress', async () => {
    const { uploadFile, uploadProgress } = useFileUpload()

    const file = new File(['test'], 'test.txt', { type: 'text/plain' })
    await uploadFile(file)

    expect(uploadProgress.value).toBe(100)
  })
})
