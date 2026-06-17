import type { RouteRecordRaw } from "vue-router";
import AdminLayout from "@/tenant/layouts/AdminLayout.vue";

/**
 * Tenant 模块路由配置 - 管理后台
 * 注意：路由名称使用 Admin 前缀，避免与 tenantRoutes 冲突
 */
export const adminRoutes: RouteRecordRaw[] = [
  {
    path: "/admin/login",
    name: "AdminLogin",
    component: () => import("@/tenant/pages/admin/AdminLoginPage.vue"),
    meta: { title: "管理员登录", hidden: true },
  },
  {
    path: "/admin",
    name: "AdminRoot",
    component: AdminLayout,
    meta: { requiresAdminAuth: true },
    children: [
      {
        path: "",
        name: "AdminRootRedirect",
        redirect: "/admin/tenants",
      },
      {
        path: "tenants",
        name: "AdminTenantManagement",
        component: () => import("@/tenant/pages/tenants/TenantList.vue"),
        meta: { title: "租户管理", requiresAdminAuth: true },
      },
      {
        path: "tenants/create",
        name: "AdminTenantCreate",
        component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
        meta: { title: "创建租户", hidden: true, requiresAdminAuth: true },
      },
      {
        path: "tenants/:id",
        name: "AdminTenantDetail",
        component: () => import("@/tenant/pages/tenants/TenantDetail.vue"),
        meta: { title: "租户详情", hidden: true, requiresAdminAuth: true },
      },
      {
        path: "tenants/:id/edit",
        name: "AdminTenantEdit",
        component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
        meta: { title: "编辑租户", hidden: true, requiresAdminAuth: true },
      },
      {
        path: "resources",
        name: "AdminResources",
        component: () => import("@/tenant/pages/admin/ResourceConfigList.vue"),
        meta: { title: "资源管理", requiresAdminAuth: true },
      },
      {
        path: "modules",
        name: "AdminModuleList",
        component: () => import("@/tenant/pages/admin/ModuleList.vue"),
        meta: { title: "模块管理", requiresAdminAuth: true },
      },
      {
        path: "modules/create",
        name: "AdminModuleCreate",
        component: () => import("@/tenant/pages/admin/ModuleForm.vue"),
        meta: { title: "创建模块", hidden: true, requiresAdminAuth: true },
      },
      {
        path: "modules/:id",
        name: "AdminModuleDetail",
        component: () => import("@/tenant/pages/admin/ModuleDetail.vue"),
        meta: { title: "模块详情", hidden: true, requiresAdminAuth: true },
      },
      {
        path: "modules/:id/edit",
        name: "AdminModuleEdit",
        component: () => import("@/tenant/pages/admin/ModuleForm.vue"),
        meta: { title: "编辑模块", hidden: true, requiresAdminAuth: true },
      },
    ],
  },
];

/**
 * 嵌套在 AdminLayout 下的路由（普通用户界面）
 */
export const tenantRoutes: RouteRecordRaw[] = [
  {
    path: "tenants",
    name: "TenantManagement",
    component: () => import("@/tenant/pages/tenants/TenantList.vue"),
    meta: { title: "租户管理", icon: "tenant", requiresAuth: true, roles: ["admin"] },
  },
  {
    path: "tenants/create",
    name: "TenantCreate",
    component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
    meta: { title: "创建租户", hidden: true, requiresAuth: true, roles: ["admin"] },
  },
  {
    path: "tenants/:id",
    name: "TenantDetail",
    component: () => import("@/tenant/pages/tenants/TenantDetail.vue"),
    meta: { title: "租户详情", hidden: true, requiresAuth: true, roles: ["admin"] },
  },
  {
    path: "tenants/:id/edit",
    name: "TenantEdit",
    component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
    meta: { title: "编辑租户", hidden: true, requiresAuth: true, roles: ["admin"] },
  },
];

export default tenantRoutes;
