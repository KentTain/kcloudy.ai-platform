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

  // 从后端获取用户菜单并过滤权限
  const fetchUserMenus = async (): Promise<void> => {
    // TODO: 替换为真实 API 调用
    // const response = await apiClient.get('/admin/v1/menus');
    // const menus = response.data;

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
      },
      {
        id: "4",
        name: "系统管理",
        path: "/iam",
        icon: "settings",
        children: [
          {
            id: "4-1",
            name: "用户管理",
            path: "/iam/users",
            icon: "user",
            permissions: ["iam:user:view"],
          },
          {
            id: "4-2",
            name: "角色管理",
            path: "/iam/roles",
            icon: "role",
            permissions: ["iam:role:view"],
          },
          {
            id: "4-3",
            name: "权限管理",
            path: "/iam/permissions",
            icon: "lock",
            permissions: ["iam:permission:view"],
          },
          {
            id: "4-4",
            name: "部门管理",
            path: "/iam/departments",
            icon: "department",
            permissions: ["iam:department:view"],
          },
        ],
      },
    ];

    // 过滤菜单（根据权限）
    const filterMenus = (menus: MenuApiResponse[]): MenuApiResponse[] => {
      return menus
        .filter((menu) => {
          if (menu.permissions && menu.permissions.length > 0) {
            return hasPermission(menu.permissions);
          }
          return true;
        })
        .map((menu) => ({
          ...menu,
          children: menu.children ? filterMenus(menu.children) : undefined,
        }))
        .filter((menu) => {
          // 如果父菜单没有权限要求但所有子菜单都被过滤掉了，也隐藏父菜单
          if (!menu.permissions && menu.children && menu.children.length === 0) {
            return false;
          }
          return true;
        });
    };

    const filteredMenus = filterMenus(mockMenus);

    // 转换菜单格式用于侧边栏
    const menuItems: MenuItem[] = filteredMenus.map((m) => ({
      id: m.id,
      name: m.name,
      path: m.path,
      icon: m.icon,
      children: m.children,
    }));

    setMenus(menuItems);
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
    fetchUserMenus,
    resetPermission,
  };
});

export default usePermissionStore;
