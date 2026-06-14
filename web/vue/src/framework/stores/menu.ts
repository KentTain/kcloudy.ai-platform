import { defineStore } from "pinia";
import { ref } from "vue";
import { get } from "@/framework/api/client";
import type { UserMenuVo } from "@/framework/api/menu";

/**
 * 菜单树节点
 */
export interface MenuTreeNode {
  id: string;
  parent_id?: string | null;
  tree_level: number;
  tree_leaf: boolean;
  tree_sort: number;
  tree_sorts: string;
  tree_names: string;
  parent_ids: string;
  module: string;
  code: string;
  name: string;
  path: string;
  icon?: string | null;
  is_visible: boolean;
  deployment_base_url?: string | null;
  children: MenuTreeNode[];
  /** 计算属性：是否为跨域菜单 */
  isExternal?: boolean;
  /** 计算属性：外部完整 URL */
  externalUrl?: string;
}

/**
 * 用户菜单项（用于前端导航）
 */
export interface UserMenuItem {
  id: string;
  code: string;
  name: string;
  icon: string | null;
  path: string | null;
  sortOrder: number;
  children: UserMenuItem[];
}

/**
 * 菜单列表响应
 */
interface MenuListResponse {
  menus: MenuTreeNode[];
}

/**
 * 菜单缓存结构
 */
interface MenuCache {
  data: MenuTreeNode[];
  timestamp: number;
}

/** 缓存过期时间：5 分钟 */
const CACHE_TTL = 5 * 60 * 1000;

/** 缓存 Key */
const CACHE_KEY = "menu_cache";

/**
 * 菜单状态管理
 */
export const useMenuStore = defineStore("menu", () => {
  /** 后台管理菜单树（用于 IAM 菜单管理） */
  const menus = ref<MenuTreeNode[]>([]);
  /** 用户导航菜单（用于前端导航） */
  const userMenus = ref<UserMenuItem[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  /**
   * 处理菜单树，添加 isExternal 和 externalUrl 属性
   */
  function processMenuTree(items: MenuTreeNode[]): MenuTreeNode[] {
    return items.map((item) => {
      const isExternal = !!item.deployment_base_url;
      const externalUrl = isExternal
        ? `${item.deployment_base_url}${item.path}`
        : undefined;

      return {
        ...item,
        isExternal,
        externalUrl,
        children: item.children?.length ? processMenuTree(item.children) : [],
      };
    });
  }

  /**
   * 将 UserMenuVo 转换为 UserMenuItem
   */
  function convertToUserMenuItem(vo: UserMenuVo): UserMenuItem {
    return {
      id: vo.id,
      code: vo.code,
      name: vo.name,
      icon: vo.icon,
      path: vo.path,
      sortOrder: vo.sort_order,
      children: vo.children?.map(convertToUserMenuItem) || [],
    };
  }

  /**
   * 获取缓存数据
   */
  function getCache(): MenuCache | null {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (!cached) return null;

      const parsed = JSON.parse(cached) as MenuCache;
      const isExpired = Date.now() - parsed.timestamp > CACHE_TTL;

      return isExpired ? null : parsed;
    } catch {
      return null;
    }
  }

  /**
   * 设置缓存数据
   */
  function setCache(data: MenuTreeNode[]): void {
    try {
      localStorage.setItem(
        CACHE_KEY,
        JSON.stringify({
          data,
          timestamp: Date.now(),
        })
      );
    } catch {
      // 忽略存储错误
    }
  }

  /**
   * 获取后台管理菜单数据（用于 IAM 菜单管理）
   * @param options.force 强制刷新，忽略缓存
   */
  async function fetchMenus(options?: { force?: boolean }): Promise<void> {
    // 检查缓存
    if (!options?.force) {
      const cache = getCache();
      if (cache) {
        menus.value = cache.data;
        // 后台静默更新
        void fetchFromApi(true);
        return;
      }
    }

    await fetchFromApi(false);
  }

  /**
   * 从 API 获取后台管理菜单
   * @param silent 静默模式，不更新 loading 状态
   */
  async function fetchFromApi(silent: boolean): Promise<void> {
    if (!silent) {
      loading.value = true;
      error.value = null;
    }

    try {
      const response = await get<MenuListResponse>("/v1/menus/user");
      const processedMenus = processMenuTree(response.menus);
      menus.value = processedMenus;
      setCache(processedMenus);
    } catch (err) {
      error.value = err instanceof Error ? err.message : "获取菜单失败";
    } finally {
      if (!silent) {
        loading.value = false;
      }
    }
  }

  /**
   * 获取用户导航菜单
   */
  async function fetchUserMenus(): Promise<void> {
    loading.value = true;
    error.value = null;

    try {
      const { getUserMenus } = await import("@/framework/api/menu");
      const response = await getUserMenus();
      userMenus.value = response.data.map(convertToUserMenuItem);
    } catch (err) {
      error.value = err instanceof Error ? err.message : "加载菜单失败";
      console.error("Failed to fetch user menus:", err);
    } finally {
      loading.value = false;
    }
  }

  /**
   * 清空菜单状态
   */
  function clearMenus(): void {
    menus.value = [];
    userMenus.value = [];
    error.value = null;
    localStorage.removeItem(CACHE_KEY);
  }

  return {
    menus,
    userMenus,
    loading,
    error,
    fetchMenus,
    fetchUserMenus,
    clearMenus,
  };
});

export default useMenuStore;
