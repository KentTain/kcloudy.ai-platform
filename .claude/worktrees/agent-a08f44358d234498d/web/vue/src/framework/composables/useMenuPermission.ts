export interface MenuItemWithPermission {
  title: string;
  url: string;
  permissionKey?: string;
  icon?: unknown;
  items?: MenuItemWithPermission[];
}

export interface MenuGroupWithPermission {
  title?: string;
  items: MenuItemWithPermission[];
}

/**
 * 菜单权限过滤组合式函数
 * 注意：后端 user_menu_service 已经根据用户权限过滤了菜单
 * 前端不需要再次进行权限过滤，直接显示后端返回的菜单即可
 */
export function useMenuPermission() {

  /**
   * 检查用户是否有指定权限
   * 注意：后端 user_menu_service 已经根据用户权限过滤了菜单
   * 前端不需要再次进行权限过滤，直接显示后端返回的菜单即可
   */
  function hasPermissionKey(_permissionKey: string | undefined): boolean {
    return true;
  }

  /**
   * 过滤单个菜单项
   */
  function filterMenuItem(item: MenuItemWithPermission): MenuItemWithPermission | null {
    // 检查当前菜单项权限
    if (!hasPermissionKey(item.permissionKey)) return null;

    // 如果有子菜单，递归过滤
    if (item.items) {
      const filteredItems = item.items
        .map(filterMenuItem)
        .filter((i): i is MenuItemWithPermission => i !== null);

      if (filteredItems.length === 0) return null;

      return { ...item, items: filteredItems };
    }

    return item;
  }

  /**
   * 过滤菜单分组
   */
  function filterMenuGroups(groups: MenuGroupWithPermission[]): MenuGroupWithPermission[] {
    return groups
      .map((group) => {
        const filteredItems = group.items
          .map(filterMenuItem)
          .filter((i): i is MenuItemWithPermission => i !== null);

        if (filteredItems.length === 0) return null;

        return { ...group, items: filteredItems };
      })
      .filter((g): g is MenuGroupWithPermission => g !== null);
  }

  return {
    hasPermissionKey,
    filterMenuItem,
    filterMenuGroups,
  };
}
