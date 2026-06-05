import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useTenantStore } from "@/iam/stores/tenant";
import * as tenantApi from "@/iam/api/tenant";

vi.mock("@/iam/api/tenant", () => ({
  getTenants: vi.fn(),
  getTenant: vi.fn(),
  createTenant: vi.fn(),
  updateTenant: vi.fn(),
  deleteTenant: vi.fn(),
  getTenantStats: vi.fn(),
  getMyTenants: vi.fn(),
  switchTenant: vi.fn(),
  getCurrentTenant: vi.fn(),
  activateTenant: vi.fn(),
  deactivateTenant: vi.fn(),
}));

describe("Tenant Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("fetchTenants", () => {
    it("fetches tenant list", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          items: [
            { id: "1", name: "Demo租户", code: "demo", status: "active", created_at: "2024-01-01" },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
      };
      vi.mocked(tenantApi.getTenants).mockResolvedValue(mockResponse);

      const store = useTenantStore();
      await store.fetchTenants({ page: 1 });

      expect(tenantApi.getTenants).toHaveBeenCalledWith({ page: 1 });
      expect(store.tenants).toEqual(mockResponse.data.items);
      expect(store.total).toBe(1);
    });
  });

  describe("fetchTenant", () => {
    it("fetches single tenant", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", name: "Demo租户", code: "demo", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(tenantApi.getTenant).mockResolvedValue(mockResponse);

      const store = useTenantStore();
      await store.fetchTenant("1");

      expect(tenantApi.getTenant).toHaveBeenCalledWith("1");
      expect(store.currentTenant).toEqual(mockResponse.data);
    });
  });

  describe("addTenant", () => {
    it("creates tenant", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", name: "新租户", code: "new", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(tenantApi.createTenant).mockResolvedValue(mockResponse);

      const store = useTenantStore();
      await store.addTenant({ name: "新租户", code: "new" });

      expect(tenantApi.createTenant).toHaveBeenCalledWith({ name: "新租户", code: "new" });
    });
  });

  describe("editTenant", () => {
    it("updates tenant", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", name: "更新租户", code: "demo", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(tenantApi.updateTenant).mockResolvedValue(mockResponse);

      const store = useTenantStore();
      await store.editTenant("1", { name: "更新租户" });

      expect(tenantApi.updateTenant).toHaveBeenCalledWith("1", { name: "更新租户" });
    });
  });

  describe("removeTenant", () => {
    it("deletes tenant", async () => {
      vi.mocked(tenantApi.deleteTenant).mockResolvedValue({ code: 0, msg: "success", data: undefined });

      const store = useTenantStore();
      await store.removeTenant("1");

      expect(tenantApi.deleteTenant).toHaveBeenCalledWith("1");
    });
  });

  describe("fetchMyTenants", () => {
    it("fetches user tenants", async () => {
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
      vi.mocked(tenantApi.getMyTenants).mockResolvedValue(mockResponse);

      const store = useTenantStore();
      await store.fetchMyTenants();

      expect(tenantApi.getMyTenants).toHaveBeenCalled();
      expect(store.myTenants).toEqual(mockResponse.data);
    });
  });

  describe("switchTenant", () => {
    it("switches current tenant", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: {
          tenant_id: "2",
          tenant_name: "新租户",
          access_token: "new-token",
          refresh_token: "new-refresh",
          expires_in: 3600,
        },
      };
      vi.mocked(tenantApi.switchTenant).mockResolvedValue(mockResponse);
      vi.mocked(tenantApi.getCurrentTenant).mockResolvedValue({
        code: 0,
        msg: "success",
        data: { id: "2", name: "新租户", code: "new", status: "active", created_at: "2024-01-01" },
      });

      const store = useTenantStore();
      await store.switchTenant("2");

      expect(tenantApi.switchTenant).toHaveBeenCalledWith("2");
    });
  });

  describe("activate", () => {
    it("activates tenant", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", name: "Demo租户", code: "demo", status: "active", created_at: "2024-01-01" },
      };
      vi.mocked(tenantApi.activateTenant).mockResolvedValue(mockResponse);

      const store = useTenantStore();
      store.tenants = [{ id: "1", name: "Demo租户", code: "demo", status: "inactive" as const, created_at: "2024-01-01" }];
      await store.activate("1");

      expect(tenantApi.activateTenant).toHaveBeenCalledWith("1");
    });
  });

  describe("deactivate", () => {
    it("deactivates tenant", async () => {
      const mockResponse = {
        code: 0,
        msg: "success",
        data: { id: "1", name: "Demo租户", code: "demo", status: "inactive", created_at: "2024-01-01" },
      };
      vi.mocked(tenantApi.deactivateTenant).mockResolvedValue(mockResponse);

      const store = useTenantStore();
      store.tenants = [{ id: "1", name: "Demo租户", code: "demo", status: "active" as const, created_at: "2024-01-01" }];
      await store.deactivate("1");

      expect(tenantApi.deactivateTenant).toHaveBeenCalledWith("1");
    });
  });
});
