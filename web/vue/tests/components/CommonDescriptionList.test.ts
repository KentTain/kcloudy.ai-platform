import { describe, expect, it } from 'vitest'
import { h } from 'vue'
import { mount } from '@vue/test-utils'
import CommonDescriptionList from '@/components/CommonDescriptionList.vue'
import type { DescriptionItem } from '@/components/CommonDescriptionList.vue'

describe('CommonDescriptionList', () => {
  const sampleItems: DescriptionItem[] = [
    { label: '用户名', value: 'admin' },
    { label: '邮箱', value: 'admin@example.com' },
    { label: '状态', value: 'active', type: 'badge', badgeVariant: 'default' },
    { label: '空值', value: null },
    { label: '空字符串', value: '' },
    { label: '未定义', value: undefined },
  ]

  describe('基本渲染', () => {
    it('渲染 key-value 对', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: sampleItems },
      })
      expect(wrapper.text()).toContain('用户名')
      expect(wrapper.text()).toContain('admin')
      expect(wrapper.text()).toContain('邮箱')
      expect(wrapper.text()).toContain('admin@example.com')
    })

    it('使用 grid 布局', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: sampleItems, columns: 2 },
      })
      expect(wrapper.find('.grid').classes()).toContain('grid-cols-2')
    })

    it('支持 1 列布局', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: sampleItems, columns: 1 },
      })
      expect(wrapper.find('.grid').classes()).toContain('grid-cols-1')
    })

    it('支持 3 列布局', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: sampleItems, columns: 3 },
      })
      expect(wrapper.find('.grid').classes()).toContain('grid-cols-3')
    })
  })

  describe('空值处理', () => {
    it('null 值显示占位符', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: [{ label: '测试', value: null }] },
      })
      expect(wrapper.text()).toContain('--')
    })

    it('undefined 值显示占位符', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: [{ label: '测试', value: undefined }] },
      })
      expect(wrapper.text()).toContain('--')
    })

    it('空字符串显示占位符', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: [{ label: '测试', value: '' }] },
      })
      expect(wrapper.text()).toContain('--')
    })
  })

  describe('Badge 类型', () => {
    it('type=badge 时渲染 Badge 组件', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: {
          items: [{ label: '状态', value: 'active', type: 'badge' as const }],
        },
      })
      expect(wrapper.findComponent({ name: 'Badge' }).exists()).toBe(true)
    })

    it('Badge 支持不同 variant', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: {
          items: [
            { label: '状态', value: 'active', type: 'badge' as const, badgeVariant: 'default' as const },
          ],
        },
      })
      const badge = wrapper.findComponent({ name: 'Badge' })
      expect(badge.exists()).toBe(true)
    })
  })

  describe('边框样式', () => {
    it('bordered=true 显示边框', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: sampleItems, bordered: true },
      })
      const borderedElements = wrapper.findAll('.border-b')
      expect(borderedElements.length).toBeGreaterThan(0)
    })

    it('bordered=false 不显示边框', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: sampleItems, bordered: false },
      })
      expect(wrapper.find('.border-b').exists()).toBe(false)
    })
  })

  describe('自定义 slot', () => {
    it('支持 item slot', () => {
      const wrapper = mount(CommonDescriptionList, {
        props: { items: sampleItems },
        slots: {
          item: (slotProps: { item: DescriptionItem }) =>
            h('span', { class: 'custom-value' }, slotProps.item.value),
        },
      })
      expect(wrapper.find('.custom-value').exists()).toBe(true)
    })
  })
})
