/**
 * Tenant Store 测试
 */
import { describe, expect, it, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useTenantStore } from "@/tenant/stores/tenant";
import * as tenantApi from "@/tenant/api/tenant";

// Mock API
vi.mock("@/tenant/api/tenant", () => ({
  getTenants: vi.fn(),
  getTenant: vi.fn(),
  createTenant: vi.fn(),
  updateTenant: vi.fn(),
  deleteTenant: vi.fn(),
  activateTenant: vi.fn(),
  deactivateTenant: vi.fn(),
  getCurrentTenant: vi.fn(),
  getMyTenants: vi.fn(),
  switchTenant: vi.fn(),
}));

// Mock feedback utils
vi.mock("@/framework/utils/feedback", () => ({
  notifyError: vi.fn(),
  notifySuccess: vi.fn(),
  getErrorMessage: vi.fn((_, fallback) => fallback),
}));

// 测试数据
const mockTenants = [
  {
    id: "tenant-1",
    name: "测试租户1",
    code: "test1",
    status: "active" as const,
    contact_name: "张三",
    contact_email: "zhangsan@test.com",
    created_at: "2025-01-01T00:00:00Z",
  },
  {
    id: "tenant-2",
    name: "测试租户2",
    code: "test2",
    status: "inactive" as const,
    contact_name: "李四",
    contact_email: "lisi@test.com",
    created_at: "2025-01-02T00:00:00Z",
  },
];

const mockStats = {
  total_count: 10,
  inactive_count: 3,
  expired_count: 2,
};

