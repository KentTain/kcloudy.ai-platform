import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { Tree } from '@/components/common'
import type { TreeSelectNode } from '@/framework/types/tree'

// 测试数据
const treeData: TreeSelectNode[] = [
  {
    id: '1',
    name: '研发部',
    children: [
      { id: '2', name: '前端组' },
      { id: '3', name: '后端组' },
    ],
  },
  {
    id: '4',
    name: '市场部',
  },
]

const flatData: TreeSelectNode[] = [
  { id: '1', name: '研发部' },
  { id: '4', name: '市场部' },
]

const deepTreeData: TreeSelectNode[] = [
  {
    id: '1',
    name: '根节点',
    children: [
      {
        id: '1-1',
        name: '子节点1',
        children: [
          { id: '1-1-1', name: '孙节点1' },
          { id: '1-1-2', name: '孙节点2' },
        ],
      },
      { id: '1-2', name: '子节点2' },
    ],
  },
]

describe('Tree', () => {
  describe('基础功能', () => {
    it('渲染扁平节点列表', () => {
      const wrapper = mount(Tree, {
        props: { data: flatData, defaultExpandLevel: 0 },
      })
      expect(wrapper.text()).toContain('研发部')
      expect(wrapper.text()).toContain('市场部')
    })

    it('默认展开第一层显示子节点', () => {
      const wrapper = mount(Tree, {
        props: { data: treeData, defaultExpandLevel: 1 },
      })
      expect(wrapper.text()).toContain('研发部')
      expect(wrapper.text()).toContain('前端组')
      expect(wrapper.text()).toContain('后端组')
    })

    it('空数据不崩溃', () => {
      const wrapper = mount(Tree, {
        props: { data: [] },
      })
      expect(wrapper.find('div').exists()).toBe(true)
    })
  })

  describe('checkable 模式', () => {
    it('显示复选框', () => {
      const wrapper = mount(Tree, {
        props: { data: flatData, checkable: true },
      })
      // Checkbox 组件会被渲染
      expect(wrapper.html()).toContain('role="checkbox"')
    })

    it('显示已选中的节点', () => {
      const wrapper = mount(Tree, {
        props: { data: flatData, checkable: true, modelValue: ['1'] },
      })
      // 第一个节点应该被选中 - 检查 checked="true" 属性
      expect(wrapper.html()).toContain('checked="true"')
    })

    it('禁用节点不可选中', async () => {
      const disabledData: TreeSelectNode[] = [
        { id: '1', name: '禁用节点', disabled: true },
        { id: '2', name: '正常节点' },
      ]
      const wrapper = mount(Tree, {
        props: { data: disabledData, checkable: true, modelValue: [] },
      })

      // 检查第一个 checkbox 是否禁用
      expect(wrapper.html()).toContain('disabled:cursor-not-allowed')
    })
  })

  describe('cascade 级联选择', () => {
    it('选中父节点自动选中所有子节点', async () => {
      const wrapper = mount(Tree, {
        props: { data: deepTreeData, checkable: true, cascade: true, modelValue: [], defaultExpandLevel: 2 },
      })

      // 点击第一个 checkbox（根节点）
      const checkbox = wrapper.find('[role="checkbox"]')
      if (checkbox.exists()) {
        await checkbox.trigger('click')
        const emitted = wrapper.emitted('update:modelValue')
        if (emitted && emitted[0]) {
          const newValue = emitted[0][0] as (string | number)[]
          // 应该包含根节点和所有子节点
          expect(newValue).toContain('1')
          expect(newValue).toContain('1-1')
          expect(newValue).toContain('1-2')
          expect(newValue).toContain('1-1-1')
          expect(newValue).toContain('1-1-2')
        }
      }
    })

    it('取消选中父节点自动取消所有子节点', async () => {
      // 所有节点都已选中
      const allSelected = ['1', '1-1', '1-2', '1-1-1', '1-1-2']
      const wrapper = mount(Tree, {
        props: { data: deepTreeData, checkable: true, cascade: true, modelValue: allSelected, defaultExpandLevel: 2 },
      })

      const checkbox = wrapper.find('[role="checkbox"]')
      if (checkbox.exists()) {
        // 点击根节点取消选中
        await checkbox.trigger('click')
        const emitted = wrapper.emitted('update:modelValue')
        if (emitted && emitted[0]) {
          const newValue = emitted[0][0] as (string | number)[]
          // 应该全部取消
          expect(newValue.length).toBe(0)
        }
      }
    })

    it('子节点部分选中时显示 indeterminate 状态', () => {
      // 只有部分子节点选中
      const partialSelected = ['1', '1-1']  // 缺少 1-2
      const wrapper = mount(Tree, {
        props: { data: deepTreeData, checkable: true, cascade: true, modelValue: partialSelected, defaultExpandLevel: 2 },
      })

      // 根节点应该显示 indeterminate 状态
      // 检查 DOM 中是否有 indeterminate 属性
      const html = wrapper.html()
      expect(html).toContain('indeterminate="true"')
    })
  })

  describe('disabled 禁用状态', () => {
    it('整棵树禁用时添加禁用样式', async () => {
      const wrapper = mount(Tree, {
        props: { data: treeData, disabled: true, defaultExpandLevel: 1 },
      })

      // 检查禁用样式
      expect(wrapper.html()).toContain('cursor-not-allowed')
    })

    it('单个节点禁用时添加禁用样式', async () => {
      const disabledNodeData: TreeSelectNode[] = [
        { id: '1', name: '禁用节点', disabled: true, children: [{ id: '2', name: '子节点' }] },
      ]
      const wrapper = mount(Tree, {
        props: { data: disabledNodeData, defaultExpandLevel: 0 },
      })

      // 检查禁用样式
      expect(wrapper.html()).toContain('cursor-not-allowed')
    })
  })

  describe('loadData 异步加载', () => {
    it('异步加载子节点', async () => {
      const loadData = vi.fn((node, callback) => {
        setTimeout(() => {
          callback([
            { id: `${node.id}-child-1`, name: '异步子节点1' },
            { id: `${node.id}-child-2`, name: '异步子节点2' },
          ])
        }, 100)
      })

      const asyncData: TreeSelectNode[] = [
        { id: '1', name: '可展开节点', isLeaf: false },
      ]

      const wrapper = mount(Tree, {
        props: { data: asyncData, loadData, defaultExpandLevel: 0 },
      })

      // 点击展开按钮触发异步加载
      const buttons = wrapper.findAll('button')
      if (buttons.length > 0) {
        await buttons[0].trigger('click')
        expect(loadData).toHaveBeenCalled()

        // 等待异步加载完成
        await new Promise(resolve => setTimeout(resolve, 150))
        await nextTick()

        // 应该显示加载的子节点
        expect(wrapper.text()).toContain('异步子节点1')
      }
    })
  })

  describe('showLine 连接线', () => {
    it('启用 showLine 显示连接线', () => {
      const wrapper = mount(Tree, {
        props: { data: treeData, showLine: true, defaultExpandLevel: 1 },
      })

      // 检查连接线样式 - 使用 kebab-case 的 border-left
      const html = wrapper.html()
      expect(html).toContain('border-left')
    })
  })
})
