/**
 * IAM 模块菜单工具函数
 */
import type { MenuTreeNode } from '@/iam/types'

/**
 * 递归查找菜单节点
 * @param menuList 菜单列表
 * @param id 菜单 ID
 * @returns 找到的菜单节点，未找到返回 null
 */
export const findMenuById = (menuList: MenuTreeNode[], id: string): MenuTreeNode | null => {
  for (const menu of menuList) {
    if (menu.id === id) return menu
    if (menu.children?.length) {
      const found = findMenuById(menu.children, id)
      if (found) return found
    }
  }
  return null
}
