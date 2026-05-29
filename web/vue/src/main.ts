import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./framework/router";
import { setupRouterGuards } from "./framework/router/guards";
import { setupPermissionDirective } from "./framework/directives/permission";
import { setupFramework } from "./framework/module";

// 导入模块描述符
import { demoModule } from "./demo";
import { iamModule } from "./iam";
import { tenantModule } from "./tenant";

// 导入样式
import "./framework/styles/main.css";

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
  modules: [demoModule, iamModule, tenantModule],
})
  .then(() => {
    // 挂载应用
    app.mount("#app");
  })
  .catch((error) => {
    console.error("Failed to setup framework:", error);
  });
