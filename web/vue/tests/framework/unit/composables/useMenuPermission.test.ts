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

    it("returns true when user has no permissions (default show all)", () => {
      const { hasPermissionKey } = useMenuPermission();

      expect(hasPermissionKey("iam.users")).toBe(true);
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

    it("returns true when user has parent permission (hierarchical)", () => {
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["admin"],
        permissions: ["iam"],
      });

      const { hasPermissionKey } = useMenuPermission();

      // Parent permission should cover children
      expect(hasPermissionKey("iam.users")).toBe(true);
      expect(hasPermissionKey("iam.roles")).toBe(true);
      expect(hasPermissionKey("iam.departments")).toBe(true);
    });

    it("returns false when user lacks permission", () => {
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["user"],
        permissions: ["iam.users"],
      });

      const { hasPermissionKey } = useMenuPermission();

      expect(hasPermissionKey("iam.roles")).toBe(false);
      expect(hasPermissionKey("iam.departments")).toBe(false);
    });
  });

  describe("filterMenuItem", () => {
    it("returns item when no permission required", () => {
      const { filterMenuItem } = useMenuPermission();

      const item = { title: "首页", url: "/" };
      expect(filterMenuItem(item)).toEqual(item);
    });

    it("returns null when permission check fails", () => {
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
      expect(filterMenuItem(item)).toBeNull();
    });

    it("filters sub-items when parent has no permission", () => {
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

      expect(filterMenuItem(item)).toBeNull();
    });
  });

  describe("filterMenuGroups", () => {
    it("returns all items when user has no permissions set (backward compatible)", () => {
      const userStore = useUserStore();
      userStore.setUserInfo({
        id: "1",
        username: "test",
        nickname: "Test User",
        roles: ["user"],
        permissions: [], // Empty permissions = show all (backward compatible)
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

      // When permissions array is empty, all items are shown
      expect(filterMenuGroups(groups)).toHaveLength(1);
    });

    it("filters items when user has specific permissions", () => {
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
      expect(result[0].items).toHaveLength(1);
      expect(result[0].items[0].title).toBe("首页");
    });

    it("preserves groups with accessible items", () => {
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
      expect(result[0].items).toHaveLength(2);
    });
  });
});
