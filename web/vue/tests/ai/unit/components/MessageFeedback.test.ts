// tests/ai/unit/components/MessageFeedback.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageFeedback from '@/components/ai-elements/metadata/MessageFeedback.vue'

describe('MessageFeedback', () => {
  it('renders feedback buttons', () => {
    const wrapper = mount(MessageFeedback, {
      props: { messageId: 'msg-123' }
    })

    expect(wrapper.find('[data-testid="thumbs-up"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="thumbs-down"]').exists()).toBe(true)
  })

  it('highlights selected rating', async () => {
    const wrapper = mount(MessageFeedback, {
      props: {
        messageId: 'msg-123',
        rating: 2
      }
    })

    const thumbsUp = wrapper.find('[data-testid="thumbs-up"]')
    expect(thumbsUp.classes()).toContain('text-green-500')
  })

  it('shows feedback dialog', async () => {
    const wrapper = mount(MessageFeedback, {
      props: { messageId: 'msg-123' }
    })

    await wrapper.find('[data-testid="feedback-button"]').trigger('click')

    expect(wrapper.find('[data-testid="feedback-dialog"]').exists()).toBe(true)
  })
})
