import { describe, expect, it } from "vitest";
import { createRouter, createWebHistory, type Router } from "vue-router";

function addRootAndIamRoutes(router: Router) {
  router.addRoute({
    path: "/",
    name: "Root",
    component: { template: "<div>Root</div>" },
    children: [],
  });

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
}

describe("initial navigation with dynamic module routes", () => {
  it("should resolve dynamic module route when routes are registered before initial navigation", async () => {
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

    addRootAndIamRoutes(router);

    await router.push("/iam/users");
    await router.isReady();

    expect(router.currentRoute.value.name).toBe("UserManagement");
  });
});
