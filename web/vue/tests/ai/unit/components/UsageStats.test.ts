// tests/ai/unit/components/UsageStats.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import UsageStats from '@/components/ai-elements/metadata/UsageStats.vue'

describe('UsageStats', () => {
  it('displays statistics cards', async () => {
    const wrapper = mount(UsageStats)

    // 等待数据加载
    await wrapper.vm.$nextTick()

    expect(wrapper.find('[data-testid="total-messages"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="total-tokens"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="total-cost"]').exists()).toBe(true)
  })

  it('formats large numbers correctly', () => {
    const wrapper = mount(UsageStats)

    // Mock 组件内部方法
    const result = wrapper.vm.formatNumber(1500000)
    expect(result).toBe('1.5M')
  })
})
