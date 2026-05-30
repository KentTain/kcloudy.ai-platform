import type { Router } from "vue-router";
import { useUserStore, usePermissionStore } from "@/framework/stores";
import { useAdminAuthStore } from "@/tenant/stores/adminAuth";
import { asyncRoutes } from "./index";

// 白名单路由
const whiteList = ["/login", "/admin/login", "/403", "/404"];

/**
 * 设置路由守卫
 */
export const setupRouterGuards = (router: Router) => {
  router.beforeEach(async (to, _from, next) => {
    const userStore = useUserStore();
    const permissionStore = usePermissionStore();
    const adminAuthStore = useAdminAuthStore();

    // 设置页面标题
    const title = to.meta?.title;
    document.title = title ? title + " - AI 助手平台" : "AI 助手平台";

    // 白名单路由直接放行
    if (whiteList.includes(to.path)) {
      next();
      return;
    }

    // 预览页面直接放行（无需登录）
    if (to.path.startsWith("/preview")) {
      next();
      return;
    }

    // 管理后台路由（排除登录页）
    if (to.meta?.requiresAdminAuth || (to.path.startsWith("/admin") && to.path !== "/admin/login")) {
      // 未登录跳转管理后台登录页
      if (!adminAuthStore.isLoggedIn && !adminAuthStore.checkAuth()) {
        next("/admin/login?redirect=" + to.path);
        return;
      }
      next();
      return;
    }

    // 普通用户路由处理
    // 未登录跳转登录页
    if (!userStore.isLoggedIn) {
      next("/login?redirect=" + to.path);
      return;
    }

    // 已登录访问登录页，重定向首页
    if (to.path === "/login") {
      next("/");
      return;
    }

    // 动态路由已加载，直接放行
    if (permissionStore.isLoaded) {
      next();
      return;
    }

    // 生成并注册动态路由
    try {
      const routes = await permissionStore.generateRoutes(asyncRoutes);

      // 动态添加路由
      routes.forEach((route) => {
        router.addRoute(route);
      });

      // 重新导航到目标路由
      next({ ...to, replace: true });
    } catch (error) {
      console.error("Failed to setup routes:", error);
      // 路由生成失败，清除登录状态并跳转登录页
      userStore.logout();
      next("/login?redirect=" + to.path);
    }
  });
};

export default setupRouterGuards;
