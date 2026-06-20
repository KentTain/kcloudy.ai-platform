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
 * 与后端 `framework.schemas.base.Success` 对齐
 */
export interface Success<T> {
  code: number;
  msg: string;
  data: T;
}

/**
 * 分页响应类型
 *
 * 与后端 `framework.schemas.base.SuccessExtra` 对齐
 * 用于 DataTable 组件的分页数据响应
 */
export interface SuccessExtra<T> {
  code: number;
  msg: string;
  data: T;
  total: number;
  page: number;
  page_size: number;
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


/**
 * 分页列表响应
 *
 * @deprecated 使用 `SuccessExtra<T[]>` 替代。后端已统一使用 `SuccessExtra` 响应格式。
 * 迁移示例：`ApiResponse<PaginatedListResponse<T>>` → `SuccessExtra<T[]>`
 */
export interface PaginatedListResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// 树节点类型
export type { TreeNode, TreeNodeTree, TreeAction, TreeSelectNode } from './tree'
