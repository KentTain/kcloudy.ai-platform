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
];

export default aiRoutes;
