// tests/ai/unit/components/SourceRendererEnhanced.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SourceUrlCard from '@/components/ai-elements/source/SourceUrlCard.vue'

describe('SourceRenderer Enhanced', () => {
  it('opens URL in new tab on click', async () => {
    const openSpy = vi.spyOn(window, 'open')

    const wrapper = mount(SourceUrlCard, {
      props: {
        sourceId: 'src-123',
        url: 'https://example.com',
        title: 'Example',
      }
    })

    await wrapper.find('.source-card').trigger('click')

    expect(openSpy).toHaveBeenCalledWith('https://example.com', '_blank')
  })

  it('shows preview button on hover', async () => {
    const wrapper = mount(SourceUrlCard, {
      props: {
        sourceId: 'src-456',
        url: 'https://example.com',
      }
    })

    const previewButton = wrapper.find('[data-testid="preview-button"]')
    expect(previewButton.classes()).toContain('opacity-0')

    await wrapper.find('.source-card').trigger('mouseenter')
    expect(previewButton.classes()).toContain('group-hover:opacity-100')
  })
})
