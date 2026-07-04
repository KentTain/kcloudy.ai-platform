import type { RouteRecordRaw } from "vue-router";

/**
 * AI 模块路由配置
 */
export const aiRoutes: RouteRecordRaw[] = [
  {
    path: "ai",
    name: "AIChat",
    component: () => import("@/ai/pages/ChatPage.vue"),
    meta: { title: "AI 对话", icon: "message-square", requiresAuth: true },
  },
  {
    path: "ai/plugins",
    name: "AIPlugins",
    component: () => import("@/ai/pages/PluginManagePage.vue"),
    meta: { title: "插件管理", icon: "package", requiresAuth: true },
  },
  {
    path: "ai/plugins/:pluginId/config",
    name: "AIPluginConfig",
    component: () => import("@/ai/pages/PluginConfigPage.vue"),
    meta: { title: "插件配置", hidden: true, requiresAuth: true },
  },
  {
    path: "ai/model-config",
    name: "AIModelConfig",
    component: () => import("@/ai/pages/ModelConfigPage.vue"),
    meta: { title: "模型配置", icon: "cpu", requiresAuth: true },
  },
];

export default aiRoutes;
