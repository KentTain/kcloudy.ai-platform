import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SourceUrlCard from '@/components/ai-elements/source/SourceUrlCard.vue'
import SourceDocumentCard from '@/components/ai-elements/source/SourceDocumentCard.vue'

describe('SourceUrlCard', () => {
  it('renders with correct link and title', () => {
    const wrapper = mount(SourceUrlCard, {
      props: {
        sourceId: 'source-123',
        url: 'https://example.com',
        title: 'Example Site',
      }
    })

    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe('https://example.com')
    expect(link.attributes('target')).toBe('_blank')
    expect(wrapper.text()).toContain('Example Site')
    expect(wrapper.text()).toContain('https://example.com')
  })

  it('displays URL when title is missing', () => {
    const wrapper = mount(SourceUrlCard, {
      props: {
        sourceId: 'source-456',
        url: 'https://example.com/page',
      }
    })

    expect(wrapper.text()).toContain('https://example.com/page')
  })
})

describe('SourceDocumentCard', () => {
  it('renders document with preview button', () => {
    const wrapper = mount(SourceDocumentCard, {
      props: {
        sourceId: 'source-789',
        mediaType: 'application/pdf',
        url: 'https://example.com/doc.pdf',
        title: 'Document Title',
      }
    })

    expect(wrapper.text()).toContain('Document Title')
    expect(wrapper.text()).toContain('application/pdf')
    expect(wrapper.find('button').exists()).toBe(true)
  })
})
