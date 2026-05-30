import type { RouteRecordRaw } from "vue-router";
import { createRouter, createWebHistory } from "vue-router";
import AdminLayout from "@/framework/layouts/AdminLayout.vue";

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
    path: "/preview",
    name: "PreviewRoot",
    component: AdminLayout,
    meta: { hidden: true, requiresAuth: false },
    children: [
      {
        path: "layout",
        name: "PreviewLayout",
        component: () => import("@/framework/pages/PreviewLayoutPage.vue"),
        meta: { title: "布局预览", hidden: true, requiresAuth: false },
      },
    ],
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
 * 业务模块路由通过 setupFramework 动态注册
 */
export const asyncRoutes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "Root",
    component: AdminLayout,
    children: [
      // 设置页面
      {
        path: "settings/account",
        name: "AccountSettings",
        component: () => import("@/framework/pages/AccountSettingsPage.vue"),
        meta: { title: "账号设置", hidden: true, requiresAuth: true },
      },
      {
        path: "settings/developer",
        name: "DeveloperSettings",
        component: () => import("@/framework/pages/DeveloperSettingsPage.vue"),
        meta: { title: "开发者设置", hidden: true, requiresAuth: true },
      },
      // 业务模块路由由 setupFramework 动态注册
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
