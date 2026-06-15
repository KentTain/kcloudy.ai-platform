import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from "axios";

/**
 * API 客户端配置
 * baseURL 优先使用环境变量 VITE_API_BASE_URL，默认 /api
 */
const defaultConfig: AxiosRequestConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
};

/**
 * 创建 API 客户端实例
 */
export const createApiClient = (config?: AxiosRequestConfig): AxiosInstance => {
  const instance = axios.create({ ...defaultConfig, ...config });

  // 请求拦截器
  instance.interceptors.request.use(
    (config) => {
      // 根据请求路径判断使用哪个 token
      // 注意：/admin/v1/iam/* 和 /admin/v1/system-settings/* 是租户级管理 API，使用普通用户 token
      const isAdminRequest = config.url?.startsWith("/admin") &&
        !config.url?.startsWith("/admin/v1/iam") &&
        !config.url?.startsWith("/admin/v1/system-settings");
      const tokenKey = isAdminRequest ? "admin_token" : "token";
      const token = localStorage.getItem(tokenKey);

      if (token) {
        config.headers.Authorization = "Bearer " + token;
      }

      // 添加租户 ID 请求头
      const tenantId = localStorage.getItem("tenant_id");
      if (tenantId && !isAdminRequest) {
        config.headers["X-Tenant-Id"] = tenantId;
      }

      return config;
    },
    (error) => Promise.reject(error)
  );

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse) => response.data,
    (error) => {
      const { response, config } = error;

      // 判断是否为管理后台请求（租户级管理 API 使用普通用户 token）
      const isAdminRequest = config?.url?.startsWith("/admin") &&
        !config?.url?.startsWith("/admin/v1/iam") &&
        !config?.url?.startsWith("/admin/v1/system-settings");

      // 401 未登录
      if (response?.status === 401) {
        if (isAdminRequest) {
          localStorage.removeItem("admin_token");
          localStorage.removeItem("admin_info");
          window.location.href = "/admin/login";
        } else {
          localStorage.removeItem("token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("tenant_id");
          window.location.href = "/login";
        }
      }

      // 403 无权限
      if (response?.status === 403) {
        window.location.href = "/403";
      }

      return Promise.reject(error);
    }
  );

  return instance;
};

/**
 * 默认 API 客户端
 */
export const apiClient = createApiClient();

/**
 * 无前缀 API 客户端，用于后端根路径注册的接口（如 /admin、/console）
 */
export const rawApiClient = createApiClient({ baseURL: "" });

/**
 * GET 请求
 */
export const get = <T>(url: string, config?: AxiosRequestConfig): Promise<T> =>
  apiClient.get(url, config);

/**
 * POST 请求
 */
export const post = <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> =>
  apiClient.post(url, data, config);

/**
 * PUT 请求
 */
export const put = <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> =>
  apiClient.put(url, data, config);

/**
 * DELETE 请求
 */
export const del = <T>(url: string, config?: AxiosRequestConfig): Promise<T> =>
  apiClient.delete(url, config);

export const rawGet = <T>(url: string, config?: AxiosRequestConfig): Promise<T> =>
  rawApiClient.get(url, config);

export const rawPost = <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> => rawApiClient.post(url, data, config);

export const rawPut = <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> =>
  rawApiClient.put(url, data, config);

export const rawDel = <T>(url: string, config?: AxiosRequestConfig): Promise<T> =>
  rawApiClient.delete(url, config);

export default apiClient;
