import { describe, expect, it, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import OrganizationTree from '@/iam/components/OrganizationTree.vue'
import type { Organization } from '@/iam/types'

const mockOrganizations: Organization[] = [
  {
    id: 'org-1',
    tenant_id: 'tenant-1',
    name: '总公司',
    sort_order: 0,
    status: 'active',
    created_at: '2024-01-01',
    children: [
      {
        id: 'org-2',
        tenant_id: 'tenant-1',
        parent_id: 'org-1',
        name: '研发部',
        sort_order: 0,
        status: 'active',
        created_at: '2024-01-01',
        children: [
          { id: 'org-3', tenant_id: 'tenant-1', parent_id: 'org-2', name: '前端组', sort_order: 0, status: 'active', created_at: '2024-01-01' },
          { id: 'org-4', tenant_id: 'tenant-1', parent_id: 'org-2', name: '后端组', sort_order: 1, status: 'active', created_at: '2024-01-01' },
        ],
      },
      {
        id: 'org-5',
        tenant_id: 'tenant-1',
        parent_id: 'org-1',
        name: '市场部',
        sort_order: 1,
        status: 'active',
        created_at: '2024-01-01',
      },
    ],
  },
]

describe('OrganizationTree', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('基础渲染', () => {
    it('组件存在且可挂载', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '' },
      })
      expect(wrapper.exists()).toBe(true)
    })

    it('渲染 CheckboxTree 组件', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '' },
      })
      expect(wrapper.findComponent({ name: 'CheckboxTree' }).exists()).toBe(true)
    })
  })

  describe('树形结构展示', () => {
    it('展示组织树形结构转换为 TreeNode', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '' },
      })
      const checkboxTree = wrapper.findComponent({ name: 'CheckboxTree' })
      expect(checkboxTree.exists()).toBe(true)
      expect(checkboxTree.props('data')).toBeDefined()
      const data = checkboxTree.props('data') as any[]
      expect(data.length).toBe(1)
      expect(data[0].name).toBe('总公司')
      expect(data[0].children?.length).toBe(2)
    })

    it('展示组织名称', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '' },
      })
      const checkboxTree = wrapper.findComponent({ name: 'CheckboxTree' })
      const data = checkboxTree.props('data') as any[]
      expect(data[0].id).toBe('org-1')
      expect(data[0].name).toBe('总公司')
    })
  })

  describe('节点选择', () => {
    it('单选模式渲染 CheckboxTree', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '', mode: 'single' },
      })
      expect(wrapper.props('mode')).toBe('single')
    })

    it('多选模式渲染 CheckboxTree', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: [], mode: 'multiple' },
      })
      expect(wrapper.props('mode')).toBe('multiple')
    })

    it('支持 v-model 双向绑定', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: 'org-2', mode: 'single' },
      })
      expect(wrapper.props('modelValue')).toBe('org-2')
    })
  })

  describe('组织搜索', () => {
    it('CheckboxTree 提供搜索功能', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '' },
      })
      const checkboxTree = wrapper.findComponent({ name: 'CheckboxTree' })
      expect(checkboxTree.exists()).toBe(true)
      expect(checkboxTree.props('searchable')).toBe(true)
    })
  })

  describe('Props 接口', () => {
    it('接受 organizations prop', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '' },
      })
      expect(wrapper.props('organizations')).toEqual(mockOrganizations)
    })

    it('接受 modelValue prop（单选）', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: 'org-1', mode: 'single' },
      })
      expect(wrapper.props('modelValue')).toBe('org-1')
    })

    it('接受 modelValue prop（多选）', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: ['org-1', 'org-2'], mode: 'multiple' },
      })
      expect(wrapper.props('modelValue')).toEqual(['org-1', 'org-2'])
    })

    it('接受 mode prop（single/multiple）', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '', mode: 'single' },
      })
      expect(wrapper.props('mode')).toBe('single')
    })

    it('接受 defaultExpandLevel prop', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '', defaultExpandLevel: 2 },
      })
      expect(wrapper.props('defaultExpandLevel')).toBe(2)
    })

    it('接受 disabled prop', () => {
      const wrapper = mount(OrganizationTree, {
        props: { organizations: mockOrganizations, modelValue: '', disabled: true },
      })
      expect(wrapper.props('disabled')).toBe(true)
    })
  })
})
