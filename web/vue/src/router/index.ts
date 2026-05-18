import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import MainLayout from "@/layouts/MainLayout.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: MainLayout,
    children: [
      {
        path: "",
        name: "Home",
        component: () => import("@/pages/HomePage.vue"),
        meta: {
          title: "首页",
        },
      },
      {
        path: "datasets",
        name: "Datasets",
        component: () => import("@/pages/DatasetListPage.vue"),
        meta: {
          title: "知识库列表",
        },
      },
      {
        path: "datasets/:id",
        name: "DatasetDetail",
        component: () => import("@/pages/DatasetDetailPage.vue"),
        meta: {
          title: "知识库详情",
        },
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/pages/NotFoundPage.vue"),
    meta: {
      title: "页面未找到",
    },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation guard for auth (placeholder)
router.beforeEach((to, _from, next) => {
  // Update document title
  const title = to.meta.title as string;
  if (title) {
    document.title = `${title} - Demo`;
  }

  // Check auth if needed (future implementation)
  // if (to.meta.requiresAuth) {
  //   const isAuthenticated = checkAuth();
  //   if (!isAuthenticated) {
  //     next({ name: 'Login' });
  //     return;
  //   }
  // }

  next();
});

export default router;
