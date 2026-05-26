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
 * 统一 API 响应类型
 *
 * 与后端 `framework.common.responses.ApiResponse` 对齐
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
  page_size: number;
}

/**
 * 分页响应数据
 *
 * 与后端 `TenantListVo` 等分页响应格式对齐
 */
export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// 树节点类型
export type { TreeNode, TreeNodeTree, TreeComponentNode, TreeAction } from './tree'
