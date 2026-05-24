/**
 * 路由元信息类型
 */
export interface RouteMeta {
  /** 页面标题 */
  title?: string;
  /** 菜单图标 */
  icon?: string;
  /** 是否隐藏菜单 */
  hidden?: boolean;
  /** 是否需要登录 */
  requiresAuth?: boolean;
  /** 需要的权限码 */
  permissions?: string[];
  /** 需要的角色 */
  roles?: string[];
  /** 是否固定在 TagsView */
  affix?: boolean;
  /** 是否缓存页面 */
  keepAlive?: boolean;
}

/**
 * API 响应类型
 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

/**
 * 分页请求参数
 */
export interface PageParams {
  page: number;
  pageSize: number;
}

/**
 * 分页响应数据
 */
export interface PageResult<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
}

// 树节点类型
export type { TreeNode, TreeNodeTree, TreeComponentNode, TreeAction } from './tree'
