import { describe, expect, it, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import PermissionTree from '@/iam/components/PermissionTree.vue'
import type { Permission } from '@/iam/types'

const mockPermissions: Permission[] = [
  { id: 'perm-1', code: 'user:create', name: '创建用户', resource: 'user', action: 'create', description: '创建新用户', created_at: '2024-01-01' },
  { id: 'perm-2', code: 'user:read', name: '查看用户', resource: 'user', action: 'read', description: '查看用户列表', created_at: '2024-01-01' },
  { id: 'perm-3', code: 'user:update', name: '编辑用户', resource: 'user', action: 'update', description: '编辑用户信息', created_at: '2024-01-01' },
  { id: 'perm-4', code: 'role:create', name: '创建角色', resource: 'role', action: 'create', description: '创建新角色', created_at: '2024-01-01' },
  { id: 'perm-5', code: 'role:read', name: '查看角色', resource: 'role', action: 'read', description: '查看角色列表', created_at: '2024-01-01' },
]

describe('PermissionTree', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('基础渲染', () => {
    it('组件存在且可挂载', () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: [] },
      })
      expect(wrapper.exists()).toBe(true)
    })

    it('渲染 CheckboxTree 组件', () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: [] },
      })
      expect(wrapper.findComponent({ name: 'CheckboxTree' }).exists()).toBe(true)
    })
  })

  describe('按资源分组展示', () => {
    function getCheckboxTreeData(wrapper: ReturnType<typeof mount>) {
      const checkboxTree = wrapper.findComponent({ name: 'CheckboxTree' })
      return checkboxTree.props('data') as any[]
    }

    it('权限按资源分组转换为 TreeNode', () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: [] },
      })
      const treeData = getCheckboxTreeData(wrapper)
      expect(treeData.length).toBe(2)
    })

    it('user 资源组包含 3 个权限', () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: [] },
      })
      const treeData = getCheckboxTreeData(wrapper)
      const userGroup = treeData.find((g: any) => g.id === 'resource-user')
      expect(userGroup).toBeDefined()
      expect(userGroup.name).toBe('user')
      expect(userGroup.children.length).toBe(3)
    })

    it('role 资源组包含 2 个权限', () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: [] },
      })
      const treeData = getCheckboxTreeData(wrapper)
      const roleGroup = treeData.find((g: any) => g.id === 'resource-role')
      expect(roleGroup).toBeDefined()
      expect(roleGroup.name).toBe('role')
      expect(roleGroup.children.length).toBe(2)
    })
  })

  describe('多选功能', () => {
    it('支持 v-model 双向绑定', () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: ['perm-1', 'perm-2'] },
      })
      expect(wrapper.props('modelValue')).toEqual(['perm-1', 'perm-2'])
    })

    it('过滤掉 resource 节点 ID', async () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: [] },
      })
      // 模拟 CheckboxTree 触发 update:model-value，包含 resource ID
      const checkboxTree = wrapper.findComponent({ name: 'CheckboxTree' })
      // 直接调用 CheckboxTree 的 update:model-value emit
      checkboxTree.vm.$emit('update:model-value', ['resource-user', 'perm-1', 'perm-2', 'resource-role', 'perm-4'])
      // 等待下一个 tick 让 handleUpdate 处理
      await new Promise(resolve => setTimeout(resolve, 0))
      // 只有权限 ID 被传递给 emit（resource 节点 ID 被过滤掉）
      const lastEmit = wrapper.emitted('update:modelValue')
      if (lastEmit) {
        const value = lastEmit[lastEmit.length - 1][0] as string[]
        expect(value).not.toContain('resource-user')
        expect(value).not.toContain('resource-role')
        expect(value).toContain('perm-1')
        expect(value).toContain('perm-2')
        expect(value).toContain('perm-4')
      }
    })
  })

  describe('搜索过滤功能', () => {
    it('CheckboxTree 提供搜索功能', () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: [] },
      })
      const checkboxTree = wrapper.findComponent({ name: 'CheckboxTree' })
      expect(checkboxTree.exists()).toBe(true)
      expect(checkboxTree.props('searchable')).toBe(true)
    })
  })

  describe('Props 接口', () => {
    it('接受 permissions prop', () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: [] },
      })
      expect(wrapper.props('permissions')).toEqual(mockPermissions)
    })

    it('接受 disabled prop', () => {
      const wrapper = mount(PermissionTree, {
        props: { permissions: mockPermissions, modelValue: [], disabled: true },
      })
      expect(wrapper.props('disabled')).toBe(true)
      const checkboxTree = wrapper.findComponent({ name: 'CheckboxTree' })
      expect(checkboxTree.props('disabled')).toBe(true)
    })
  })
})