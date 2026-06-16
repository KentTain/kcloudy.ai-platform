import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  getRoles,
  getRole,
  createRole,
  updateRole,
  deleteRole,
  getRolePermissions,
  assignRolePermissions,
} from "@/iam/api/role";
import * as client from "@/framework/api/client";

vi.mock("@/framework/api/client", () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}));

describe("Role API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getRoles", () => {
    it("calls GET /iam/admin/v1/roles with params", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { items: [], total: 0, page: 1, page_size: 20 },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getRoles({ page: 1, keyword: "admin" });

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/roles", { params: { page: 1, keyword: "admin" } });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getRole", () => {
    it("calls GET /iam/admin/v1/roles/:id", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", code: "admin", name: "管理员", is_system: false, created_at: "2024-01-01" },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getRole("1");

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/roles/1");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("createRole", () => {
    it("calls POST /iam/admin/v1/roles with role data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", code: "editor", name: "编辑", is_system: false, created_at: "2024-01-01" },
      };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await createRole({
        code: "editor",
        name: "编辑",
        description: "编辑角色",
      });

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/roles", {
        code: "editor",
        name: "编辑",
        description: "编辑角色",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("updateRole", () => {
    it("calls PUT /iam/admin/v1/roles/:id with update data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", code: "editor", name: "高级编辑", is_system: false, created_at: "2024-01-01" },
      };
      vi.mocked(client.put).mockResolvedValue(mockResponse);

      const result = await updateRole("1", { name: "高级编辑" });

      expect(client.put).toHaveBeenCalledWith("/iam/admin/v1/roles/1", { name: "高级编辑" });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("deleteRole", () => {
    it("calls DELETE /iam/admin/v1/roles/:id", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.del).mockResolvedValue(mockResponse);

      const result = await deleteRole("1");

      expect(client.del).toHaveBeenCalledWith("/iam/admin/v1/roles/1");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getRolePermissions", () => {
    it("calls GET /iam/admin/v1/roles/:id/permissions", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [
          { id: "perm-1", code: "user:read", name: "查看用户", resource: "user", action: "read", created_at: "2024-01-01" },
        ],
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getRolePermissions("1");

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/roles/1/permissions");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("assignRolePermissions", () => {
    it("calls POST /iam/admin/v1/roles/:id/permissions with permission ids", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await assignRolePermissions("1", { permission_ids: ["perm-1", "perm-2"] });

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/roles/1/permissions", {
        permission_ids: ["perm-1", "perm-2"],
      });
      expect(result).toEqual(mockResponse);
    });
  });
});
