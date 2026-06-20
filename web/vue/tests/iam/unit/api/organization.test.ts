import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  getOrganizations,
  getOrganizationTree,
  createOrganization,
  updateOrganization,
  deleteOrganization,
  getOrganizationUsers,
  addOrganizationUser,
  removeOrganizationUser,
} from "@/iam/api/organization";
import * as client from "@/framework/api/client";

vi.mock("@/framework/api/client", () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
}));

describe("Organization API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getOrganizations", () => {
    it("calls GET /iam/admin/v1/organizations with params", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [],
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getOrganizations({ keyword: "研发" });

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/organizations", { params: { keyword: "研发" } });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getOrganizationTree", () => {
    it("calls GET /iam/admin/v1/organizations/tree", async () => {
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

      const result = await getOrganizationTree();

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/organizations/tree");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("createOrganization", () => {
    it("calls POST /iam/admin/v1/organizations with organization data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", tenant_id: "tenant-1", name: "研发部", sort_order: 0, status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await createOrganization({ name: "研发部", parent_id: "1" });

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/organizations", {
        name: "研发部",
        parent_id: "1",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("updateOrganization", () => {
    it("calls PUT /iam/admin/v1/organizations/:id with update data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", tenant_id: "tenant-1", name: "研发一部", sort_order: 0, status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(client.put).mockResolvedValue(mockResponse);

      const result = await updateOrganization("1", { name: "研发一部" });

      expect(client.put).toHaveBeenCalledWith("/iam/admin/v1/organizations/1", { name: "研发一部" });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("deleteOrganization", () => {
    it("calls DELETE /iam/admin/v1/organizations/:id", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.del).mockResolvedValue(mockResponse);

      const result = await deleteOrganization("1");

      expect(client.del).toHaveBeenCalledWith("/iam/admin/v1/organizations/1");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getOrganizationUsers", () => {
    it("calls GET /iam/admin/v1/organizations/:id/users", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [],
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getOrganizationUsers("1");

      expect(client.get).toHaveBeenCalledWith("/iam/admin/v1/organizations/1/users");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("addOrganizationUser", () => {
    it("calls POST /iam/admin/v1/organizations/:id/users with user id", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.post).mockResolvedValue(mockResponse);

      const result = await addOrganizationUser("1", "user-1");

      expect(client.post).toHaveBeenCalledWith("/iam/admin/v1/organizations/1/users", {
        user_id: "user-1",
        is_leader: false,
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("removeOrganizationUser", () => {
    it("calls DELETE /iam/admin/v1/organizations/:id/users/:userId", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.del).mockResolvedValue(mockResponse);

      const result = await removeOrganizationUser("1", "user-1");

      expect(client.del).toHaveBeenCalledWith("/iam/admin/v1/organizations/1/users/user-1");
      expect(result).toEqual(mockResponse);
    });
  });
});
