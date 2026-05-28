import type { RouteRecordRaw } from "vue-router";

/**
 * Demo 模块路由配置
 */
export const demoRoutes: RouteRecordRaw[] = [
  {
    path: "",
    name: "Home",
    component: () => import("@/demo/pages/HomePage.vue"),
    meta: { title: "首页", icon: "home", requiresAuth: true },
  },
  {
    path: "health",
    name: "Health",
    component: () => import("@/demo/pages/HealthPage.vue"),
    meta: { title: "健康检查", icon: "health", requiresAuth: true },
  },
  {
    path: "datasets",
    name: "Datasets",
    component: () => import("@/demo/pages/DatasetsPage.vue"),
    meta: { title: "知识库", icon: "database", requiresAuth: true },
  },
];

export default demoRoutes;
