import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { RouteRecordRaw } from "vue-router";
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
 * 后端菜单 API 响应类型
 */
interface MenuApiResponse {
  id: string;
  name: string;
  path: string;
  icon?: string;
  component?: string;
  permissions?: string[];
  children?: MenuApiResponse[];
}

/**
 * 权限状态管理
 */
export const usePermissionStore = defineStore("permission", () => {
  // 路由列表
  const routes = ref<RouteRecordRaw[]>([]);

  // 菜单列表
  const menus = ref<MenuItem[]>([]);

  // 是否已加载
  const isLoaded = ref(false);

  // 用户 Store
  const userStore = useUserStore();

  // 设置路由
  const setRoutes = (newRoutes: RouteRecordRaw[]) => {
    routes.value = newRoutes;
  };

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

  // 从后端获取用户菜单
  const fetchUserMenus = async (): Promise<MenuApiResponse[]> => {
    // TODO: 替换为真实 API 调用
    // const response = await apiClient.get('/admin/v1/menus');
    // return response.data;

    // Mock 数据 - 根据用户角色返回不同菜单
    const mockMenus: MenuApiResponse[] = [
      {
        id: "1",
        name: "首页",
        path: "/",
        icon: "home",
      },
      {
        id: "2",
        name: "健康检查",
        path: "/health",
        icon: "health",
        permissions: ["health:view"],
      },
      {
        id: "3",
        name: "知识库管理",
        path: "/datasets",
        icon: "database",
        permissions: ["dataset:view"],
        children: [
          {
            id: "3-1",
            name: "知识库列表",
            path: "/datasets",
            icon: "list",
          },
        ],
      },
    ];

    return mockMenus;
  };

  // 将后端菜单转换为路由配置
  const transformMenusToRoutes = (
    menus: MenuApiResponse[],
    asyncRoutes: RouteRecordRaw[]
  ): RouteRecordRaw[] => {
    const result: RouteRecordRaw[] = [];

    for (const menu of menus) {
      // 检查权限
      if (menu.permissions && !hasPermission(menu.permissions)) {
        continue;
      }

      // 查找匹配的异步路由
      const matchedRoute = asyncRoutes.find((r) => r.path === menu.path);

      if (matchedRoute) {
        result.push(matchedRoute);
      }

      // 处理子菜单
      if (menu.children?.length) {
        const childRoutes = transformMenusToRoutes(menu.children, asyncRoutes);
        result.push(...childRoutes);
      }
    }

    return result;
  };

  // 生成动态路由
  const generateRoutes = async (
    asyncRoutes: RouteRecordRaw[]
  ): Promise<RouteRecordRaw[]> => {
    try {
      const menus = await fetchUserMenus();
      const routes = transformMenusToRoutes(menus, asyncRoutes);

      // 转换菜单格式用于侧边栏
      const menuItems: MenuItem[] = menus.map((m) => ({
        id: m.id,
        name: m.name,
        path: m.path,
        icon: m.icon,
        children: m.children,
      }));

      setMenus(menuItems);
      setRoutes(routes);
      setLoaded(true);

      return routes;
    } catch (error) {
      console.error("Failed to generate routes:", error);
      return [];
    }
  };

  // 重置权限
  const resetPermission = () => {
    routes.value = [];
    menus.value = [];
    isLoaded.value = false;
  };

  return {
    routes,
    menus,
    isLoaded,
    setRoutes,
    setMenus,
    setLoaded,
    hasPermission,
    fetchUserMenus,
    generateRoutes,
    resetPermission,
  };
});

export default usePermissionStore;
