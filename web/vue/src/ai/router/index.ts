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
];

export default aiRoutes;
