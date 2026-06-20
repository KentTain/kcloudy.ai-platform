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
 * 列表查询基类（非分页）
 */
export interface BaseQuery {
  keyword?: string;
}

/**
 * 分页查询基类
 *
 * 与后端 `framework.schemas.base.BasePaginatedQuery` 对齐
 * page 和 page_size 有默认值，因此为可选字段
 */
export interface BasePaginatedQuery extends BaseQuery {
  page?: number;
  page_size?: number;
}

// 树节点类型
export type { TreeNode, TreeNodeTree, TreeAction, TreeSelectNode } from './tree'
