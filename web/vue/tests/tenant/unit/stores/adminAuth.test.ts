/**
 * Admin Auth Store 测试
 */
import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useAdminAuthStore } from "@/tenant/stores/adminAuth";
import * as adminApi from "@/tenant/api/admin";

// Mock API
vi.mock("@/tenant/api/admin", () => ({
  adminLogin: vi.fn(),
  adminLogout: vi.fn(),
  getCurrentAdmin: vi.fn(),
}));

// 测试数据
const mockAdminInfo = {
  id: "admin-1",
  username: "admin",
  is_default: true,
  is_active: true,
  role: "super_admin",
  permissions: [
    "tenant:tenant:read",
    "tenant:tenant:write",
    "tenant:resource:read",
  ],
  menus: [
    {
      id: "menu-1",
      module_id: "tenant",
      parent_id: null,
      code: "tenant_management",
      name: "租户管理",
      path: "/admin/tenants",
      icon: null,
      sort_order: 1,
      is_visible: true,
      children: [],
    },
  ],
};

describe("Admin Auth Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe("初始状态", () => {
    it("初始化时 role 为空字符串", () => {
      const store = useAdminAuthStore();
      expect(store.role).toBe("");
    });

    it("初始化时 permissions 为空数组", () => {
      const store = useAdminAuthStore();
      expect(store.permissions).toEqual([]);
    });

    it("初始化时 menus 为空数组", () => {
      const store = useAdminAuthStore();
      expect(store.menus).toEqual([]);
    });
  });

  describe("hasPermission", () => {
    it("拥有精确权限码时返回 true", () => {
      const store = useAdminAuthStore();
      store.permissions = ["tenant:tenant:read"];
      expect(store.hasPermission("tenant:tenant:read")).toBe(true);
    });

    it("没有权限码时返回 false", () => {
      const store = useAdminAuthStore();
      store.permissions = ["tenant:tenant:read"];
      expect(store.hasPermission("tenant:module:read")).toBe(false);
    });

    it("拥有通配符 *:*:* 时对所有权限返回 true", () => {
      const store = useAdminAuthStore();
      store.permissions = ["*:*:*"];
      expect(store.hasPermission("tenant:tenant:read")).toBe(true);
      expect(store.hasPermission("tenant:module:write")).toBe(true);
    });

    it("permissions 为空时返回 false", () => {
      const store = useAdminAuthStore();
      expect(store.hasPermission("tenant:tenant:read")).toBe(false);
    });
  });

  describe("hasRole", () => {
    it("角色匹配时返回 true", () => {
      const store = useAdminAuthStore();
      store.role = "super_admin";
      expect(store.hasRole("super_admin")).toBe(true);
    });

    it("角色不匹配时返回 false", () => {
      const store = useAdminAuthStore();
      store.role = "admin";
      expect(store.hasRole("super_admin")).toBe(false);
    });

    it("角色为空时返回 false", () => {
      const store = useAdminAuthStore();
      store.role = "";
      expect(store.hasRole("super_admin")).toBe(false);
    });
  });

  describe("login", () => {
    it("登录成功后调用 getCurrentAdmin 获取完整信息", async () => {
      const loginResponse = {
        code: 200,
        msg: "success",
        data: {
          token: "test-token",
          username: "admin",
          is_default: true,
          role: "super_admin",
          permissions: ["tenant:tenant:read"],
        },
      };
      const adminInfoResponse = {
        code: 200,
        msg: "success",
        data: mockAdminInfo,
      };

      vi.mocked(adminApi.adminLogin).mockResolvedValue(loginResponse as any);
      vi.mocked(adminApi.getCurrentAdmin).mockResolvedValue(
        adminInfoResponse as any
      );

      const store = useAdminAuthStore();
      const result = await store.login({
        username: "admin",
        password: "admin123",
      });

      expect(result).toBe(true);
      expect(adminApi.adminLogin).toHaveBeenCalledWith({
        username: "admin",
        password: "admin123",
      });
      expect(adminApi.getCurrentAdmin).toHaveBeenCalled();

      expect(store.token).toBe("test-token");
      expect(store.role).toBe("super_admin");
      expect(store.permissions).toEqual([
        "tenant:tenant:read",
        "tenant:tenant:write",
        "tenant:resource:read",
      ]);
      expect(store.menus).toEqual(mockAdminInfo.menus);
    });

    it("登录成功后将状态保存到 localStorage", async () => {
      const loginResponse = {
        code: 200,
        msg: "success",
        data: {
          token: "test-token",
          username: "admin",
          is_default: true,
          role: "super_admin",
          permissions: ["tenant:tenant:read"],
        },
      };
      const adminInfoResponse = {
        code: 200,
        msg: "success",
        data: mockAdminInfo,
      };

      vi.mocked(adminApi.adminLogin).mockResolvedValue(loginResponse as any);
      vi.mocked(adminApi.getCurrentAdmin).mockResolvedValue(
        adminInfoResponse as any
      );

      const store = useAdminAuthStore();
      await store.login({ username: "admin", password: "admin123" });

      expect(localStorage.getItem("admin_token")).toBe("test-token");
      expect(localStorage.getItem("admin_role")).toBe("super_admin");
      expect(localStorage.getItem("admin_permissions")).toBe(
        JSON.stringify(mockAdminInfo.permissions)
      );
      expect(localStorage.getItem("admin_menus")).toBe(
        JSON.stringify(mockAdminInfo.menus)
      );
    });

    it("登录失败时返回 false", async () => {
      vi.mocked(adminApi.adminLogin).mockRejectedValue(
        new Error("登录失败")
      );

      const store = useAdminAuthStore();
      const result = await store.login({
        username: "admin",
        password: "wrong",
      });

      expect(result).toBe(false);
    });
  });

  describe("logout", () => {
    it("登出时清除所有状态", async () => {
      const store = useAdminAuthStore();

      // 模拟已登录状态
      store.token = "test-token";
      store.role = "super_admin";
      store.adminInfo = mockAdminInfo as any;
      store.permissions = ["tenant:tenant:read", "tenant:tenant:write"];
      store.menus = mockAdminInfo.menus as any;

      localStorage.setItem("admin_token", "test-token");
      localStorage.setItem("admin_role", "super_admin");

      vi.mocked(adminApi.adminLogout).mockResolvedValue({} as any);

      await store.logout();

      expect(store.token).toBeNull();
      expect(store.adminInfo).toBeNull();
      expect(store.role).toBe("");
      expect(store.permissions).toEqual([]);
      expect(store.menus).toEqual([]);
      expect(localStorage.getItem("admin_token")).toBeNull();
      expect(localStorage.getItem("admin_role")).toBeNull();
      expect(localStorage.getItem("admin_permissions")).toBeNull();
      expect(localStorage.getItem("admin_menus")).toBeNull();
    });
  });

  describe("checkAuth", () => {
    it("从 localStorage 恢复完整状态", () => {
      localStorage.setItem("admin_token", "test-token");
      localStorage.setItem("admin_info", JSON.stringify(mockAdminInfo));
      localStorage.setItem("admin_role", "super_admin");
      localStorage.setItem(
        "admin_permissions",
        JSON.stringify(mockAdminInfo.permissions)
      );
      localStorage.setItem("admin_menus", JSON.stringify(mockAdminInfo.menus));

      const store = useAdminAuthStore();
      const result = store.checkAuth();

      expect(result).toBe(true);
      expect(store.token).toBe("test-token");
      expect(store.adminInfo).toEqual(mockAdminInfo);
      expect(store.role).toBe("super_admin");
      expect(store.permissions).toEqual(mockAdminInfo.permissions);
      expect(store.menus).toEqual(mockAdminInfo.menus);
    });

    it("localStorage 中没有数据时返回 false", () => {
      const store = useAdminAuthStore();
      const result = store.checkAuth();

      expect(result).toBe(false);
      expect(store.role).toBe("");
      expect(store.permissions).toEqual([]);
      expect(store.menus).toEqual([]);
    });
  });

  describe("computed 属性", () => {
    it("isAdmin 在 role 非空时返回 true", () => {
      const store = useAdminAuthStore();
      store.role = "super_admin";
      expect(store.isAdmin).toBe(true);
    });

    it("isAdmin 在 role 为空时返回 false", () => {
      const store = useAdminAuthStore();
      expect(store.isAdmin).toBe(false);
    });

    it("currentRole 返回当前角色编码", () => {
      const store = useAdminAuthStore();
      store.role = "admin";
      expect(store.currentRole).toBe("admin");
    });

    it("currentRole 在角色为空时返回空字符串", () => {
      const store = useAdminAuthStore();
      expect(store.currentRole).toBe("");
    });
  });

  describe("isLoggedIn", () => {
    it("token 存在时 isLoggedIn 为 true", () => {
      const store = useAdminAuthStore();
      store.token = "test-token";
      expect(store.isLoggedIn).toBe(true);
    });

    it("token 为空时 isLoggedIn 为 false", () => {
      const store = useAdminAuthStore();
      store.token = null;
      expect(store.isLoggedIn).toBe(false);
    });
  });
});
