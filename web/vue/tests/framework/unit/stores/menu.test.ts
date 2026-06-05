import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useMenuStore } from "@/framework/stores/menu";

// Mock apiClient
vi.mock("@/framework/api/client", () => ({
  get: vi.fn(),
}));

import { get } from "@/framework/api/client";

const mockGet = vi.mocked(get);

describe("useMenuStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe("fetchMenus", () => {
    it("成功获取菜单", async () => {
      const mockMenus = [
        {
          id: "1",
          name: "首页",
          path: "/",
          module: "demo",
          code: "home",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "首页",
          parent_ids: "",
          is_visible: true,
          children: [],
        },
      ];

      mockGet.mockResolvedValueOnce({ menus: mockMenus });

      const store = useMenuStore();
      await store.fetchMenus();

      expect(store.menus[0].id).toBe("1");
      expect(store.menus[0].name).toBe("首页");
      expect(store.menus[0].isExternal).toBe(false);
      expect(store.loading).toBe(false);
      expect(store.error).toBeNull();
    });

    it("获取菜单失败时设置错误信息", async () => {
      mockGet.mockRejectedValueOnce(new Error("Network error"));

      const store = useMenuStore();
      await store.fetchMenus();

      expect(store.error).toBe("Network error");
      expect(store.loading).toBe(false);
    });

    it("加载状态正确切换", async () => {
      const mockMenus = [
        {
          id: "1",
          name: "首页",
          path: "/",
          module: "demo",
          code: "home",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "首页",
          parent_ids: "",
          is_visible: true,
          children: [],
        },
      ];

      mockGet.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve({ menus: mockMenus }), 100)
          )
      );

      const store = useMenuStore();
      const promise = store.fetchMenus();

      expect(store.loading).toBe(true);

      await promise;

      expect(store.loading).toBe(false);
    });
  });

  describe("跨子域名菜单处理", () => {
    it("同域菜单 isExternal 为 false", async () => {
      const mockMenus = [
        {
          id: "1",
          name: "首页",
          path: "/",
          module: "demo",
          code: "home",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "首页",
          parent_ids: "",
          is_visible: true,
          deployment_base_url: null,
          children: [],
        },
      ];

      mockGet.mockResolvedValueOnce({ menus: mockMenus });

      const store = useMenuStore();
      await store.fetchMenus();

      expect(store.menus[0].isExternal).toBe(false);
    });

    it("跨域菜单 isExternal 为 true", async () => {
      const mockMenus = [
        {
          id: "1",
          name: "外部模块",
          path: "/external",
          module: "external",
          code: "external",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "外部模块",
          parent_ids: "",
          is_visible: true,
          deployment_base_url: "https://external.example.com",
          children: [],
        },
      ];

      mockGet.mockResolvedValueOnce({ menus: mockMenus });

      const store = useMenuStore();
      await store.fetchMenus();

      expect(store.menus[0].isExternal).toBe(true);
      expect(store.menus[0].externalUrl).toBe("https://external.example.com/external");
    });

    it("子菜单的跨域处理", async () => {
      const mockMenus = [
        {
          id: "1",
          name: "外部模块",
          path: "/external",
          module: "external",
          code: "external",
          tree_level: 0,
          tree_leaf: false,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "外部模块",
          parent_ids: "",
          is_visible: true,
          deployment_base_url: "https://external.example.com",
          children: [
            {
              id: "2",
              name: "子菜单",
              path: "/external/sub",
              module: "external",
              code: "external_sub",
              tree_level: 1,
              tree_leaf: true,
              tree_sort: 0,
              tree_sorts: "0.0",
              tree_names: "外部模块/子菜单",
              parent_ids: "1",
              parent_id: "1",
              is_visible: true,
              deployment_base_url: "https://external.example.com",
              children: [],
            },
          ],
        },
      ];

      mockGet.mockResolvedValueOnce({ menus: mockMenus });

      const store = useMenuStore();
      await store.fetchMenus();

      expect(store.menus[0].isExternal).toBe(true);
      expect(store.menus[0].children?.[0]?.isExternal).toBe(true);
    });
  });

  describe("菜单缓存", () => {
    it("使用缓存菜单", async () => {
      const cachedMenus = [
        {
          id: "1",
          name: "缓存菜单",
          path: "/cached",
          module: "demo",
          code: "cached",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "缓存菜单",
          parent_ids: "",
          is_visible: true,
          children: [],
          isExternal: false,
        },
      ];

      // 设置缓存
      localStorage.setItem(
        "menu_cache",
        JSON.stringify({
          data: cachedMenus,
          timestamp: Date.now(),
        })
      );

      const freshMenus = [
        {
          id: "2",
          name: "新菜单",
          path: "/fresh",
          module: "demo",
          code: "fresh",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "新菜单",
          parent_ids: "",
          is_visible: true,
          children: [],
        },
      ];

      let resolveApi: () => void;
      mockGet.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveApi = () => resolve({ menus: freshMenus });
          })
      );

      const store = useMenuStore();
      const fetchPromise = store.fetchMenus();

      // 验证立即返回缓存数据
      expect(store.menus[0].id).toBe("1");
      expect(store.menus[0].name).toBe("缓存菜单");
      expect(mockGet).toHaveBeenCalled();

      // 完成后台更新
      resolveApi!();
      await fetchPromise;
    });

    it("强制刷新忽略缓存", async () => {
      const cachedMenus = [
        {
          id: "1",
          name: "缓存菜单",
          path: "/cached",
          module: "demo",
          code: "cached",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "缓存菜单",
          parent_ids: "",
          is_visible: true,
          children: [],
          isExternal: false,
        },
      ];

      // 设置缓存
      localStorage.setItem(
        "menu_cache",
        JSON.stringify({
          data: cachedMenus,
          timestamp: Date.now(),
        })
      );

      const freshMenus = [
        {
          id: "2",
          name: "新菜单",
          path: "/fresh",
          module: "demo",
          code: "fresh",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "新菜单",
          parent_ids: "",
          is_visible: true,
          children: [],
        },
      ];

      mockGet.mockResolvedValueOnce({ menus: freshMenus });

      const store = useMenuStore();
      await store.fetchMenus({ force: true });

      expect(store.menus[0].id).toBe("2");
      expect(store.menus[0].name).toBe("新菜单");
    });

    it("过期缓存不使用", async () => {
      const expiredTime = Date.now() - 6 * 60 * 1000; // 6分钟前（超过5分钟过期）

      const cachedMenus = [
        {
          id: "1",
          name: "过期缓存",
          path: "/expired",
          module: "demo",
          code: "expired",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "过期缓存",
          parent_ids: "",
          is_visible: true,
          children: [],
        },
      ];

      // 设置过期缓存
      localStorage.setItem(
        "menu_cache",
        JSON.stringify({
          data: cachedMenus,
          timestamp: expiredTime,
        })
      );

      const freshMenus = [
        {
          id: "2",
          name: "新菜单",
          path: "/fresh",
          module: "demo",
          code: "fresh",
          tree_level: 0,
          tree_leaf: true,
          tree_sort: 0,
          tree_sorts: "0",
          tree_names: "新菜单",
          parent_ids: "",
          is_visible: true,
          children: [],
        },
      ];

      mockGet.mockResolvedValueOnce({ menus: freshMenus });

      const store = useMenuStore();
      await store.fetchMenus();

      expect(store.menus[0].id).toBe("2");
      expect(store.menus[0].name).toBe("新菜单");
    });
  });
});
