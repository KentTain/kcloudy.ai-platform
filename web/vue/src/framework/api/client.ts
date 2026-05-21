import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from "axios";

/**
 * API 客户端配置
 */
const defaultConfig: AxiosRequestConfig = {
  baseURL: "/api",
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
      // 添加认证 token
      const token = localStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse) => response.data,
    (error) => {
      const { response } = error;

      // 401 未登录
      if (response?.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
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

export default apiClient;
