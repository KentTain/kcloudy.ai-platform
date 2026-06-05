import { describe, expect, it } from "vitest";
import { createRouter, createWebHistory } from "vue-router";

describe("Home page route resolution", () => {
  it("should resolve root path '/' to Home page", async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: "/",
          name: "Root",
          component: { template: "<div>Root</div>" },
          children: [],
        },
        {
          path: "/:pathMatch(.*)*",
          name: "NotFound",
          component: { template: "<div>404</div>" },
        },
      ],
    });

    // 添加首页路由（模拟 demo 模块）
    router.addRoute("Root", {
      path: "",
      name: "Home",
      component: { template: "<div>Home</div>" },
      meta: { title: "首页" },
    });

    await router.push("/");
    await router.isReady();

    expect(router.currentRoute.value.name).toBe("Home");
    expect(router.currentRoute.value.path).toBe("/");
  });
});
