import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  getDepartments,
  getDepartmentTree,
  createDepartment,
  updateDepartment,
  deleteDepartment,
  getDepartmentUsers,
  addDepartmentUser,
  removeDepartmentUser,
} from "@/iam/api/department";
import * as client from "@/framework/api/client";

vi.mock("@/framework/api/client", () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}));

describe("Department API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getDepartments", () => {
    it("calls GET /iam/admin/v1/departments with params", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [],
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getDepartments({ keyword: "研发" });

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/departments", { params: { keyword: "研发" } });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getDepartmentTree", () => {
    it("calls GET /iam/admin/v1/departments/tree", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [
          {
            id: "1",
            tenant_id: "tenant-1",
            name: "总公司",
            sort_order: 0,
            status: "active",
            created_at: "2024-01-01",
            children: [],
          },
        ],
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getDepartmentTree();

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/departments/tree");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("createDepartment", () => {
    it("calls POST /iam/admin/v1/departments with department data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", tenant_id: "tenant-1", name: "研发部", sort_order: 0, status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await createDepartment({ name: "研发部", parent_id: "1" });

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/departments", {
        name: "研发部",
        parent_id: "1",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("updateDepartment", () => {
    it("calls PUT /iam/admin/v1/departments/:id with update data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", tenant_id: "tenant-1", name: "研发一部", sort_order: 0, status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(client.put).mockResolvedValue(mockResponse);

      const result = await updateDepartment("1", { name: "研发一部" });

      expect(client.put).toHaveBeenCalledWith("/iam/admin/v1/departments/1", { name: "研发一部" });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("deleteDepartment", () => {
    it("calls DELETE /iam/admin/v1/departments/:id", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.del).mockResolvedValue(mockResponse);

      const result = await deleteDepartment("1");

      expect(client.del).toHaveBeenCalledWith("/iam/admin/v1/departments/1");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getDepartmentUsers", () => {
    it("calls GET /iam/admin/v1/departments/:id/users", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [],
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getDepartmentUsers("1");

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/departments/1/users");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("addDepartmentUser", () => {
    it("calls POST /iam/admin/v1/departments/:id/users with user id", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await addDepartmentUser("1", "user-1");

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/departments/1/users", {
        user_id: "user-1",
        is_leader: false,
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("removeDepartmentUser", () => {
    it("calls DELETE /iam/admin/v1/departments/:id/users/:userId", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.del).mockResolvedValue(mockResponse);

      const result = await removeDepartmentUser("1", "user-1");

      expect(client.del).toHaveBeenCalledWith("/iam/admin/v1/departments/1/users/user-1");
      expect(result).toEqual(mockResponse);
    });
  });
});
