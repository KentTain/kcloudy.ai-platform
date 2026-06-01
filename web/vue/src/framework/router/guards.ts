import type { Router } from "vue-router";
import { useUserStore, usePermissionStore } from "@/framework/stores";
import { useAdminAuthStore } from "@/tenant/stores/adminAuth";

// 白名单路由
const whiteList = ["/login", "/admin/login", "/403", "/404"];

/**
 * 设置路由守卫
 */
export const setupRouterGuards = (router: Router) => {
  router.beforeEach(async (to, _from, next) => {
    console.log("[RouterGuard] Navigating to:", to.path, "name:", to.name, "matched:", to.matched.length);

    const userStore = useUserStore();
    const permissionStore = usePermissionStore();
    const adminAuthStore = useAdminAuthStore();

    // 设置页面标题
    const title = to.meta?.title;
    document.title = title ? title + " - AI 助手平台" : "AI 助手平台";

    // 白名单路由直接放行
    if (whiteList.includes(to.path)) {
      console.log("[RouterGuard] Path in whitelist, allowing");
      next();
      return;
    }

    // 预览页面直接放行（无需登录）
    if (to.path.startsWith("/preview")) {
      console.log("[RouterGuard] Preview path, allowing");
      next();
      return;
    }

    // 管理后台路由（排除登录页）
    if (to.meta?.requiresAdminAuth || (to.path.startsWith("/admin") && to.path !== "/admin/login")) {
      // 未登录跳转管理后台登录页
      if (!adminAuthStore.isLoggedIn && !adminAuthStore.checkAuth()) {
        console.log("[RouterGuard] Admin route, not logged in, redirecting to /admin/login");
        next("/admin/login?redirect=" + to.path);
        return;
      }
      next();
      return;
    }

    // 普通用户路由处理
    // 未登录跳转登录页
    if (!userStore.isLoggedIn) {
      console.log("[RouterGuard] User not logged in, redirecting to /login");
      next("/login?redirect=" + to.path);
      return;
    }

    // 已登录访问登录页，重定向首页
    if (to.path === "/login") {
      next("/");
      return;
    }

    // 权限检查：如果路由需要权限，检查用户是否有权限
    const requiredPermissions = to.meta?.permissions as string[] | undefined;
    if (requiredPermissions && requiredPermissions.length > 0) {
      const hasPermission = requiredPermissions.some((p) => userStore.hasPermission(p));
      if (!hasPermission) {
        console.log("[RouterGuard] User lacks permission for:", to.path, "required:", requiredPermissions);
        next("/403");
        return;
      }
    }

    // 角色检查：如果路由需要角色，检查用户是否有角色
    const requiredRoles = to.meta?.roles as string[] | undefined;
    if (requiredRoles && requiredRoles.length > 0) {
      const hasRole = requiredRoles.some((r) => userStore.hasRole(r));
      if (!hasRole) {
        console.log("[RouterGuard] User lacks role for:", to.path, "required:", requiredRoles);
        next("/403");
        return;
      }
    }

    // 加载菜单（仅首次）
    if (!permissionStore.isLoaded) {
      console.log("[RouterGuard] Loading menus...");
      await permissionStore.fetchUserMenus();
      permissionStore.setLoaded(true);
    }

    next();
  });
};

export default setupRouterGuards;
