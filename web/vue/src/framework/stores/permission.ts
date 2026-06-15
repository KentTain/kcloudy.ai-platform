import { defineStore } from "pinia";
import { ref } from "vue";
import { useUserStore } from "./user";

/**
 * 菜单项类型
 */
export interface MenuItem {
  id: string;
  name: string;
  path: string;
  icon?: string;
  children?: MenuItem[];
}

/**
 * 权限状态管理
 */
export const usePermissionStore = defineStore("permission", () => {
  // 菜单列表
  const menus = ref<MenuItem[]>([]);

  // 是否已加载
  const isLoaded = ref(false);

  // 用户 Store
  const userStore = useUserStore();

  // 设置菜单
  const setMenus = (newMenus: MenuItem[]) => {
    menus.value = newMenus;
  };

  // 设置加载状态
  const setLoaded = (loaded: boolean) => {
    isLoaded.value = loaded;
  };

  // 检查权限
  const hasPermission = (permissions: string | string[]): boolean => {
    if (!userStore.userInfo) return false;

    const permissionList = Array.isArray(permissions) ? permissions : [permissions];
    return permissionList.some((p) => userStore.hasPermission(p));
  };

  // 重置权限
  const resetPermission = () => {
    menus.value = [];
    isLoaded.value = false;
  };

  return {
    menus,
    isLoaded,
    setMenus,
    setLoaded,
    hasPermission,
    resetPermission,
  };
});

export default usePermissionStore;
