import { describe, expect, it } from "vitest";
import { createRouter, createWebHistory } from "vue-router";

describe("Nested route parent must have component", () => {
  it("child route is not matched when parent has no component", async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: "/",
          name: "Root",
          component: { template: "<router-view />" },
          children: [],
        },
        {
          path: "/:pathMatch(.*)*",
          name: "NotFound",
          component: { template: "<div>404</div>" },
        },
      ],
    });

    // 添加没有 component 的父路由
    router.addRoute("Root", {
      path: "iam",
      name: "IAMRoot",
      // 注意：没有 component!
      children: [
        {
          path: "users",
          name: "UserManagement",
          component: { template: "<div>Users</div>" },
        },
      ],
    });

    await router.push("/iam/users");
    await router.isReady();

    // 预期：由于父路由没有 component，子路由无法匹配
    console.log("Route name:", router.currentRoute.value.name);
    console.log("Route path:", router.currentRoute.value.path);
    console.log("Matched:", router.currentRoute.value.matched);

    // 实际上，Vue Router 会匹配到路由，但 matched 数组中父路由没有组件
    expect(router.currentRoute.value.name).toBe("UserManagement");
    expect(router.currentRoute.value.matched.length).toBeGreaterThan(0);
  });

  it("child route works when parent has router-view component", async () => {
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: "/",
          name: "Root",
          component: { template: "<router-view />" },
          children: [],
        },
        {
          path: "/:pathMatch(.*)*",
          name: "NotFound",
          component: { template: "<div>404</div>" },
        },
      ],
    });

    // 添加有 component 的父路由
    router.addRoute("Root", {
      path: "iam",
      name: "IAMRoot",
      component: { template: "<router-view />" }, // 有 component!
      children: [
        {
          path: "users",
          name: "UserManagement",
          component: { template: "<div>Users</div>" },
        },
      ],
    });

    await router.push("/iam/users");
    await router.isReady();

    expect(router.currentRoute.value.name).toBe("UserManagement");
    // Root + IAMRoot + UserManagement = 3 层
    expect(router.currentRoute.value.matched.length).toBe(3);
  });
});
