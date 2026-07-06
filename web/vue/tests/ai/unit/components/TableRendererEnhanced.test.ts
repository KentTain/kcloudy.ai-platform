// tests/ai/unit/components/TableRendererEnhanced.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TableRenderer from '@/components/ai-elements/data/TableRenderer.vue'

describe('TableRenderer Enhanced', () => {
  const testData = {
    headers: ['Name', 'Age', 'City'],
    rows: [
      ['Alice', 25, 'Beijing'],
      ['Bob', 30, 'Shanghai'],
      ['Charlie', 35, 'Guangzhou'],
    ]
  }

  it('filters rows by search query', async () => {
    const wrapper = mount(TableRenderer, {
      props: { content: testData }
    })

    const input = wrapper.find('input[placeholder="搜索..."]')
    await input.setValue('Alice')

    const rows = wrapper.findAll('tbody tr')
    expect(rows.length).toBe(1)
    expect(rows[0].text()).toContain('Alice')
  })

  it('sorts rows by column', async () => {
    const wrapper = mount(TableRenderer, {
      props: { content: testData }
    })

    // 点击 Age 表头排序
    const headers = wrapper.findAll('th')
    await headers[1].trigger('click')

    const rows = wrapper.findAll('tbody tr')
    expect(rows[0].text()).toContain('25')  // 升序
  })

  it('toggles sort direction', async () => {
    const wrapper = mount(TableRenderer, {
      props: { content: testData }
    })

    const headers = wrapper.findAll('th')
    // 第一次点击：升序
    await headers[1].trigger('click')
    // 第二次点击：降序
    await headers[1].trigger('click')

    const rows = wrapper.findAll('tbody tr')
    expect(rows[0].text()).toContain('35')  // 降序
  })
})
