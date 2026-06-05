import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  getTenants,
  getTenant,
  createTenant,
  updateTenant,
  deleteTenant,
  getTenantStats,
  getMyTenants,
  switchTenant,
} from "@/iam/api/tenant";
import * as client from "@/framework/api/client";

vi.mock("@/framework/api/client", () => ({
  rawGet: vi.fn(),
  rawPost: vi.fn(),
  rawPut: vi.fn(),
  rawDel: vi.fn(),
}));

describe("Tenant API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getTenants", () => {
    it("calls rawGet /admin/v1/tenants with params", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { items: [], total: 0, page: 1, page_size: 20 },
      };
      vi.mocked(client.rawGet).mockResolvedValue(mockResponse);

      const result = await getTenants({ page: 1, keyword: "demo" });

      expect(client.rawGet).toHaveBeenCalledWith("/admin/v1/tenants", { params: { page: 1, keyword: "demo" } });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getTenant", () => {
    it("calls rawGet /admin/v1/tenants/:id", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          id: "1",
          name: "Demo租户",
          code: "demo",
          status: "active",
          created_at: "2024-01-01",
        },
      };
      vi.mocked(client.rawGet).mockResolvedValue(mockResponse);

      const result = await getTenant("1");

      expect(client.rawGet).toHaveBeenCalledWith("/admin/v1/tenants/1");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("createTenant", () => {
    it("calls rawPost /admin/v1/tenants with tenant data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          id: "1",
          name: "新租户",
          code: "new",
          status: "active",
          created_at: "2024-01-01",
        },
      };
      vi.mocked(client.rawPost).mockResolvedValue(mockResponse);

      const result = await createTenant({
        name: "新租户",
        code: "new",
        contact_name: "联系人",
      });

      expect(client.rawPost).toHaveBeenCalledWith("/admin/v1/tenants", {
        name: "新租户",
        code: "new",
        contact_name: "联系人",
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("updateTenant", () => {
    it("calls rawPut /admin/v1/tenants/:id with update data", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          id: "1",
          name: "更新租户",
          code: "demo",
          status: "active",
          created_at: "2024-01-01",
        },
      };
      vi.mocked(client.rawPut).mockResolvedValue(mockResponse);

      const result = await updateTenant("1", { name: "更新租户" });

      expect(client.rawPut).toHaveBeenCalledWith("/admin/v1/tenants/1", { name: "更新租户" });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("deleteTenant", () => {
    it("calls rawDel /admin/v1/tenants/:id", async () => {
      const mockResponse = { code: 0, msg: "success", data: undefined };
      vi.mocked(client.rawDel).mockResolvedValue(mockResponse);

      const result = await deleteTenant("1");

      expect(client.rawDel).toHaveBeenCalledWith("/admin/v1/tenants/1");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getTenantStats", () => {
    it("calls rawGet /admin/v1/tenants/:id/stats", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          tenant_id: "1",
          user_count: 100,
          storage_usage: 1024,
          active_users: 50,
        },
      };
      vi.mocked(client.rawGet).mockResolvedValue(mockResponse);

      const result = await getTenantStats("1");

      expect(client.rawGet).toHaveBeenCalledWith("/admin/v1/tenants/1/stats");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getMyTenants", () => {
    it("calls rawGet /console/v1/tenants", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: [
          {
            tenant_id: "1",
            tenant_name: "Demo租户",
            tenant_code: "demo",
            role_ids: ["role-1"],
            role_names: ["管理员"],
            is_current: true,
          },
        ],
      };
      vi.mocked(client.rawGet).mockResolvedValue(mockResponse);

      const result = await getMyTenants();

      expect(client.rawGet).toHaveBeenCalledWith("/console/v1/tenants");
      expect(result).toEqual(mockResponse);
    });
  });

  describe("switchTenant", () => {
    it("calls rawPost /console/v1/tenants/:id/switch", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          tenant_id: "1",
          tenant_name: "Demo租户",
          access_token: "new-token",
          refresh_token: "new-refresh",
          expires_in: 3600,
        },
      };
      vi.mocked(client.rawPost).mockResolvedValue(mockResponse);

      const result = await switchTenant("1");

      expect(client.rawPost).toHaveBeenCalledWith("/console/v1/tenants/1/switch");
      expect(result).toEqual(mockResponse);
    });
  });
});
