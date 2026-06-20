import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  getUsers,
  getUser,
  createUser,
  updateUser,
  deleteUser,
  assignUserRoles,
  assignUserOrganizations,
  resetUserPassword,
} from "@/iam/api/user";
import * as client from "@/framework/api/client";

vi.mock("@/framework/api/client", () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}));

describe("User API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getUsers", () => {
    it("calls GET /iam/admin/v1/users with params", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { items: [], total: 0, page: 1, page_size: 20 },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getUsers({ page: 1, keyword: "admin" });

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/users", { params: { page: 1, keyword: "admin" } });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getUser", () => {
    it("calls GET /iam/admin/v1/users/:id", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", username: "admin", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getUser("1");

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/users/1");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("createUser", () => {
    it("calls POST /iam/admin/v1/users with user data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", username: "newuser", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await createUser({
        username: "newuser",
        password: "password",
        email: "new@example.com",
      });

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/users", {
        username: "newuser",
        password: "password",
        email: "new@example.com",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("updateUser", () => {
    it("calls PUT /iam/admin/v1/users/:id with update data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", username: "admin", nickname: "Admin", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(client.put).mockResolvedValue(mockResponse);

      const result = await updateUser("1", { nickname: "Admin" });

      expect(client.put).toHaveBeenCalledWith("/iam/admin/v1/users/1", { nickname: "Admin" });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("deleteUser", () => {
    it("calls DELETE /iam/admin/v1/users/:id", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.del).mockResolvedValue(mockResponse);

      const result = await deleteUser("1");

      expect(client.del).toHaveBeenCalledWith("/iam/admin/v1/users/1");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("assignUserRoles", () => {
    it("calls POST /iam/admin/v1/users/:id/roles with role ids", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await assignUserRoles("1", ["role-1", "role-2"]);

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/users/1/roles", {
        role_ids: ["role-1", "role-2"],
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("assignUserOrganizations", () => {
    it("calls POST /iam/admin/v1/users/:id/organizations with organization ids", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await assignUserOrganizations("1", ["org-1"]);

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/users/1/organizations", {
        organization_ids: ["org-1"],
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("resetUserPassword", () => {
    it("calls POST /iam/admin/v1/users/:id/reset-password", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { password: "random-password" },
      };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await resetUserPassword("1");

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/users/1/reset-password", {});
      expect(result).toEqual(mockResponse);
    });
  });
});
