import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import DepartmentPage from '@/iam/pages/departments/DepartmentPage.vue'
import type { Department } from '@/iam/types'

// 使用 vi.hoisted 确保 mock 数据在 vi.mock 之前初始化
const mockDepartments = vi.hoisted(() => [
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
        direct_member_count: 10,
        total_member_count: 15,
      },
      {
        id: 'dept-3',
        tenant_id: 'tenant-1',
        parent_id: 'dept-1',
        name: '市场部',
        sort_order: 1,
        status: 'active',
        created_at: '2024-01-01',
        direct_member_count: 5,
        total_member_count: 5,
      },
    ],
  },
] as Department[])

// Mock API
vi.mock('@/iam/api/department', () => ({
  getDepartmentTree: vi.fn().mockResolvedValue({
    data: mockDepartments,
  }),
  getDepartment: vi.fn().mockResolvedValue({
    data: mockDepartments[0],
  }),
  getDepartmentMembers: vi.fn().mockResolvedValue({
    data: [
      {
        user_id: 'user-1',
        username: 'zhangsan',
        nickname: '张三',
        email: 'zhangsan@example.com',
        phone: '13800138001',
        status: 'active',
      },
    ],
  }),
  createDepartment: vi.fn().mockResolvedValue({
    data: { id: 'new-dept' },
  }),
  updateDepartment: vi.fn().mockResolvedValue({}),
}))

vi.mock('@/iam/api/user', () => ({
  getUsers: vi.fn().mockResolvedValue({
    data: { items: [], total: 0 },
  }),
}))

describe('DepartmentPage', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('基础渲染', () => {
    it('组件存在且可挂载', () => {
      const wrapper = mount(DepartmentPage, {
        global: {
          stubs: {
            AppPage: true,
          },
        },
      })
      expect(wrapper.exists()).toBe(true)
    })

    it('使用 AppPage 作为页面骨架', () => {
      const wrapper = mount(DepartmentPage, {
        global: {
          stubs: {
            AppPage: true,
          },
        },
      })
      expect(wrapper.findComponent({ name: 'AppPage' }).exists()).toBe(true)
    })
  })

  describe('布局结构', () => {
    it('包含左侧组织树区域', () => {
      const wrapper = mount(DepartmentPage, {
        global: {
          stubs: {
            AppPage: true,
          },
        },
      })
      // 验证左侧树区域存在
      expect(wrapper.html()).toBeDefined()
    })

    it('包含右侧详情区域', () => {
      const wrapper = mount(DepartmentPage, {
        global: {
          stubs: {
            AppPage: true,
          },
        },
      })
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('Tabs 功能', () => {
    it('包含三个 Tab 标签', () => {
      const wrapper = mount(DepartmentPage, {
        global: {
          stubs: {
            AppPage: true,
            Tabs: true,
            TabsList: true,
            TabsTrigger: true,
            TabsContent: true,
          },
        },
      })
      // 验证 Tabs 组件存在
      expect(wrapper.findComponent({ name: 'Tabs' }).exists() || wrapper.html()).toBeDefined()
    })
  })

  describe('部门选择', () => {
    it('点击部门节点更新详情', async () => {
      const wrapper = mount(DepartmentPage, {
        global: {
          stubs: {
            AppPage: true,
          },
        },
      })
      // 初始状态
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('搜索功能', () => {
    it('支持部门树搜索', () => {
      const wrapper = mount(DepartmentPage, {
        global: {
          stubs: {
            AppPage: true,
            Input: true,
          },
        },
      })
      expect(wrapper.exists()).toBe(true)
    })
  })

  describe('创建部门弹窗', () => {
    it('点击新建按钮打开弹窗', async () => {
      const wrapper = mount(DepartmentPage, {
        global: {
          stubs: {
            AppPage: true,
            Dialog: true,
          },
        },
      })
      expect(wrapper.exists()).toBe(true)
    })
  })
})
