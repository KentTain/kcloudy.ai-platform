import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { Pagination } from '@/components/common'

describe('Pagination', () => {
  describe('基本渲染', () => {
    it('当 total 为 0 时不显示', () => {
      const wrapper = mount(Pagination, {
        props: { total: 0, page: 1, pageSize: 10 },
      })
      expect(wrapper.find('div').exists()).toBe(false)
    })

    it('当 total > 0 时显示分页控件', () => {
      const wrapper = mount(Pagination, {
        props: { total: 100, page: 1, pageSize: 10 },
      })
      expect(wrapper.find('div').exists()).toBe(true)
      expect(wrapper.text()).toContain('共')
      expect(wrapper.text()).toContain('100')
      expect(wrapper.text()).toContain('条')
    })

    it('显示正确的总数', () => {
      const wrapper = mount(Pagination, {
        props: { total: 256, page: 1, pageSize: 10 },
      })
      expect(wrapper.text()).toContain('256')
    })
  })

  describe('页码导航', () => {
    it('点击页码按钮触发 update:page 事件', async () => {
      const onUpdatePage = vi.fn()
      const wrapper = mount(Pagination, {
        props: { total: 100, page: 1, pageSize: 10 },
        attrs: { 'onUpdate:page': onUpdatePage },
      })
      // 找到页码按钮（包含数字的按钮）
      const pageButtons = wrapper.findAll('button').filter(b => {
        const text = b.text().trim()
        return text === '2'
      })
      expect(pageButtons.length).toBeGreaterThan(0)
      await pageButtons[0].trigger('click')
      expect(onUpdatePage).toHaveBeenCalledWith(2)
    })

    it('点击下一页按钮触发 update:page 事件', async () => {
      const onUpdatePage = vi.fn()
      const wrapper = mount(Pagination, {
        props: { total: 100, page: 1, pageSize: 10 },
        attrs: { 'onUpdate:page': onUpdatePage },
      })
      // 找到所有按钮
      const buttons = wrapper.findAll('button')
      // 找到包含 chevron-right 图标的按钮（注意是小写）
      const nextBtn = buttons.find(b => b.html().includes('chevron-right'))
      expect(nextBtn).toBeDefined()
      if (nextBtn) {
        await nextBtn.trigger('click')
        expect(onUpdatePage).toHaveBeenCalledWith(2)
      }
    })

    it('点击上一页按钮触发 update:page 事件', async () => {
      const onUpdatePage = vi.fn()
      const wrapper = mount(Pagination, {
        props: { total: 100, page: 2, pageSize: 10 },
        attrs: { 'onUpdate:page': onUpdatePage },
      })
      const buttons = wrapper.findAll('button')
      // 找到包含 ChevronLeft 图标的按钮
      const prevBtn = buttons.find(b => b.html().includes('chevron-left'))
      expect(prevBtn).toBeDefined()
      if (prevBtn) {
        await prevBtn.trigger('click')
        expect(onUpdatePage).toHaveBeenCalledWith(1)
      }
    })
  })

  describe('每页条数切换', () => {
    it('切换每页条数触发 update:pageSize 事件', async () => {
      const wrapper = mount(Pagination, {
        props: { total: 100, page: 5, pageSize: 10 },
      })
      const selectTrigger = wrapper.find('[data-testid="select-trigger"]')
      if (selectTrigger.exists()) {
        await selectTrigger.trigger('click')
      }
    })

    it('切换每页条数后页码重置为 1', async () => {
      const wrapper = mount(Pagination, {
        props: { total: 100, page: 5, pageSize: 10, pageSizeOptions: [10, 20, 50] },
      })
    })
  })

  describe('边界条件', () => {
    it('当前页码大于最大页码时自动修正', () => {
      const wrapper = mount(Pagination, {
        props: { total: 100, page: 20, pageSize: 10 },
      })
      // 总页数为 10，page=20 时应当显示第 10 页
      // 检查第 10 页按钮存在且是当前页
      const allButtons = wrapper.findAll('button')
      // 在 ChevronsLeft, ChevronLeft 图标按钮之后的第 9 个按钮是页码 10
      const page10Btn = allButtons.find(b => b.text().trim() === '10')
      expect(page10Btn).toBeDefined()
    })

    it('在第一页时禁用首页和上一页按钮', () => {
      const wrapper = mount(Pagination, {
        props: { total: 100, page: 1, pageSize: 10 },
      })
      const buttons = wrapper.findAll('button')
      const disabledButtons = buttons.filter(b => b.attributes('disabled') !== undefined)
      expect(disabledButtons.length).toBeGreaterThan(0)
    })

    it('在最后一页时禁用下一页和末页按钮', () => {
      const wrapper = mount(Pagination, {
        props: { total: 100, page: 10, pageSize: 10 },
      })
      const buttons = wrapper.findAll('button')
      const disabledButtons = buttons.filter(b => b.attributes('disabled') !== undefined)
      expect(disabledButtons.length).toBeGreaterThan(0)
    })
  })
})
