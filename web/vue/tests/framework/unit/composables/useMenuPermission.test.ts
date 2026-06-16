import { describe, it, expect, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useMenuPermission } from "@/framework/composables/useMenuPermission";
import { useUserStore } from "@/framework/stores/user";

describe("useMenuPermission", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe("hasPermissionKey", () => {
    it("returns true when permissionKey is undefined", () => {
      const { hasPermissionKey } = useMenuPermission();

      expect(hasPermissionKey(undefined)).toBe(true);
    });

    it("returns true for any permission key (backend handles filtering)", () => {
      // 注意：后端 user_menu_service 已经根据用户权限过滤了菜单
      // 前端不需要再次进行权限过滤，直接显示后端返回的菜单即可
      const { hasPermissionKey } = useMenuPermission();

      expect(hasPermissionKey("iam.users")).toBe(true);
      expect(hasPermissionKey("iam.roles")).toBe(true);
      expect(hasPermissionKey("any.permission")).toBe(true);
    });

    it("returns true when user has exact permission", () => {
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["admin"],
        permissions: ["iam.users", "iam.roles"],
      });

      const { hasPermissionKey } = useMenuPermission();

      expect(hasPermissionKey("iam.users")).toBe(true);
      expect(hasPermissionKey("iam.roles")).toBe(true);
    });

    it("returns true even when user lacks permission (backend filtering)", () => {
      // 注意：前端不再进行权限检查，始终返回 true
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["user"],
        permissions: ["iam.users"],
      });

      const { hasPermissionKey } = useMenuPermission();

      // 前端不再过滤，由后端负责
      expect(hasPermissionKey("iam.roles")).toBe(true);
      expect(hasPermissionKey("iam.departments")).toBe(true);
    });
  });

  describe("filterMenuItem", () => {
    it("returns item when no permission required", () => {
      const { filterMenuItem } = useMenuPermission();

      const item = { title: "首页", url: "/" };
      expect(filterMenuItem(item)).toEqual(item);
    });

    it("returns item even when permission check would fail (backend filtering)", () => {
      // 注意：前端不再进行权限过滤
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["user"],
        permissions: ["home"],
      });

      const { filterMenuItem } = useMenuPermission();

      const item = { title: "用户管理", url: "/iam/users", permissionKey: "iam.users" };
      // 前端不再过滤，返回原始项
      expect(filterMenuItem(item)).toEqual(item);
    });

    it("returns item with sub-items (backend filtering)", () => {
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["user"],
        permissions: ["home"], // Has "home" but not "iam"
      });

      const { filterMenuItem } = useMenuPermission();

      const item = {
        title: "IAM",
        permissionKey: "iam",
        items: [
          { title: "用户管理", url: "/iam/users", permissionKey: "iam.users" },
        ],
      };

      // 前端不再过滤，返回原始项
      const result = filterMenuItem(item);
      expect(result).not.toBeNull();
      expect(result?.title).toBe("IAM");
      expect(result?.items).toHaveLength(1);
    });

    it("returns null when item has empty sub-items", () => {
      const { filterMenuItem } = useMenuPermission();

      const item = {
        title: "Empty",
        items: [],
      };

      expect(filterMenuItem(item)).toBeNull();
    });
  });

  describe("filterMenuGroups", () => {
    it("returns all items (backend handles filtering)", () => {
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["user"],
        permissions: [],
      });

      const { filterMenuGroups } = useMenuPermission();

      const groups = [
        {
          title: "系统管理",
          items: [
            { title: "用户管理", url: "/iam/users", permissionKey: "iam.users" },
          ],
        },
      ];

      // 前端不再过滤，返回所有项
      expect(filterMenuGroups(groups)).toHaveLength(1);
    });

    it("returns all items regardless of permissions (backend filtering)", () => {
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["admin"],
        permissions: ["home"], // Only has "home" permission
      });

      const { filterMenuGroups } = useMenuPermission();

      const groups = [
        {
          title: "导航",
          items: [
            { title: "首页", url: "/", permissionKey: "home" },
            { title: "用户管理", url: "/iam/users", permissionKey: "iam.users" },
          ],
        },
      ];

      const result = filterMenuGroups(groups);
      expect(result).toHaveLength(1);
      // 前端不再过滤，返回所有项
      expect(result[0].items).toHaveLength(2);
    });

    it("preserves all groups with items", () => {
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["admin"],
        permissions: ["home", "iam.users"],
      });

      const { filterMenuGroups } = useMenuPermission();

      const groups = [
        {
          title: "导航",
          items: [
            { title: "首页", url: "/", permissionKey: "home" },
            { title: "用户管理", url: "/iam/users", permissionKey: "iam.users" },
            { title: "角色管理", url: "/iam/roles", permissionKey: "iam.roles" },
          ],
        },
      ];

      const result = filterMenuGroups(groups);
      expect(result).toHaveLength(1);
      // 前端不再过滤，返回所有项
      expect(result[0].items).toHaveLength(3);
    });
  });
});
