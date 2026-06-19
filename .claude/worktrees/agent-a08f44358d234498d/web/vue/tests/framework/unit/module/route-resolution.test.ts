import { beforeEach, describe, expect, it, vi } from "vitest";
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { ModuleRegistry } from "@/framework/module/registry";
import type { ModuleDescriptor } from "@/framework/module/types";

describe("IAM route registration and path resolution", () => {
  let router: ReturnType<typeof createRouter>;
  let registry: ModuleRegistry;

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: "/login",
          name: "Login",
          component: { template: "<div>Login</div>" },
        },
        {
          path: "/:pathMatch(.*)*",
          name: "NotFound",
          component: { template: "<div>404</div>" },
        },
      ],
    });
    registry = new ModuleRegistry();
  });

  it("IAM nested routes should resolve to /iam/users after registration", async () => {
    // 先添加 Root 路由（模拟 main.ts 中的 asyncRoutes）
    router.addRoute({
      path: "/",
      name: "Root",
      component: { template: "<div>Root</div>" },
      children: [],
    });

    // 定义 IAM 模块（使用嵌套结构）
    const iamModule: ModuleDescriptor = {
      name: "iam",
      version: "1.0.0",
      getRoutes: () => [
        {
          path: "iam",
          name: "IAMRoot",
          meta: { requiresAuth: true },
          children: [
            {
              path: "users",
              name: "UserManagement",
              component: { template: "<div>Users</div>" },
              meta: { title: "用户管理" },
            },
          ],
        } as RouteRecordRaw,
      ],
    };

    // 注册模块并获取路由
    registry.register(iamModule);
    const routes = registry.getRoutes();

    // 动态添加路由到 Root 下
    const rootRoute = router.getRoutes().find((r) => r.path === "/" && r.children);
    for (const route of routes) {
      router.addRoute(rootRoute!.name!, route);
    }

    // 打印所有路由用于调试
    const allRoutes = router.getRoutes();
    console.log("All routes:", allRoutes.map(r => ({ name: r.name, path: r.path })));

    // 尝试解析 /iam/users
    await router.push("/iam/users");
    await router.isReady();

    expect(router.currentRoute.value.name).toBe("UserManagement");
    expect(router.currentRoute.value.path).toBe("/iam/users");
  });
});
