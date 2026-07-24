/**
 * 文档库管理模块路由配置
 *
 * 使用嵌套路由结构，所有路由位于 /document 路径下
 */

import type { RouteRecordRaw } from "vue-router";

export const documentRoutes: RouteRecordRaw[] = [
  {
    path: "document",
    name: "DocumentRoot",
    component: () => import("@/document/components/LibraryLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      {
        path: "libraries",
        name: "DocumentLibraryList",
        component: () => import("@/document/pages/library/LibraryList.vue"),
        meta: { title: "文档库", icon: "folder-open", requiresAuth: true },
      },
      {
        path: "libraries/:id",
        name: "DocumentLibraryDetail",
        component: () => import("@/document/pages/library/LibraryDetail.vue"),
        meta: { title: "文档库详情", hidden: true, requiresAuth: true },
      },
      {
        path: "tags",
        name: "DocumentTags",
        component: () => import("@/document/pages/TagsPage.vue"),
        meta: { title: "标签管理", icon: "tag", requiresAuth: true },
      },
      {
        path: "personas",
        name: "DocumentPersonas",
        component: () => import("@/document/pages/PersonasPage.vue"),
        meta: { title: "人设管理", icon: "user-circle", requiresAuth: true },
      },
    ],
  },
];

export default documentRoutes;
