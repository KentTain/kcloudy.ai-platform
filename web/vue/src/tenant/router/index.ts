import type { RouteRecordRaw } from "vue-router";
import AdminLayout from "@/tenant/layouts/AdminLayout.vue";

/**
 * Tenant 模块路由配置 - 管理后台
 * 注意：路由名称使用 Admin 前缀，避免冲突
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
        meta: { title: "租户管理", requiresAdminAuth: true, permissions: ["tenant:tenant:read"] },
      },
      {
        path: "tenants/create",
        name: "AdminTenantCreate",
        component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
        meta: { title: "创建租户", hidden: true, requiresAdminAuth: true, permissions: ["tenant:tenant:write"] },
      },
      {
        path: "tenants/:id",
        name: "AdminTenantDetail",
        component: () => import("@/tenant/pages/tenants/TenantDetail.vue"),
        meta: { title: "租户详情", hidden: true, requiresAdminAuth: true, permissions: ["tenant:tenant:read"] },
      },
      {
        path: "tenants/:id/edit",
        name: "AdminTenantEdit",
        component: () => import("@/tenant/pages/tenants/TenantForm.vue"),
        meta: { title: "编辑租户", hidden: true, requiresAdminAuth: true, permissions: ["tenant:tenant:write"] },
      },
      {
        path: "resources",
        name: "AdminResources",
        component: () => import("@/tenant/pages/admin/ResourceConfigList.vue"),
        meta: { title: "资源管理", requiresAdminAuth: true, permissions: ["tenant:resource:read"] },
      },
      {
        path: "modules",
        name: "AdminModuleList",
        component: () => import("@/tenant/pages/admin/ModuleList.vue"),
        meta: { title: "模块管理", requiresAdminAuth: true, permissions: ["tenant:module:read"] },
      },
      {
        path: "modules/create",
        name: "AdminModuleCreate",
        component: () => import("@/tenant/pages/admin/ModuleForm.vue"),
        meta: { title: "创建模块", hidden: true, requiresAdminAuth: true, permissions: ["tenant:module:write"] },
      },
      {
        path: "modules/:id",
        name: "AdminModuleDetail",
        component: () => import("@/tenant/pages/admin/ModuleDetail.vue"),
        meta: { title: "模块详情", hidden: true, requiresAdminAuth: true, permissions: ["tenant:module:read"] },
      },
      {
        path: "modules/:id/edit",
        name: "AdminModuleEdit",
        component: () => import("@/tenant/pages/admin/ModuleForm.vue"),
        meta: { title: "编辑模块", hidden: true, requiresAdminAuth: true, permissions: ["tenant:module:write"] },
      },
      {
        path: "plugin-definitions",
        name: "AdminPluginDefinitions",
        component: () => import("@/tenant/pages/admin/PluginDefinitionList.vue"),
        meta: { title: "插件定义", requiresAdminAuth: true, permissions: ["tenant:plugin:read"] },
      },
      {
        path: "plugin-definitions/scan",
        name: "AdminPluginDefinitionScan",
        component: () => import("@/tenant/pages/admin/PluginScanPage.vue"),
        meta: { title: "扫描目录注册插件", hidden: true, requiresAdminAuth: true, permissions: ["tenant:plugin:write"] },
      },
      {
        path: "plugin-definitions/upload",
        name: "AdminPluginDefinitionUpload",
        component: () => import("@/tenant/pages/admin/PluginUploadPage.vue"),
        meta: { title: "上传插件包", hidden: true, requiresAdminAuth: true, permissions: ["tenant:plugin:write"] },
      },
      {
        path: "plugin-definitions/:id(.*)",
        name: "AdminPluginDefinitionDetail",
        component: () => import("@/tenant/pages/admin/PluginDefinitionDetailPage.vue"),
        meta: { title: "插件详情", hidden: true, requiresAdminAuth: true, permissions: ["tenant:plugin:read"] },
      },
      {
        path: "plugin-definitions/:id(.*)/edit",
        name: "AdminPluginDefinitionEdit",
        component: () => import("@/tenant/pages/admin/PluginDefinitionEditPage.vue"),
        meta: { title: "编辑插件状态", hidden: true, requiresAdminAuth: true, permissions: ["tenant:plugin:write"] },
      },
      {
        path: "plugin-installations",
        name: "AdminPluginInstallations",
        component: () => import("@/tenant/pages/admin/PluginInstallationList.vue"),
        meta: { title: "安装记录", requiresAdminAuth: true, permissions: ["tenant:plugin:read"] },
      },
      // ==================== 插件市场管理 ====================
      {
        path: "marketplaces",
        name: "AdminMarketplaceList",
        component: () => import("@/tenant/pages/admin/MarketplaceListPage.vue"),
        meta: { title: "插件市场", requiresAdminAuth: true, permissions: ["tenant:marketplace:read"] },
      },
      {
        path: "marketplaces/create",
        name: "AdminMarketplaceCreate",
        component: () => import("@/tenant/pages/admin/MarketplaceFormPage.vue"),
        meta: { title: "添加市场", hidden: true, requiresAdminAuth: true, permissions: ["tenant:marketplace:write"] },
      },
      {
        path: "marketplaces/:id/edit",
        name: "AdminMarketplaceEdit",
        component: () => import("@/tenant/pages/admin/MarketplaceFormPage.vue"),
        meta: { title: "编辑市场", hidden: true, requiresAdminAuth: true, permissions: ["tenant:marketplace:write"] },
      },
      {
        path: "marketplaces/:id/plugins",
        name: "AdminRemotePluginBrowse",
        component: () => import("@/tenant/pages/admin/RemotePluginBrowsePage.vue"),
        meta: { title: "浏览远程插件", hidden: true, requiresAdminAuth: true, permissions: ["tenant:marketplace:read"] },
      },
      {
        path: "marketplaces/:id/skills",
        name: "AdminSkillMarketplace",
        component: () => import("@/tenant/pages/admin/SkillMarketplacePage.vue"),
        meta: { title: "Skill 市场", hidden: true, requiresAdminAuth: true, permissions: ["tenant:marketplace:read"] },
      },
    ],
  },
];
