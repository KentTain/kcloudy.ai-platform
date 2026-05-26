import type { RouteRecordRaw } from "vue-router";

/**
 * Tenant 模块路由配置
 *
 * 这些路由将作为 AdminLayout 的子路由嵌套使用
 */
export const tenantRoutes: RouteRecordRaw[] = [
  {
    path: "tenants",
    name: "TenantManagement",
    component: () => import("@/tenant/pages/tenants/TenantList.vue"),
    meta: { title: "租户管理", icon: "tenant", requiresAuth: true, roles: ["tenant_admin"] },
  },
  {
    path: "tenants/create",
    name: "TenantCreate",
    component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
    meta: { title: "创建租户", hidden: true, requiresAuth: true, roles: ["tenant_admin"] },
  },
  {
    path: "tenants/:id",
    name: "TenantDetail",
    component: () => import("@/tenant/pages/tenants/TenantDetail.vue"),
    meta: { title: "租户详情", hidden: true, requiresAuth: true, roles: ["tenant_admin"] },
  },
  {
    path: "tenants/:id/edit",
    name: "TenantEdit",
    component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
    meta: { title: "编辑租户", hidden: true, requiresAuth: true, roles: ["tenant_admin"] },
  },
];

export default tenantRoutes;
