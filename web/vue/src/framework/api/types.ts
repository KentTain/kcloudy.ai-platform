/**
 * 统一 API 响应类型
 *
 * 与后端 `framework.common.response.ApiResponse` 对齐
 * code: HTTP status，200=成功，其他=失败
 */
export interface ApiResponse<T = unknown> {
  /** HTTP status code，200=成功，其他=失败 */
  code: number;
  /** 响应消息 */
  msg: string;
  /** 响应数据 */
  data: T | null;
  /** 分页响应时存在：总条数 */
  total?: number;
  /** 分页响应时存在：当前页码 */
  page?: number;
  /** 分页响应时存在：每页条数 */
  page_size?: number;
  /** 支持扩展字段 */
  [key: string]: unknown;
}

/**
 * 类型守卫：判断响应是否成功
 *
 * @param res - API 响应
 * @returns 如果 code === 200，返回 true
 *
 * @example
 * const res = await rawGet<ApiResponse<User>>("/api/users/1");
 * if (isSuccess(res)) {
 *   // res.data 是 User 类型
 *   console.log(res.data.name);
 * } else {
 *   // 显示错误 res.msg
 *   console.error(res.msg);
 * }
 */
export function isSuccess<T>(res: ApiResponse<T>): res is ApiResponse<T> & { data: T } {
  return res.code === 200;
}

/**
 * 类型守卫：判断响应是否失败
 *
 * @param res - API 响应
 * @returns 如果 code !== 200，返回 true
 */
export function isFail<T>(res: ApiResponse<T>): res is ApiResponse<T> & { data: T | null } {
  return res.code !== 200;
}

/**
 * 提取成功响应的数据，失败时抛出错误
 *
 * @param res - API 响应
 * @returns 成功时返回 data
 * @throws 失败时抛出包含 msg 的 Error
 *
 * @example
 * const user = await get<ApiResponse<User>>("/api/users/1").then(unwrap);
 */
export function unwrap<T>(res: ApiResponse<T>): T {
  if (res.code === 200) {
    return res.data as T;
  }
  throw new Error(res.msg);
}

/**
 * 构造分页响应（用于 DataTable remoteFetchFn）
 *
 * @param res - 原始 API 响应
 * @returns 符合 ApiResponse<T[]> 类型的分页响应
 *
 * @example
 * const res = await getUsers({ page, page_size });
 * return createPaginatedResponse(res);
 */
export function createPaginatedResponse<T>(
  res: Pick<ApiResponse<T[]>, 'code' | 'msg' | 'data' | 'total' | 'page' | 'page_size'>
): ApiResponse<T[]> {
  return {
    code: res.code,
    msg: res.msg,
    data: res.data ?? [],
    total: res.total ?? 0,
    page: res.page,
    page_size: res.page_size,
  };
}
