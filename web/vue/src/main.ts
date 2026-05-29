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

// Pinia 状态管理
const pinia = createPinia();
app.use(pinia);

// 路由守卫
setupRouterGuards(router);

// 注册异步路由
import { asyncRoutes } from "./framework/router";
asyncRoutes.forEach((route) => router.addRoute(route));

app.use(router);

// 权限指令
setupPermissionDirective(app);

// 设置框架并注册模块
setupFramework({
  app,
  router,
  pinia,
  modules,
})
  .then(() => {
    // 挂载应用
    app.mount("#app");
  })
  .catch((error) => {
    console.error("Failed to setup framework:", error);
  });
