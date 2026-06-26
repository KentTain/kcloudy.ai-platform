import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useRoleStore } from "@/iam/stores/role";
import * as roleApi from "@/iam/api/role";

vi.mock("@/iam/api/role", () => ({
  getRoles: vi.fn(),
  getRole: vi.fn(),
  createRole: vi.fn(),
  updateRole: vi.fn(),
  deleteRole: vi.fn(),
  getRolePermissions: vi.fn(),
  assignRolePermissions: vi.fn(),
}));

describe("Role Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("fetchRoles", () => {
    it("fetches role list and sets roles", async () => {
      const mockResponse = {
        code: 200,
        msg: "success",
        data: [
          { id: "1", code: "admin", name: "管理员", is_system: false, created_at: "2024-01-01" },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      };
      vi.mocked(roleApi.getRoles).mockResolvedValue(mockResponse);

      const store = useRoleStore();
      await store.fetchRoles({ page: 1 });

      expect(roleApi.getRoles).toHaveBeenCalledWith({ page: 1 });
      expect(store.roles).toEqual(mockResponse.data);
      expect(store.total).toBe(1);
    });
  });

  describe("fetchRole", () => {
    it("fetches single role and sets currentRole", async () => {
      const mockResponse = {
        code: 200,
        msg: "success",
        data: { id: "1", code: "admin", name: "管理员", is_system: false, created_at: "2024-01-01" },
      };
      vi.mocked(roleApi.getRole).mockResolvedValue(mockResponse);

      const store = useRoleStore();
      await store.fetchRole("1");

      expect(roleApi.getRole).toHaveBeenCalledWith("1");
      expect(store.currentRole).toEqual(mockResponse.data);
    });
  });

  describe("addRole", () => {
    it("creates role and returns new role", async () => {
      const mockResponse = {
        code: 200,
        msg: "success",
        data: { id: "1", code: "editor", name: "编辑", is_system: false, created_at: "2024-01-01" },
      };
      vi.mocked(roleApi.createRole).mockResolvedValue(mockResponse);

      const store = useRoleStore();
      const result = await store.addRole({ code: "editor", name: "编辑" });

      expect(roleApi.createRole).toHaveBeenCalledWith({ code: "editor", name: "编辑" });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe("editRole", () => {
    it("updates role", async () => {
      const mockResponse = {
        code: 200,
        msg: "success",
        data: { id: "1", code: "editor", name: "高级编辑", is_system: false, created_at: "2024-01-01" },
      };
      vi.mocked(roleApi.updateRole).mockResolvedValue(mockResponse);

      const store = useRoleStore();
      await store.editRole("1", { name: "高级编辑" });

      expect(roleApi.updateRole).toHaveBeenCalledWith("1", { name: "高级编辑" });
    });
  });

  describe("removeRole", () => {
    it("deletes role", async () => {
      vi.mocked(roleApi.deleteRole).mockResolvedValue({ code: 0, msg: "success", data: undefined });

      const store = useRoleStore();
      await store.removeRole("1");

      expect(roleApi.deleteRole).toHaveBeenCalledWith("1");
    });
  });

  describe("fetchRolePermissions", () => {
    it("fetches role permissions", async () => {
      const mockResponse = {
        code: 200,
        msg: "success",
        data: [
          { id: "perm-1", code: "user:read", name: "查看用户", resource: "user", action: "read", created_at: "2024-01-01" },
        ],
      };
      vi.mocked(roleApi.getRolePermissions).mockResolvedValue(mockResponse);

      const store = useRoleStore();
      await store.fetchRolePermissions("1");

      expect(roleApi.getRolePermissions).toHaveBeenCalledWith("1");
      expect(store.currentRolePermissions).toEqual(mockResponse.data);
    });
  });

  describe("updateRolePermissions", () => {
    it("assigns permissions to role", async () => {
      vi.mocked(roleApi.assignRolePermissions).mockResolvedValue({ code: 0, msg: "success", data: undefined });

      const store = useRoleStore();
      await store.updateRolePermissions("1", ["perm-1", "perm-2"]);

      expect(roleApi.assignRolePermissions).toHaveBeenCalledWith("1", {
        permission_ids: ["perm-1", "perm-2"],
      });
    });
  });
});
