import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useAppStore } from "@/framework/stores/app";
import { useUserStore } from "@/framework/stores/user";
import { usePermissionStore } from "@/framework/stores/permission";

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock });

describe("Permission System", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorageMock.clear();
  });

  describe("AppStore", () => {
    it("initializes with default state", () => {
      const store = useAppStore();

      expect(store.sidebarCollapsed).toBe(false);
      expect(store.device).toBe("desktop");
    });

    it("toggles sidebar", () => {
      const store = useAppStore();

      store.toggleSidebar();
      expect(store.sidebarCollapsed).toBe(true);

      store.toggleSidebar();
      expect(store.sidebarCollapsed).toBe(false);
    });

    it("sets device type", () => {
      const store = useAppStore();

      store.setDevice("mobile");
      expect(store.device).toBe("mobile");
      expect(store.sidebarCollapsed).toBe(true);
    });
  });

  describe("UserStore", () => {
    it("initializes with default state", () => {
      const store = useUserStore();

      expect(store.userInfo).toBeNull();
      expect(store.isLoggedIn).toBe(false);
    });

    it("sets token", () => {
      const store = useUserStore();

      store.setToken("test-token");

      expect(store.token).toBe("test-token");
      expect(localStorageMock.setItem).toHaveBeenCalledWith("token", "test-token");
    });

    it("sets user info", () => {
      const store = useUserStore();
      const userInfo = {
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["admin"],
        permissions: ["*"],
      };

      store.setUserInfo(userInfo);

      expect(store.userInfo).toEqual(userInfo);
    });

    it("checks permission correctly", () => {
      const store = useUserStore();

      store.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["admin"],
        permissions: ["user:add", "user:edit"],
      });

      expect(store.hasPermission("user:add")).toBe(true);
      expect(store.hasPermission("user:delete")).toBe(false);
    });

    it("checks role correctly", () => {
      const store = useUserStore();

      store.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["admin"],
        permissions: [],
      });

      expect(store.hasRole("admin")).toBe(true);
      expect(store.hasRole("user")).toBe(false);
    });

    it("logs out correctly", () => {
      const store = useUserStore();

      store.setToken("test-token");
      store.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["admin"],
        permissions: [],
      });

      store.logout();

      expect(store.token).toBeNull();
      expect(store.userInfo).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("token");
    });
  });

  describe("PermissionStore", () => {
    it("initializes with default state", () => {
      const store = usePermissionStore();

      expect(store.routes).toEqual([]);
      expect(store.menus).toEqual([]);
      expect(store.isLoaded).toBe(false);
    });

    it("sets routes", () => {
      const store = usePermissionStore();
      const routes = [{ path: "/test", name: "Test" }] as any;

      store.setRoutes(routes);

      expect(store.routes).toEqual(routes);
    });

    it("sets menus", () => {
      const store = usePermissionStore();
      const menus = [{ id: "1", name: "Test", path: "/test" }];

      store.setMenus(menus);

      expect(store.menus).toEqual(menus);
    });

    it("resets permission", () => {
      const store = usePermissionStore();

      store.setRoutes([{ path: "/test" }] as any);
      store.setMenus([{ id: "1", name: "Test", path: "/test" }]);
      store.setLoaded(true);

      store.resetPermission();

      expect(store.routes).toEqual([]);
      expect(store.menus).toEqual([]);
      expect(store.isLoaded).toBe(false);
    });
  });
});
