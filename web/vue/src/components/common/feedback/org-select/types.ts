/**
 * OrganizationSelect 组件类型定义
 *
 * 提供组织树节点、选择事件等类型，与后端 API 响应对齐。
 * 独立于 people-select，专注于纯组织选择场景。
 *
 * @see server/python/src/iam/schemas/org_user.py 后端 Schema 定义
 */

import type { TreeNodeTree } from '@/framework/types/tree'
import type {
  OrganizationItem,
  OrganizationModelValue,
  OrganizationConfirmEvent,
  CheckState,
} from '../people-select/types'

// ==============================================================================
// 数据接口（与后端 API 响应对齐）
// ==============================================================================

/**
 * 组织选择树节点（用于渲染）
 *
 * 继承 TreeNodeTree，支持嵌套子节点渲染。
 * 用于组织选择组件的树形展示。
 */
export interface OrgSelectNode extends TreeNodeTree {
  /** 租户 ID */
  tenant_id: string
  /** 组织名称 */
  name: string
  /** 组织编码 */
  code?: string | null
  /** 状态 */
  status: string
  /** 是否有子节点（用于判断懒加载） */
  has_children?: boolean
  /** 子节点列表（覆盖 TreeNodeTree 的 children 类型） */
  children?: OrgSelectNode[]
}

/**
 * 扁平化组织节点（用于渲染优化）
 *
 * 将树形数据扁平化处理，优化大列表渲染性能。
 */
export interface OrgFlatNode {
  /** 节点 ID */
  id: string
  /** 组织名称 */
  name: string
  /** 父节点 ID */
  parent_id: string | null
  /** 树层级 */
  tree_level: number
  /** 是否是叶子节点 */
  tree_leaf: boolean
  /** 是否展开 */
  expanded: boolean
  /** 复选框状态 */
  checkState: CheckState
  /** 原始节点数据 */
  data: OrgSelectNode
}

// ==============================================================================
// 组件配置类型
// ==============================================================================

/**
 * 组织选择组件配置选项
 */
export interface OrgSelectOptions {
  /** 是否多选模式（默认 false） */
  multiple?: boolean
  /** 禁用的组织 ID 列表 */
  disabledIds?: string[]
  /** 已选中的组织 ID（单选模式）或 ID 数组（多选模式） */
  modelValue?: OrganizationModelValue
  /** 弹窗标题 */
  title?: string
  /** 确认按钮文本 */
  confirmText?: string
  /** 清空按钮文本 */
  clearText?: string
  /** 占位符文本 */
  placeholder?: string
}

// ==============================================================================
// 重导出共享类型
// ==============================================================================

/**
 * 组织简要信息
 *
 * @see people-select/types.ts OrganizationItem
 */
export type { OrganizationItem }

/**
 * 组织选择器值类型
 *
 * @see people-select/types.ts OrganizationModelValue
 */
export type { OrganizationModelValue }

/**
 * 组织选择确认事件
 *
 * @see people-select/types.ts OrganizationConfirmEvent
 */
export type { OrganizationConfirmEvent }

/**
 * 复选框状态
 *
 * @see people-select/types.ts CheckState
 */
export type { CheckState }
