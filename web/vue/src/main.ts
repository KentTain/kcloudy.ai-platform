import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./framework/router";
import { setupRouterGuards } from "./framework/router/guards";
import { setupPermissionDirective } from "./framework/directives/permission";
import { demoRoutes } from "./demo/router";

// 导入样式
import "./framework/styles/main.css";

// 创建应用实例
const app = createApp(App);

// Pinia 状态管理
const pinia = createPinia();
app.use(pinia);

// 路由
setupRouterGuards(router);

// 注册 Demo 路由
demoRoutes.forEach((route) => {
  router.addRoute(route);
});

app.use(router);

// 权限指令
setupPermissionDirective(app);

// 挂载应用
app.mount("#app");
