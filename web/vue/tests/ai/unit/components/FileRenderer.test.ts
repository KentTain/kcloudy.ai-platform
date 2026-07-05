import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FileAttachment from '@/components/ai-elements/file/FileAttachment.vue'

describe('FileAttachment', () => {
  it('renders file with correct information', () => {
    const wrapper = mount(FileAttachment, {
      props: {
        mediaType: 'application/pdf',
        url: 'https://minio.example.com/doc.pdf',
        filename: 'report.pdf',
        size: 1048576,
      }
    })

    expect(wrapper.text()).toContain('report.pdf')
    expect(wrapper.text()).toContain('1.0 MB')
    expect(wrapper.text()).toContain('application/pdf')
  })

  it('opens file in new tab on click', async () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)

    const wrapper = mount(FileAttachment, {
      props: {
        mediaType: 'application/pdf',
        url: 'https://minio.example.com/doc.pdf',
        filename: 'document.pdf',
      }
    })

    await wrapper.find('[data-testid="file-link"]').trigger('click')

    expect(openSpy).toHaveBeenCalledWith('https://minio.example.com/doc.pdf', '_blank')
    openSpy.mockRestore()
  })
})
