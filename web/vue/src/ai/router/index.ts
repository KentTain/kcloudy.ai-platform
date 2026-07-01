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
    path: "ai/conversations",
    name: "ConversationList",
    component: () => import("@/ai/pages/ConversationListPage.vue"),
    meta: { title: "会话列表", icon: "list", requiresAuth: true },
  },
  {
    path: "ai/plugins/market",
    name: "AIPluginMarket",
    component: () => import("@/ai/pages/PluginMarketPage.vue"),
    meta: { title: "插件市场", icon: "store", requiresAuth: true },
  },
  {
    path: "ai/plugins",
    name: "AIPluginList",
    component: () => import("@/ai/pages/PluginList.vue"),
    meta: { title: "我的插件", icon: "package", requiresAuth: true },
  },
  {
    path: "ai/plugins/:pluginId/config",
    name: "AIPluginConfig",
    component: () => import("@/ai/pages/PluginConfigPage.vue"),
    meta: { title: "插件配置", hidden: true, requiresAuth: true },
  },
];

export default aiRoutes;
