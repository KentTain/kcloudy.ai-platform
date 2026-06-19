import { describe, expect, it, vi } from "vitest";
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { ModuleRegistry } from "@/framework/module/registry";
import type { ModuleDescriptor } from "@/framework/module/types";

describe("Route registration timing and rootRoute lookup", () => {
  it("should find rootRoute after asyncRoutes are registered", async () => {
    const router = createRouter({
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

    // 模拟 main.ts 中的 asyncRoutes 注册
    router.addRoute({
      path: "/",
      name: "Root",
      component: { template: "<router-view />" },
      children: [],
    });

    // 模拟 registerRoutes 函数
    const rootRoute = router
      .getRoutes()
      .find((r) => r.path === "/" && r.name === "Root");

    console.log("rootRoute found:", rootRoute?.name, rootRoute?.path);
    expect(rootRoute).toBeDefined();
    expect(rootRoute?.name).toBe("Root");
  });

  it("should correctly register nested module routes to Root", async () => {
    const router = createRouter({
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

    // 模拟 asyncRoutes 注册
    router.addRoute({
      path: "/",
      name: "Root",
      component: { template: "<router-view />" },
      children: [],
    });

    // 模拟 setupFramework 中的路由注册
    const rootRoute = router
      .getRoutes()
      .find((r) => r.path === "/" && r.name === "Root");

    // IAM 模块路由（使用 RouterView 作为父组件）
    const iamRoutes: RouteRecordRaw[] = [
      {
        path: "iam",
        name: "IAMRoot",
        component: { template: "<router-view />" },
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
    ];

    // 注册模块路由
    for (const route of iamRoutes) {
      router.addRoute(rootRoute!.name!, route);
    }

    // 打印所有路由
    console.log("All routes after registration:");
    router.getRoutes().forEach(r => {
      console.log(`  - ${r.name}: ${r.path}, hasComponent: ${!!r.components}`);
    });

    // 测试路由匹配
    await router.push("/iam/users");
    await router.isReady();

    console.log("Current route:", router.currentRoute.value.name, router.currentRoute.value.path);
    console.log("Matched:", router.currentRoute.value.matched.map(m => ({ name: m.name, path: m.path, hasComponent: !!m.components })));

    expect(router.currentRoute.value.name).toBe("UserManagement");
  });
});
