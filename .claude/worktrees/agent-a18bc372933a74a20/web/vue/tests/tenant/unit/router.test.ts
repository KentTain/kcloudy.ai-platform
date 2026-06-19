/**
 * Tenant 模块路由测试
 */
import { describe, expect, it } from "vitest";
import { adminRoutes, tenantRoutes } from "@/tenant/router";

describe("adminRoutes", () => {
  describe("路由结构", () => {
    it("使用 /admin 前缀作为管理后台根路径", () => {
      const adminRoot = adminRoutes.find((route) => route.path === "/admin");
      expect(adminRoot).toBeDefined();
      expect(adminRoot?.name).toBe("AdminRoot");
    });

    it("/admin 根路径重定向到租户管理", () => {
      const adminRoot = adminRoutes.find((route) => route.path === "/admin");
      const redirectRoute = adminRoot?.children?.find(
        (route) => route.path === ""
      );
      expect(redirectRoute).toBeDefined();
      expect(redirectRoute?.redirect).toBe("/admin/tenants");
    });
  });

  describe("租户管理路由", () => {
    it("包含租户列表路由 /admin/tenants", () => {
      const adminRoot = adminRoutes.find((route) => route.path === "/admin");
      const tenantRoute = adminRoot?.children?.find(
        (route) => route.path === "tenants"
      );
      expect(tenantRoute).toBeDefined();
      expect(tenantRoute?.name).toBe("AdminTenantManagement");
      expect(tenantRoute?.meta?.title).toBe("租户管理");
    });

    it("包含创建租户路由 /admin/tenants/create", () => {
      const adminRoot = adminRoutes.find((route) => route.path === "/admin");
      const createRoute = adminRoot?.children?.find(
        (route) => route.path === "tenants/create"
      );
      expect(createRoute).toBeDefined();
      expect(createRoute?.name).toBe("AdminTenantCreate");
      expect(createRoute?.meta?.hidden).toBe(true);
    });

    it("包含租户详情路由 /admin/tenants/:id", () => {
      const adminRoot = adminRoutes.find((route) => route.path === "/admin");
      const detailRoute = adminRoot?.children?.find(
        (route) => route.path === "tenants/:id"
      );
      expect(detailRoute).toBeDefined();
      expect(detailRoute?.name).toBe("AdminTenantDetail");
    });

    it("包含编辑租户路由 /admin/tenants/:id/edit", () => {
      const adminRoot = adminRoutes.find((route) => route.path === "/admin");
      const editRoute = adminRoot?.children?.find(
        (route) => route.path === "tenants/:id/edit"
      );
      expect(editRoute).toBeDefined();
      expect(editRoute?.name).toBe("AdminTenantEdit");
    });
  });

  describe("资源管理路由", () => {
    it("包含资源管理路由 /admin/resources", () => {
      const adminRoot = adminRoutes.find((route) => route.path === "/admin");
      const resourcesRoute = adminRoot?.children?.find(
        (route) => route.path === "resources"
      );
      expect(resourcesRoute).toBeDefined();
      expect(resourcesRoute?.name).toBe("AdminResources");
      expect(resourcesRoute?.meta?.title).toBe("资源管理");
    });
  });

  describe("模块管理路由", () => {
    it("包含模块列表路由 /admin/modules", () => {
      const adminRoot = adminRoutes.find((route) => route.path === "/admin");
      const moduleRoute = adminRoot?.children?.find(
        (route) => route.path === "modules"
      );
      expect(moduleRoute).toBeDefined();
      expect(moduleRoute?.name).toBe("AdminModuleList");
      expect(moduleRoute?.meta?.title).toBe("模块管理");
    });
  });
});

describe("tenantRoutes", () => {
  describe("用户端路由结构", () => {
    it("使用嵌套结构定义用户端租户路由", () => {
      const tenantManageRoute = tenantRoutes.find(
        (route) => route.path === "tenants"
      );
      expect(tenantManageRoute).toBeDefined();
      expect(tenantManageRoute?.name).toBe("TenantManagement");
    });

    it("包含创建租户路由 tenants/create", () => {
      const createRoute = tenantRoutes.find(
        (route) => route.path === "tenants/create"
      );
      expect(createRoute).toBeDefined();
      expect(createRoute?.name).toBe("TenantCreate");
    });

    it("包含租户详情路由 tenants/:id", () => {
      const detailRoute = tenantRoutes.find(
        (route) => route.path === "tenants/:id"
      );
      expect(detailRoute).toBeDefined();
      expect(detailRoute?.name).toBe("TenantDetail");
    });

    it("包含编辑租户路由 tenants/:id/edit", () => {
      const editRoute = tenantRoutes.find(
        (route) => route.path === "tenants/:id/edit"
      );
      expect(editRoute).toBeDefined();
      expect(editRoute?.name).toBe("TenantEdit");
    });
  });

  describe("路由权限", () => {
    it("用户端路由需要 admin 角色", () => {
      tenantRoutes.forEach((route) => {
        if (route.meta?.roles) {
          expect(route.meta.roles).toContain("admin");
        }
      });
    });
  });
});
