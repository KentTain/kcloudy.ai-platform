/**
 * PeopleSelect 组件 API 服务
 *
 * 提供用户、组织的查询、搜索、批量获取等功能。
 * 支持请求合并（50ms 内的多个请求合并为一次批量查询）和缓存。
 */

import { get, post } from '@/framework/api/client'
import type { ApiResponse } from '@/framework/api/types'
import { isSuccess } from '@/framework/api/types'
import type { UserItem, OrganizationItem, OrgTreeNode } from './types'

// ==============================================================================
// 类型定义
// ==============================================================================

/**
 * 用户搜索参数
 */
export interface UserSearchParams {
  /** 搜索关键词 */
  keyword: string
  /** 当前页码 */
  page?: number
  /** 每页条数 */
  page_size?: number
}

/**
 * 组织搜索参数
 */
export interface OrganizationSearchParams {
  /** 搜索关键词 */
  keyword: string
  /** 当前页码 */
  page?: number
  /** 每页条数 */
  page_size?: number
}

/**
 * 批量请求参数
 */
export interface BatchRequest {
  ids: string[]
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ==============================================================================
// 缓存和请求合并机制
// ==============================================================================

/** 用户缓存 */
const userCache = new Map<string, UserItem>()

/** 组织缓存 */
const orgCache = new Map<string, OrganizationItem>()

/** 待处理的用户 ID 队列 */
let pendingUserIds = new Set<string>()

/** 待处理的组织 ID 队列 */
let pendingOrgIds = new Set<string>()

/** 用户请求合并定时器 */
let userBatchTimer: ReturnType<typeof setTimeout> | null = null

/** 组织请求合并定时器 */
let orgBatchTimer: ReturnType<typeof setTimeout> | null = null

/** 用户请求回调映射 */
const userCallbacks = new Map<string, Array<(user: UserItem | null) => void>>()

/** 组织请求回调映射 */
const orgCallbacks = new Map<string, Array<(org: OrganizationItem | null) => void>>()

/** 请求合并延迟（毫秒） */
const BATCH_DELAY = 50

/**
 * 批量获取用户详情
 */
async function fetchUsersBatch(ids: string[]): Promise<Map<string, UserItem>> {
  const result = new Map<string, UserItem>()

  if (ids.length === 0) return result

  try {
    const res = await post<ApiResponse<{ items: UserItem[] }>>('/iam/console/v1/users/batch', { user_ids: ids })

    if (isSuccess(res) && res.data) {
      for (const user of res.data.items) {
        result.set(user.id, user)
        userCache.set(user.id, user)
      }
    }
  } catch (error) {
    console.error('Failed to fetch users batch:', error)
  }

  return result
}

/**
 * 批量获取组织详情
 */
async function fetchOrganizationsBatch(ids: string[]): Promise<Map<string, OrganizationItem>> {
  const result = new Map<string, OrganizationItem>()

  if (ids.length === 0) return result

  try {
    const res = await post<ApiResponse<{ items: OrganizationItem[] }>>('/iam/console/v1/organizations/batch', { org_ids: ids })

    if (isSuccess(res) && res.data) {
      for (const org of res.data.items) {
        result.set(org.id, org)
        orgCache.set(org.id, org)
      }
    }
  } catch (error) {
    console.error('Failed to fetch organizations batch:', error)
  }

  return result
}

/**
 * 执行用户批量请求
 */
function executeUserBatch() {
  const ids = Array.from(pendingUserIds)
  pendingUserIds = new Set()
  userBatchTimer = null

  fetchUsersBatch(ids).then((users) => {
    // 触发所有等待的回调
    for (const [id, callbacks] of userCallbacks) {
      const user = users.get(id) || null
      callbacks.forEach(cb => cb(user))
    }
    userCallbacks.clear()
  })
}

/**
 * 执行组织批量请求
 */
function executeOrgBatch() {
  const ids = Array.from(pendingOrgIds)
  pendingOrgIds = new Set()
  orgBatchTimer = null

  fetchOrganizationsBatch(ids).then((orgs) => {
    // 触发所有等待的回调
    for (const [id, callbacks] of orgCallbacks) {
      const org = orgs.get(id) || null
      callbacks.forEach(cb => cb(org))
    }
    orgCallbacks.clear()
  })
}

// ==============================================================================
// 公开 API 函数
// ==============================================================================

/**
 * 获取用户详情（带缓存和请求合并）
 *
 * @param userId - 用户 ID
 * @returns 用户详情，不存在则返回 null
 *
 * @example
 * const user = await fetchUserDetails('user-123')
 * if (user) {
 *   console.log(user.nickname)
 * }
 */
export function fetchUserDetails(userId: string): Promise<UserItem | null> {
  return new Promise((resolve) => {
    // 检查缓存
    const cached = userCache.get(userId)
    if (cached) {
      resolve(cached)
      return
    }

    // 添加到待处理队列
    pendingUserIds.add(userId)

    // 注册回调
    const callbacks = userCallbacks.get(userId) || []
    callbacks.push(resolve)
    userCallbacks.set(userId, callbacks)

    // 设置定时器
    if (!userBatchTimer) {
      userBatchTimer = setTimeout(executeUserBatch, BATCH_DELAY)
    }
  })
}

/**
 * 获取组织详情（带缓存和请求合并）
 *
 * @param orgId - 组织 ID
 * @returns 组织详情，不存在则返回 null
 *
 * @example
 * const org = await fetchOrganizationDetails('org-123')
 * if (org) {
 *   console.log(org.name)
 * }
 */
export function fetchOrganizationDetails(orgId: string): Promise<OrganizationItem | null> {
  return new Promise((resolve) => {
    // 检查缓存
    const cached = orgCache.get(orgId)
    if (cached) {
      resolve(cached)
      return
    }

    // 添加到待处理队列
    pendingOrgIds.add(orgId)

    // 注册回调
    const callbacks = orgCallbacks.get(orgId) || []
    callbacks.push(resolve)
    orgCallbacks.set(orgId, callbacks)

    // 设置定时器
    if (!orgBatchTimer) {
      orgBatchTimer = setTimeout(executeOrgBatch, BATCH_DELAY)
    }
  })
}

/**
 * 搜索用户
 *
 * @param params - 搜索参数
 * @returns 分页用户列表
 *
 * @example
 * const result = await searchUsers({ keyword: '张三', page: 1, page_size: 10 })
 * console.log(result.items, result.total)
 */
export async function searchUsers(params: UserSearchParams): Promise<PaginatedResponse<UserItem>> {
  const { keyword, page = 1, page_size = 10 } = params

  const res = await get<ApiResponse<UserItem[]>>('/iam/console/v1/users/search', {
    params: { keyword, page, page_size }
  })

  if (isSuccess(res) && res.data) {
    // 更新缓存
    for (const user of res.data) {
      userCache.set(user.id, user)
    }

    return {
      items: res.data,
      total: res.total ?? 0,
      page: res.page ?? page,
      page_size: res.page_size ?? page_size
    }
  }

  return {
    items: [],
    total: 0,
    page,
    page_size
  }
}

/**
 * 搜索组织
 *
 * @param params - 搜索参数
 * @returns 分页组织列表
 *
 * @example
 * const result = await searchOrganizations({ keyword: '研发部', page: 1, page_size: 10 })
 * console.log(result.items, result.total)
 */
export async function searchOrganizations(params: OrganizationSearchParams): Promise<PaginatedResponse<OrganizationItem>> {
  const { keyword, page = 1, page_size = 10 } = params

  const res = await get<ApiResponse<OrganizationItem[]>>('/iam/console/v1/organizations/search', {
    params: { keyword, page, page_size }
  })

  if (isSuccess(res) && res.data) {
    // 更新缓存
    for (const org of res.data) {
      orgCache.set(org.id, org)
    }

    return {
      items: res.data,
      total: res.total ?? 0,
      page: res.page ?? page,
      page_size: res.page_size ?? page_size
    }
  }

  return {
    items: [],
    total: 0,
    page,
    page_size
  }
}

/**
 * 加载组织人员树
 *
 * @param parentId - 父组织 ID，不传则加载根节点
 * @returns 组织人员树节点列表
 *
 * @example
 * // 加载根节点
 * const rootNodes = await loadOrgUserTree()
 *
 * // 加载指定组织的子节点
 * const childNodes = await loadOrgUserTree('org-123')
 */
export async function loadOrgUserTree(parentId?: string): Promise<OrgTreeNode[]> {
  const params = parentId ? { parent_id: parentId } : {}

  const res = await get<ApiResponse<{ items: OrgTreeNode[] }>>('/iam/console/v1/org-users/tree', { params })

  if (isSuccess(res) && res.data) {
    // 更新缓存
    for (const node of res.data.items) {
      orgCache.set(node.id, {
        id: node.id,
        tenant_id: node.tenant_id,
        name: node.name,
        code: node.code,
        status: node.status,
        parent_id: node.parent_id,
        tree_level: node.tree_level,
        tree_leaf: node.tree_leaf,
        tree_sort: node.tree_sort,
        tree_sorts: node.tree_sorts,
        tree_names: node.tree_names,
        parent_ids: node.parent_ids
      })

      // 更新用户缓存
      for (const user of node.users) {
        userCache.set(user.id, user)
      }
    }

    return res.data.items
  }

  return []
}

/**
 * 加载组织下的用户列表
 *
 * @param orgId - 组织 ID
 * @returns 用户列表
 *
 * @example
 * const users = await loadOrgUsers('org-123')
 */
export async function loadOrgUsers(orgId: string): Promise<UserItem[]> {
  const res = await get<ApiResponse<UserItem[]>>(`/iam/console/v1/org-users/${orgId}/users`)

  if (isSuccess(res) && res.data) {
    // 更新缓存
    for (const user of res.data) {
      userCache.set(user.id, user)
    }

    return res.data
  }

  return []
}

/**
 * 清除用户缓存
 */
export function clearUserCache(): void {
  userCache.clear()
}

/**
 * 清除组织缓存
 */
export function clearOrgCache(): void {
  orgCache.clear()
}

/**
 * 清除所有缓存
 */
export function clearAllCache(): void {
  userCache.clear()
  orgCache.clear()
}
