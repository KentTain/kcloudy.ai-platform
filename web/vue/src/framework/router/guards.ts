import type { Router } from "vue-router";
import { useUserStore } from "@/framework/stores";
import { useMenuStore } from "@/framework/stores/menu";
import { useAdminAuthStore } from "@/tenant/stores/adminAuth";
import { getCurrentUser } from "@/iam/api/auth";
import { isDynamicRoutesReady, waitForDynamicRoutes } from "@/framework/module";
import { isSuccess } from "@/framework/api/types";
import { notifyError } from "@/framework/utils/feedback";

// 白名单路由
const whiteList = ["/login", "/admin/login", "/403", "/404"];

/**
 * 设置路由守卫
 */
export const setupRouterGuards = (router: Router) => {
  router.beforeEach(async (to, _from, next) => {
    console.log("[RouterGuard] Navigating to:", to.path, "name:", to.name, "matched:", to.matched.length);

    // 检查动态路由是否已准备好
    // 如果路由未匹配且动态路由未准备好，等待后重新导航
    if (to.matched.length === 0 && !isDynamicRoutesReady()) {
      console.log("[RouterGuard] Route not matched, waiting for dynamic routes...");

      // 等待动态路由注册完成
      await waitForDynamicRoutes();

      console.log("[RouterGuard] Dynamic routes ready, retrying navigation to:", to.fullPath);
      // 重新导航到目标路由（保留查询参数）
      next({ path: to.fullPath, replace: true });
      return;
    }

    const userStore = useUserStore();
    const menuStore = useMenuStore();
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

      // 权限检查
      const requiredPermissions = to.meta?.permissions as string[] | undefined;
      if (requiredPermissions && requiredPermissions.length > 0) {
        const hasPermission = requiredPermissions.some((p) => adminAuthStore.hasPermission(p));
        if (!hasPermission) {
          console.log("[RouterGuard] Admin lacks permission for:", to.path, "required:", requiredPermissions);
          next("/403");
          return;
        }
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

    // 已登录但 userInfo 为空，重新获取用户信息
    if (!userStore.userInfo) {
      console.log("[RouterGuard] User logged in but userInfo is null, fetching...");
      try {
        const response = await getCurrentUser();
        if (!isSuccess(response)) {
          notifyError(response.msg || "登录失败");
          throw new Error(response.msg || "登录失败");
        }
        // 手动转换用户信息
        const user = response.data;
        const defaultTenant = user.tenants?.find((t: any) => t.is_default);
        const currentTenant = user.tenants?.find((t: any) => t.id === user.tenant_id) || defaultTenant;

        userStore.setUserInfo({
          id: user.id,
          username: user.username,
          nickname: user.nickname || user.username,
          avatar: user.avatar,
          email: user.email,
          roles: user.roles || [],
          permissions: user.permissions || [],
          tenantId: user.tenant_id,
          tenantName: currentTenant?.name,
          tenantCode: currentTenant?.code,
          tenants: user.tenants?.map((t: any) => ({
            id: t.id,
            name: t.name,
            code: t.code,
            is_default: t.is_default,
          })),
        });

        // 同时设置菜单数据（/users/me 接口已返回 menus）
        if (user.menus && Array.isArray(user.menus)) {
          menuStore.setUserMenus(user.menus);
        }
      } catch (error) {
        console.error("[RouterGuard] Failed to fetch user info:", error);
        // 获取用户信息失败，可能是 token 过期，重定向到登录页
        next("/login?redirect=" + to.path);
        return;
      }
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

    next();
  });
};

export default setupRouterGuards;
