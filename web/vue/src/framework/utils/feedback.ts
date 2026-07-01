/**
 * 反馈工具函数
 *
 * 提供通知、确认和错误消息提取功能
 */

import { toast } from "vue-sonner"

/**
 * 成功提示
 * @param message - 提示消息
 * @param options - 可选配置（id: 消息ID用于合并，duration: 持续时间ms）
 */
export const notifySuccess = (message: string, options?: { id?: string; duration?: number }) => {
  toast.success(message, options)
}

/**
 * 错误提示
 * @param message - 提示消息
 * @param options - 可选配置（id: 消息ID用于合并，duration: 持续时间ms）
 */
export const notifyError = (message: string, options?: { id?: string; duration?: number }) => {
  toast.error(message, options)
}

/**
 * 警告提示
 * @param message - 提示消息
 * @param options - 可选配置（id: 消息ID用于合并，duration: 持续时间ms）
 */
export const notifyWarning = (message: string, options?: { id?: string; duration?: number }) => {
  toast.warning(message, options)
}

/**
 * 信息提示
 * @param message - 提示消息
 * @param options - 可选配置（id: 消息ID用于合并，duration: 持续时间ms）
 */
export const notifyInfo = (message: string, options?: { id?: string; duration?: number }) => {
  toast.info(message, options)
}

/**
 * 批量操作成功提示
 * @param count - 处理数量
 * @param action - 操作名称（如"删除"、"导入"）
 */
export const notifyBatchSuccess = (count: number, action: string) => {
  toast.success(`${action}成功`, {
    id: `batch-${action}`,
    description: `已处理 ${count} 项`
  })
}

/**
 * 批量操作失败提示
 * @param count - 失败数量
 * @param action - 操作名称（如"删除"、"导入"）
 */
export const notifyBatchError = (count: number, action: string) => {
  toast.error(`${action}失败`, {
    id: `batch-${action}`,
    description: `${count} 项处理失败`
  })
}

/**
 * 确认对话框
 * @param message - 确认消息
 * @returns 用户是否确认
 */
export const confirmAction = (message: string) => window.confirm(message)

/**
 * 提取错误消息
 * @param error - 错误对象
 * @param fallback - 默认消息
 * @returns 错误消息字符串
 */
export const getErrorMessage = (error: unknown, fallback: string) => {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { msg?: string; detail?: string } } }).response
    return response?.data?.msg || response?.data?.detail || fallback
  }

  if (error instanceof Error) {
    return error.message || fallback
  }

  return fallback
}
