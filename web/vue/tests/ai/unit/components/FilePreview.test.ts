// tests/ai/unit/components/FilePreview.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FilePreview from '@/components/ai-elements/file/FilePreview.vue'

describe('FilePreview', () => {
  it('shows PDF viewer for PDF files', () => {
    const wrapper = mount(FilePreview, {
      props: {
        mediaType: 'application/pdf',
        url: 'https://example.com/doc.pdf',
      }
    })

    expect(wrapper.find('[data-testid="pdf-viewer"]').exists()).toBe(true)
  })

  it('shows image viewer for image files', () => {
    const wrapper = mount(FilePreview, {
      props: {
        mediaType: 'image/png',
        url: 'https://example.com/image.png',
      }
    })

    expect(wrapper.find('[data-testid="image-viewer"]').exists()).toBe(true)
  })

  it('shows download option for unsupported types', () => {
    const wrapper = mount(FilePreview, {
      props: {
        mediaType: 'application/zip',
        url: 'https://example.com/file.zip',
      }
    })

    expect(wrapper.text()).toContain('该文件类型暂不支持预览')
  })
})
