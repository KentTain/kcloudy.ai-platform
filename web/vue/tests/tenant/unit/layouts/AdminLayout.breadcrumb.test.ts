import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import type { AdminMenuItem } from '@/tenant/stores/adminMenu'

/**
 * 测试面包屑逻辑
 */
describe('AdminLayout Breadcrumb Logic', () => {
  // 模拟菜单数据
  const mockAdminMenus = ref<AdminMenuItem[]>([
    {
      id: 'e72cb152-8efa-4fc5-9352-4738a8e4fb6a',
      module_id: 'e72cb152-8efa-4fc5-9352-4738a8e4fb6a',
      parent_id: null,
      code: 'tenant',
      name: '租户管理',
      path: '',
      icon: 'Organization',
      sort_order: 0,
      is_visible: true,
      children: [
        {
          id: '818e983c-1c09-413a-9677-5b010858dc95',
          module_id: 'e72cb152-8efa-4fc5-9352-4738a8e4fb6a',
          parent_id: 'root',
          code: 'tenant.tenants',
          name: '租户管理',
          path: '/admin/tenants',
          icon: 'Organization',
          sort_order: 2,
          is_visible: true,
          children: []
        },
        {
          id: '5238a616-6f67-464d-9d18-395a5ad3b800',
          module_id: 'e72cb152-8efa-4fc5-9352-4738a8e4fb6a',
          parent_id: 'root',
          code: 'tenant.modules',
          name: '模块管理',
          path: '/admin/modules',
          icon: 'Puzzle',
          sort_order: 1,
          is_visible: true,
          children: []
        }
      ]
    }
  ])

  /**
   * 检查路径是否匹配二级菜单
   */
  function isSecondaryMenuPath(path: string, menus: AdminMenuItem[]): boolean {
    for (const module of menus) {
      const matched = module.children?.some((child) => child.path === path)
      if (matched) return true
    }
    return false
  }

  /**
   * 检查路由路径是否匹配动态路由模式
   */
  function isDynamicRoutePath(path: string, menuPath: string): boolean {
    const pattern = `^${menuPath}(/[^/]+)?$`
    return new RegExp(pattern).test(path)
  }

  /**
   * 从路由路径中提取二级菜单路径
   */
  function extractMenuPath(path: string, menus: AdminMenuItem[]): string | null {
    for (const module of menus) {
      for (const child of module.children || []) {
        if (child.path && isDynamicRoutePath(path, child.path)) {
          return child.path
        }
      }
    }
    return null
  }

  describe('isSecondaryMenuPath', () => {
    it('应该识别二级菜单路径', () => {
      expect(isSecondaryMenuPath('/admin/tenants', mockAdminMenus.value)).toBe(true)
      expect(isSecondaryMenuPath('/admin/modules', mockAdminMenus.value)).toBe(true)
    })

    it('应该正确识别非二级菜单路径', () => {
      expect(isSecondaryMenuPath('/admin/tenants/abc', mockAdminMenus.value)).toBe(false)
      expect(isSecondaryMenuPath('/admin/tenants/create', mockAdminMenus.value)).toBe(false)
    })
  })

  describe('isDynamicRoutePath', () => {
    it('应该匹配精确路径', () => {
      expect(isDynamicRoutePath('/admin/tenants', '/admin/tenants')).toBe(true)
    })

    it('应该匹配动态路由参数', () => {
      expect(isDynamicRoutePath('/admin/tenants/abc-123', '/admin/tenants')).toBe(true)
    })

    it('应该匹配子路径', () => {
      expect(isDynamicRoutePath('/admin/tenants/create', '/admin/tenants')).toBe(true)
    })

    it('不应该匹配不相关的路径', () => {
      expect(isDynamicRoutePath('/admin/modules', '/admin/tenants')).toBe(false)
    })
  })

  describe('extractMenuPath', () => {
    it('应该从精确路径提取菜单路径', () => {
      expect(extractMenuPath('/admin/tenants', mockAdminMenus.value)).toBe('/admin/tenants')
    })

    it('应该从动态路由路径提取菜单路径', () => {
      expect(extractMenuPath('/admin/tenants/abc-123', mockAdminMenus.value)).toBe('/admin/tenants')
    })

    it('应该从子路径提取菜单路径', () => {
      expect(extractMenuPath('/admin/tenants/create', mockAdminMenus.value)).toBe('/admin/tenants')
    })

    it('应该返回 null 当路径不匹配任何菜单时', () => {
      expect(extractMenuPath('/unknown/path', mockAdminMenus.value)).toBe(null)
    })
  })
})
