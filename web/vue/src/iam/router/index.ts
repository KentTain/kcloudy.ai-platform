import type { RouteRecordRaw } from "vue-router";

/**
 * IAM 模块路由配置
 *
 * 使用嵌套路由结构，所有路由位于 /iam 路径下
 */
export const iamRoutes: RouteRecordRaw[] = [
  {
    path: "iam",
    name: "IAMRoot",
    component: () => import("@/iam/layouts/IAMLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      // 用户管理
      {
        path: "users",
        name: "UserManagement",
        component: () => import("@/iam/pages/users/UserList.vue"),
        meta: { title: "用户管理", icon: "user", requiresAuth: true },
      },
      {
        path: "users/create",
        name: "UserCreate",
        component: () => import("@/iam/pages/users/UserForm.vue"),
        meta: { title: "创建用户", hidden: true, requiresAuth: true },
      },
      {
        path: "users/:id",
        name: "UserDetail",
        component: () => import("@/iam/pages/users/UserDetail.vue"),
        meta: { title: "用户详情", hidden: true, requiresAuth: true },
      },
      {
        path: "users/:id/edit",
        name: "UserEdit",
        component: () => import("@/iam/pages/users/UserForm.vue"),
        meta: { title: "编辑用户", hidden: true, requiresAuth: true },
      },

      // 角色管理
      {
        path: "roles",
        name: "RoleManagement",
        component: () => import("@/iam/pages/roles/RoleList.vue"),
        meta: { title: "角色管理", icon: "role", requiresAuth: true },
      },
      {
        path: "roles/create",
        name: "RoleCreate",
        component: () => import("@/iam/pages/roles/RoleForm.vue"),
        meta: { title: "创建角色", hidden: true, requiresAuth: true },
      },
      {
        path: "roles/:id",
        name: "RoleDetail",
        component: () => import("@/iam/pages/roles/RoleForm.vue"),
        meta: { title: "角色详情/编辑", hidden: true, requiresAuth: true },
      },

      // 权限管理
      {
        path: "permissions",
        name: "PermissionManagement",
        component: () => import("@/iam/pages/permissions/PermissionList.vue"),
        meta: { title: "权限管理", icon: "lock", requiresAuth: true },
      },

      // 部门管理
      {
        path: "departments",
        name: "DepartmentManagement",
        component: () => import("@/iam/pages/departments/DepartmentPage.vue"),
        meta: { title: "部门管理", icon: "department", requiresAuth: true },
      },

      // 个人中心
      {
        path: "profile",
        name: "Profile",
        component: () => import("@/iam/pages/profile/Profile.vue"),
        meta: { title: "个人中心", icon: "user-circle", requiresAuth: true },
      },
    ],
  },
];

export default iamRoutes;
