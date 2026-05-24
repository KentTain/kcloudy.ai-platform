import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CommonTree from '@/components/CommonTree.vue'
import type { TreeComponentNode } from '@/framework/types/tree'

// 测试数据
const treeData: TreeComponentNode[] = [
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

const flatData: TreeComponentNode[] = [
  { id: '1', name: '研发部' },
  { id: '4', name: '市场部' },
]

describe('CommonTree', () => {
  it('渲染扁平节点列表', () => {
    const wrapper = mount(CommonTree, {
      props: { data: flatData, defaultExpandLevel: 0 },
    })
    expect(wrapper.text()).toContain('研发部')
    expect(wrapper.text()).toContain('市场部')
  })

  it('默认展开第一层显示子节点', () => {
    const wrapper = mount(CommonTree, {
      props: { data: treeData, defaultExpandLevel: 1 },
    })
    // 根节点 + 子节点 + 叶子节点 都应该可见
    expect(wrapper.text()).toContain('研发部')
    expect(wrapper.text()).toContain('前端组')
    expect(wrapper.text()).toContain('后端组')
  })

  it('空数据不崩溃', () => {
    const wrapper = mount(CommonTree, {
      props: { data: [] },
    })
    expect(wrapper.find('div').exists()).toBe(true)
  })
})