import { describe, expect, it, vi, beforeEach } from "vitest";
import { getPermissions, getAllPermissions, getPermissionsByResource } from "@/iam/api/permission";
import * as client from "@/framework/api/client";

vi.mock("@/framework/api/client", () => ({
  get: vi.fn(),
}));

describe("Permission API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getPermissions", () => {
    it("calls GET /v1/iam/permission with params", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { items: [], total: 0, page: 1, page_size: 20 },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getPermissions({ page: 1, keyword: "user" });

      expect(client.get).toHaveBeenCalledWith("/v1/iam/permission", { params: { page: 1, keyword: "user" } });
      expect(result).toEqual(mockResponse);
    });

    it("calls GET /v1/iam/permission with resource filter", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          items: [
            {
              id: "perm-1",
              code: "user:read",
              name: "查看用户",
              resource: "user",
              action: "read",
              created_at: "2024-01-01",
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getPermissions({ resource: "user" });

      expect(client.get).toHaveBeenCalledWith("/v1/iam/permission", { params: { resource: "user" } });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getAllPermissions", () => {
    it("calls GET /v1/iam/permission and returns all items", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          items: [
            {
              id: "perm-1",
              code: "user:read",
              name: "查看用户",
              resource: "user",
              action: "read",
              created_at: "2024-01-01",
            },
          ],
          total: 1,
          page: 1,
          page_size: 1000,
        },
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getAllPermissions();

      expect(client.get).toHaveBeenCalledWith("/v1/iam/permission", { params: { page: 1, page_size: 1000 } });
      expect(result.data).toEqual(mockResponse.data.items);
    });
  });

  describe("getPermissionsByResource", () => {
    it("calls GET /v1/iam/permission/grouped", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [
          {
            resource: "user",
            permissions: [
              {
                id: "perm-1",
                code: "user:read",
                name: "查看用户",
                resource: "user",
                action: "read",
                created_at: "2024-01-01",
              },
            ],
          },
        ],
      };
      vi.mocked(client.get).mockResolvedValue(mockResponse);

      const result = await getPermissionsByResource();

      expect(client.get).toHaveBeenCalledWith("/v1/iam/permission/grouped");
      expect(result).toEqual(mockResponse);
    });
  });
});
