/**
 * 反馈工具函数
 *
 * 提供通知、确认和错误消息提取功能
 */

export const notifySuccess = (message: string) => {
  console.info(message);
};

export const notifyError = (message: string) => {
  console.error(message);
};

export const confirmAction = (message: string) => window.confirm(message);

export const getErrorMessage = (error: unknown, fallback: string) => {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as { response?: { data?: { message?: string; detail?: string } } }).response;
    return response?.data?.message || response?.data?.detail || fallback;
  }

  if (error instanceof Error) {
    return error.message || fallback;
  }

  return fallback;
};
