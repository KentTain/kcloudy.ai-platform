import { describe, expect, it } from "vitest";
import { createRouter, createWebHistory } from "vue-router";

describe("Dynamic route registration with initial navigation", () => {
  it("should re-match NotFound route after dynamic routes are registered", async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: "/:pathMatch(.*)*",
          name: "NotFound",
          component: { template: "<div>404</div>" },
        },
      ],
    });

    // 初始导航到 /iam/users（此时路由未注册）
    await router.push("/iam/users");
    await router.isReady();
    expect(router.currentRoute.value.name).toBe("NotFound");

    // 注册 Root 路由
    router.addRoute({
      path: "/",
      name: "Root",
      component: { template: "<div>Root</div>" },
      children: [],
    });

    // 注册 IAM 模块路由
    router.addRoute("Root", {
      path: "iam",
      name: "IAMRoot",
      component: { template: "<router-view />" },
      children: [
        {
          path: "users",
          name: "UserManagement",
          component: { template: "<div>Users</div>" },
        },
      ],
    });

    // 关键：重新导航到当前路径
    await router.replace(router.currentRoute.value.fullPath);

    expect(router.currentRoute.value.name).toBe("UserManagement");
    expect(router.currentRoute.value.path).toBe("/iam/users");
  });
});