describe("Tenant Store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("初始状态", () => {
    it("初始化时 tenants 为空数组", () => {
      const store = useTenantStore();
      expect(store.tenants).toEqual([]);
    });

    it("初始化时 loading 为 false", () => {
      const store = useTenantStore();
      expect(store.loading).toBe(false);
    });

    it("初始化时 total 为 0", () => {
      const store = useTenantStore();
      expect(store.total).toBe(0);
    });

    it("初始化时 stats 为默认值", () => {
      const store = useTenantStore();
      expect(store.stats).toEqual({
        total_count: 0,
        inactive_count: 0,
        expired_count: 0,
      });
    });
  });

  describe("fetchTenants", () => {
    it("成功获取租户列表并更新状态", async () => {
      const mockResponse = {
        data: {
          items: mockTenants,
          total: 2,
          stats: mockStats,
        },
      };
      vi.mocked(tenantApi.getTenants).mockResolvedValue(mockResponse as any);

      const store = useTenantStore();
      await store.fetchTenants();

      expect(tenantApi.getTenants).toHaveBeenCalled();
      expect(store.tenants).toEqual(mockTenants);
      expect(store.total).toBe(2);
      expect(store.stats).toEqual(mockStats);
    });

    it("成功获取租户列表时更新统计数据", async () => {
      const mockResponse = {
        data: {
          items: mockTenants,
          total: 2,
          stats: mockStats,
        },
      };
      vi.mocked(tenantApi.getTenants).mockResolvedValue(mockResponse as any);

      const store = useTenantStore();
      await store.fetchTenants();

      expect(store.stats.total_count).toBe(10);
      expect(store.stats.inactive_count).toBe(3);
      expect(store.stats.expired_count).toBe(2);
    });

    it("API 返回空数据时使用默认统计值", async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
        },
      };
      vi.mocked(tenantApi.getTenants).mockResolvedValue(mockResponse as any);

      const store = useTenantStore();
      await store.fetchTenants();

      expect(store.stats).toEqual({
        total_count: 0,
        inactive_count: 0,
        expired_count: 0,
      });
    });

    it("带参数调用时传递查询参数", async () => {
      const mockResponse = {
        data: { items: [], total: 0, stats: mockStats },
      };
      vi.mocked(tenantApi.getTenants).mockResolvedValue(mockResponse as any);

      const store = useTenantStore();
      await store.fetchTenants({ page: 1, page_size: 10, keyword: "test" });

      expect(tenantApi.getTenants).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
        keyword: "test",
      });
    });

    it("请求失败时调用 notifyError", async () => {
      vi.mocked(tenantApi.getTenants).mockRejectedValue(new Error("网络错误"));

      const store = useTenantStore();
      await store.fetchTenants();

      const { notifyError } = await import("@/framework/utils/feedback");
      expect(notifyError).toHaveBeenCalled();
    });
  });

  describe("fetchTenant", () => {
    it("成功获取租户详情", async () => {
      const mockTenant = mockTenants[0];
      vi.mocked(tenantApi.getTenant).mockResolvedValue({ data: mockTenant } as any);

      const store = useTenantStore();
      const result = await store.fetchTenant("tenant-1");

      expect(tenantApi.getTenant).toHaveBeenCalledWith("tenant-1");
      expect(store.currentTenant).toEqual(mockTenant);
      expect(result).toEqual(mockTenant);
    });
  });

  describe("addTenant", () => {
    it("成功创建租户", async () => {
      const newTenant = {
        name: "新租户",
        code: "new",
      };
      const createdTenant = {
        id: "tenant-new",
        ...newTenant,
        status: "active" as const,
        created_at: "2025-01-03T00:00:00Z",
      };

      vi.mocked(tenantApi.createTenant).mockResolvedValue({ data: createdTenant } as any);

      const store = useTenantStore();
      store.tenants = [...mockTenants];
      const initialTotal = store.total;

      const result = await store.addTenant(newTenant as any);

      expect(tenantApi.createTenant).toHaveBeenCalledWith(newTenant);
      expect(store.tenants[0]).toEqual(createdTenant);
      expect(store.total).toBe(initialTotal + 1);
      expect(result).toEqual(createdTenant);
    });
  });

  describe("editTenant", () => {
    it("成功更新租户", async () => {
      const updateData = { name: "更新后的租户" };
      const updatedTenant = {
        ...mockTenants[0],
        name: "更新后的租户",
      };

      vi.mocked(tenantApi.updateTenant).mockResolvedValue({ data: updatedTenant } as any);

      const store = useTenantStore();
      store.tenants = [...mockTenants];

      const result = await store.editTenant("tenant-1", updateData as any);

      expect(tenantApi.updateTenant).toHaveBeenCalledWith("tenant-1", updateData);
      expect(store.tenants[0]).toEqual(updatedTenant);
      expect(result).toEqual(updatedTenant);
    });
  });

  describe("removeTenant", () => {
    it("成功删除租户", async () => {
      vi.mocked(tenantApi.deleteTenant).mockResolvedValue({ data: undefined } as any);

      const store = useTenantStore();
      store.tenants = [...mockTenants];
      store.total = 2;

      await store.removeTenant("tenant-1");

      expect(tenantApi.deleteTenant).toHaveBeenCalledWith("tenant-1");
      expect(store.tenants.length).toBe(1);
      expect(store.tenants.find((t) => t.id === "tenant-1")).toBeUndefined();
      expect(store.total).toBe(1);
    });
  });

  describe("activate", () => {
    it("成功激活租户", async () => {
      const activatedTenant = {
        ...mockTenants[1],
        status: "active" as const,
      };
      vi.mocked(tenantApi.activateTenant).mockResolvedValue({ data: activatedTenant } as any);

      const store = useTenantStore();
      store.tenants = [...mockTenants];

      const result = await store.activate("tenant-2");

      expect(tenantApi.activateTenant).toHaveBeenCalledWith("tenant-2");
      expect(store.tenants[1].status).toBe("active");
      expect(result).toEqual(activatedTenant);
    });
  });

  describe("deactivate", () => {
    it("成功停用租户", async () => {
      const deactivatedTenant = {
        ...mockTenants[0],
        status: "inactive" as const,
      };
      vi.mocked(tenantApi.deactivateTenant).mockResolvedValue({ data: deactivatedTenant } as any);

      const store = useTenantStore();
      store.tenants = [...mockTenants];

      const result = await store.deactivate("tenant-1");

      expect(tenantApi.deactivateTenant).toHaveBeenCalledWith("tenant-1");
      expect(store.tenants[0].status).toBe("inactive");
      expect(result).toEqual(deactivatedTenant);
    });
  });

  describe("fetchCurrentTenant", () => {
    it("成功获取当前租户", async () => {
      vi.mocked(tenantApi.getCurrentTenant).mockResolvedValue({ data: mockTenants[0] } as any);

      const store = useTenantStore();
      const result = await store.fetchCurrentTenant();

      expect(tenantApi.getCurrentTenant).toHaveBeenCalled();
      expect(store.currentTenant).toEqual(mockTenants[0]);
      expect(result).toEqual(mockTenants[0]);
    });
  });

  describe("fetchMyTenants", () => {
    it("成功获取用户可切换的租户列表", async () => {
      const mockMyTenants = [
        {
          tenant_id: "tenant-1",
          tenant_name: "测试租户1",
          tenant_code: "test1",
          role_ids: ["role-1"],
          role_names: ["管理员"],
          is_current: true,
        },
      ];
      vi.mocked(tenantApi.getMyTenants).mockResolvedValue({ data: mockMyTenants } as any);

      const store = useTenantStore();
      await store.fetchMyTenants();

      expect(tenantApi.getMyTenants).toHaveBeenCalled();
      expect(store.myTenants).toEqual(mockMyTenants);
    });
  });

  describe("switchTenant", () => {
    it("成功切换租户", async () => {
      const mockSwitchResponse = {
        tenant_id: "tenant-2",
        tenant_name: "测试租户2",
        access_token: "new-token",
        refresh_token: "new-refresh",
        expires_in: 3600,
      };
      vi.mocked(tenantApi.switchTenant).mockResolvedValue({ data: mockSwitchResponse } as any);
      vi.mocked(tenantApi.getCurrentTenant).mockResolvedValue({ data: mockTenants[1] } as any);

      const store = useTenantStore();
      await store.switchTenant("tenant-2");

      expect(tenantApi.switchTenant).toHaveBeenCalledWith("tenant-2");
      expect(tenantApi.getCurrentTenant).toHaveBeenCalled();
    });
  });

  describe("isCurrentTenantActive", () => {
    it("当前租户激活时返回 true", () => {
      const store = useTenantStore();
      store.currentTenant = mockTenants[0]; // status: 'active'

      expect(store.isCurrentTenantActive).toBe(true);
    });

    it("当前租户停用时返回 false", () => {
      const store = useTenantStore();
      store.currentTenant = mockTenants[1]; // status: 'inactive'

      expect(store.isCurrentTenantActive).toBe(false);
    });

    it("没有当前租户时返回 false", () => {
      const store = useTenantStore();
      store.currentTenant = null;

      expect(store.isCurrentTenantActive).toBe(false);
    });
  });
});
