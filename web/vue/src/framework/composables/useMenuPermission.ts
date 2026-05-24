import { useUserStore } from "@/framework/stores/user";

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
 * 根据用户权限动态过滤菜单项
 */
export function useMenuPermission() {
  const userStore = useUserStore();

  /**
   * 检查用户是否有指定权限
   * 支持层级权限键匹配（父级权限键可以覆盖子级）
   */
  function hasPermissionKey(permissionKey: string | undefined): boolean {
    if (!permissionKey) return true;

    const userPermissions = userStore.userInfo?.permissions || [];
    if (userPermissions.length === 0) return true; // 无权限配置时默认显示所有

    // 精确匹配
    if (userPermissions.includes(permissionKey)) return true;

    // 层级匹配：检查父级权限键
    const parts = permissionKey.split(".");
    for (let i = parts.length - 1; i > 0; i--) {
      const parentKey = parts.slice(0, i).join(".");
      if (userPermissions.includes(parentKey)) return true;
    }

    return false;
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
