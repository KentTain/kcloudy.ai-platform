import { describe, expect, it, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import DepartmentTree from '@/iam/components/DepartmentTree.vue'
import type { Department } from '@/iam/types'

const mockDepartments: Department[] = [
  {
    id: 'dept-1',
    tenant_id: 'tenant-1',
    name: '总公司',
    sort_order: 0,
    status: 'active',
    created_at: '2024-01-01',
    children: [
      {
        id: 'dept-2',
        tenant_id: 'tenant-1',
        parent_id: 'dept-1',
        name: '研发部',
        sort_order: 0,
        status: 'active',
        created_at: '2024-01-01',
        children: [
          { id: 'dept-3', tenant_id: 'tenant-1', parent_id: 'dept-2', name: '前端组', sort_order: 0, status: 'active', created_at: '2024-01-01' },
          { id: 'dept-4', tenant_id: 'tenant-1', parent_id: 'dept-2', name: '后端组', sort_order: 1, status: 'active', created_at: '2024-01-01' },
        ],
      },
      {
        id: 'dept-5',
        tenant_id: 'tenant-1',
        parent_id: 'dept-1',
        name: '市场部',
        sort_order: 1,
        status: 'active',
        created_at: '2024-01-01',
      },
    ],
  },
]

describe('DepartmentTree', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('基础渲染', () => {
    it('组件存在且可挂载', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '' },
      })
      expect(wrapper.exists()).toBe(true)
    })

    it('渲染 CheckboxTree 组件', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '' },
      })
      expect(wrapper.findComponent({ name: 'CommonCheckboxTree' }).exists()).toBe(true)
    })
  })

  describe('树形结构展示', () => {
    it('展示部门树形结构转换为 TreeNode', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '' },
      })
      const treeData = wrapper.vm.treeData
      expect(treeData).toBeDefined()
      expect(treeData.length).toBe(1)
      expect(treeData[0].name).toBe('总公司')
      expect(treeData[0].children?.length).toBe(2)
    })

    it('展示部门名称', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '' },
      })
      const treeData = wrapper.vm.treeData
      expect(treeData[0].id).toBe('dept-1')
      expect(treeData[0].name).toBe('总公司')
    })
  })

  describe('节点选择', () => {
    it('单选模式渲染 CheckboxTree', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '', mode: 'single' },
      })
      expect(wrapper.props('mode')).toBe('single')
    })

    it('多选模式渲染 CheckboxTree', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: [], mode: 'multiple' },
      })
      expect(wrapper.props('mode')).toBe('multiple')
    })

    it('支持 v-model 双向绑定', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: 'dept-2', mode: 'single' },
      })
      expect(wrapper.props('modelValue')).toBe('dept-2')
    })
  })

  describe('部门搜索', () => {
    it('CheckboxTree 提供搜索功能', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '' },
      })
      const checkboxTree = wrapper.findComponent({ name: 'CommonCheckboxTree' })
      expect(checkboxTree.exists()).toBe(true)
      expect(checkboxTree.props('searchable')).toBe(true)
    })
  })

  describe('Props 接口', () => {
    it('接受 departments prop', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '' },
      })
      expect(wrapper.props('departments')).toEqual(mockDepartments)
    })

    it('接受 modelValue prop（单选）', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: 'dept-1', mode: 'single' },
      })
      expect(wrapper.props('modelValue')).toBe('dept-1')
    })

    it('接受 modelValue prop（多选）', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: ['dept-1', 'dept-2'], mode: 'multiple' },
      })
      expect(wrapper.props('modelValue')).toEqual(['dept-1', 'dept-2'])
    })

    it('接受 mode prop（single/multiple）', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '', mode: 'single' },
      })
      expect(wrapper.props('mode')).toBe('single')
    })

    it('接受 defaultExpandLevel prop', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '', defaultExpandLevel: 2 },
      })
      expect(wrapper.props('defaultExpandLevel')).toBe(2)
    })

    it('接受 disabled prop', () => {
      const wrapper = mount(DepartmentTree, {
        props: { departments: mockDepartments, modelValue: '', disabled: true },
      })
      expect(wrapper.props('disabled')).toBe(true)
    })
  })
})