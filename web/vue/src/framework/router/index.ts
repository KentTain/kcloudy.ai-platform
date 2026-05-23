import type { RouteRecordRaw } from "vue-router";
import { createRouter, createWebHistory } from "vue-router";
import AdminLayout from "@/framework/layouts/AdminLayout.vue";

// IAM 模块路由
import { iamRoutes } from "@/iam/router";

/**
 * 静态路由配置（无需权限验证）
 */
export const constantRoutes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "Login",
    component: () => import("@/framework/pages/LoginPage.vue"),
    meta: { title: "登录", hidden: true },
  },
  {
    path: "/403",
    name: "Forbidden",
    component: () => import("@/framework/pages/ForbiddenPage.vue"),
    meta: { title: "无权限", hidden: true },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/framework/pages/NotFoundPage.vue"),
    meta: { title: "页面不存在", hidden: true },
  },
];

/**
 * 异步路由配置（需要权限验证）
 */
export const asyncRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    component: AdminLayout,
    children: [
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
      // IAM 模块路由
      ...iamRoutes,
    ],
  },
];

/**
 * 创建路由实例
 */
export const createAppRouter = () =>
  createRouter({
    history: createWebHistory(),
    routes: constantRoutes,
    scrollBehavior: () => ({ top: 0 }),
  });

/**
 * 默认路由实例
 */
export const router = createAppRouter();

export default router;
