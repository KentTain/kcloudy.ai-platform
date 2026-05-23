import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DateInput from '@/components/DateInput.vue'

describe('DateInput', () => {
  describe('基本渲染', () => {
    it('渲染输入框', () => {
      const wrapper = mount(DateInput)
      expect(wrapper.find('input').exists()).toBe(true)
    })

    it('显示 placeholder', () => {
      const wrapper = mount(DateInput, {
        props: { placeholder: '请选择日期' },
      })
      expect(wrapper.find('input').attributes('placeholder')).toBe('请选择日期')
    })

    it('禁用状态', () => {
      const wrapper = mount(DateInput, {
        props: { disabled: true },
      })
      expect(wrapper.find('input').attributes('disabled')).toBeDefined()
    })

    it('显示日历图标', () => {
      const wrapper = mount(DateInput)
      expect(wrapper.html()).toContain('calendar')
    })
  })

  describe('单日期模式', () => {
    it('显示已选择的日期', () => {
      const wrapper = mount(DateInput, {
        props: {
          type: 'single',
          modelValue: '2024-01-15',
        },
      })
      expect(wrapper.find('input').element.value).toBe('2024-01-15')
    })

    it('空值时显示空', () => {
      const wrapper = mount(DateInput, {
        props: {
          type: 'single',
          modelValue: undefined,
        },
      })
      expect(wrapper.find('input').element.value).toBe('')
    })
  })

  describe('日期范围模式', () => {
    it('显示已选择的日期范围', () => {
      const wrapper = mount(DateInput, {
        props: {
          type: 'range',
          modelValue: ['2024-01-01', '2024-01-15'],
        },
      })
      expect(wrapper.find('input').element.value).toBe('2024-01-01 ~ 2024-01-15')
    })

    it('只显示开始日期', () => {
      const wrapper = mount(DateInput, {
        props: {
          type: 'range',
          modelValue: ['2024-01-01', ''],
        },
      })
      expect(wrapper.find('input').element.value).toBe('2024-01-01')
    })

    it('空值时显示空', () => {
      const wrapper = mount(DateInput, {
        props: {
          type: 'range',
          modelValue: undefined,
        },
      })
      expect(wrapper.find('input').element.value).toBe('')
    })
  })
})
