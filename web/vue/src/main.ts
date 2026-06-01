import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./framework/router";
import { setupRouterGuards } from "./framework/router/guards";
import { setupPermissionDirective } from "./framework/directives/permission";
import { setupFramework } from "./framework/module";
import { ENABLED_MODULES } from "./config/modules";

// Import module descriptors (conditionally based on config)
import { demoModule } from "./demo";
import { iamModule } from "./iam";
import { tenantModule } from "./tenant";

// Import admin routes
import { adminRoutes } from "./tenant/router";

// Import styles
import "./framework/styles/main.css";

// Build modules array based on ENABLED_MODULES config
const modules = [];
if (ENABLED_MODULES.includes("demo")) {
  modules.push(demoModule);
}
if (ENABLED_MODULES.includes("iam")) {
  modules.push(iamModule);
}
if (ENABLED_MODULES.includes("tenant")) {
  modules.push(tenantModule);
}

// 创建应用实例
const app = createApp(App);

console.log("[main.ts] App created, starting initialization...");

// Pinia 状态管理
const pinia = createPinia();
app.use(pinia);

console.log("[main.ts] Pinia installed");

// 路由守卫
setupRouterGuards(router);

console.log("[main.ts] Router guards setup");

// 注册异步路由
import { asyncRoutes } from "./framework/router";
console.log("[main.ts] Registering asyncRoutes:", asyncRoutes.map(r => r.path));
asyncRoutes.forEach((route) => router.addRoute(route));

console.log("[main.ts] After asyncRoutes, router has:", router.getRoutes().map(r => ({ name: r.name, path: r.path })));

// 注册管理后台路由
adminRoutes.forEach((route) => router.addRoute(route));

console.log("[main.ts] After adminRoutes, router has:", router.getRoutes().map(r => ({ name: r.name, path: r.path })));

// 安装路由插件
app.use(router);

console.log("[main.ts] Router installed, current route:", router.currentRoute.value.path, router.currentRoute.value.name);

// 权限指令
setupPermissionDirective(app);

// 设置框架并注册模块路由
console.log("[main.ts] Starting setupFramework...");
setupFramework({
  app,
  router,
  pinia,
  modules,
})
  .then(async () => {
    console.log("[main.ts] setupFramework completed");
    console.log("[main.ts] After setupFramework, router has:", router.getRoutes().map(r => ({ name: r.name, path: r.path })));

    // 等待路由准备好
    await router.isReady();

    console.log("[main.ts] Router ready, current route:", router.currentRoute.value.path, router.currentRoute.value.name);
    console.log("[main.ts] Current route matched:", router.currentRoute.value.matched.map(m => m.path));

    // 重新匹配当前路由（处理直接访问动态路由的情况）
    const currentRoute = router.currentRoute.value;
    if (currentRoute.name === "NotFound" || currentRoute.matched.length === 0) {
      console.log("[main.ts] Route is NotFound or unmatched, attempting to rematch...");
      // 使用 replace 重新匹配当前路径
      await router.replace(currentRoute.fullPath);
      console.log("[main.ts] After rematch, current route:", router.currentRoute.value.path, router.currentRoute.value.name);
    }

    // 挂载应用
    app.mount("#app");
    console.log("[main.ts] App mounted");
  })
  .catch((error) => {
    console.error("Failed to setup framework:", error);
  });
