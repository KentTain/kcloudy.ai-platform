import { rawDel, rawGet, rawPost, rawPut } from "@/framework/api/client";
import type {
  ApiResponse,
  CacheConfig,
  ConnectionTestResult,
  ResourceCreate,
  DatabaseConfig,
  PaginatedListResponse,
  PubsubConfig,
  QueueConfig,
  ResourcePaginatedQuery,
  StorageConfig,
  ResourceUpdate,
} from "@/tenant/types";

// ==================== 数据库配置 ====================

/**
 * 获取数据库配置列表
 */
export const getDatabaseConfigs = (params?: ResourcePaginatedQuery) =>
  rawGet<ApiResponse<PaginatedListResponse<DatabaseConfig>>>("/tenant/admin/v1/resource-configs/databases", {
    params,
  });

/**
 * 获取数据库配置详情
 */
export const getDatabaseConfig = (id: string) =>
  rawGet<ApiResponse<DatabaseConfig>>(`/tenant/admin/v1/resource-configs/databases/${id}`);

/**
 * 创建数据库配置
 */
export const createDatabaseConfig = (data: ResourceCreate) =>
  rawPost<ApiResponse<DatabaseConfig>>("/tenant/admin/v1/resource-configs/databases", data);

/**
 * 更新数据库配置
 */
export const updateDatabaseConfig = (id: string, data: ResourceUpdate) =>
  rawPut<ApiResponse<DatabaseConfig>>(`/tenant/admin/v1/resource-configs/databases/${id}`, data);

/**
 * 删除数据库配置
 */
export const deleteDatabaseConfig = (id: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/resource-configs/databases/${id}`);

/**
 * 测试数据库连接
 */
export const testDatabaseConnection = (id: string) =>
  rawPost<ApiResponse<ConnectionTestResult>>(
    `/tenant/admin/v1/resource-configs/databases/${id}/test-connection`
  );

// ==================== 存储配置 ====================

/**
 * 获取存储配置列表
 */
export const getStorageConfigs = (params?: ResourcePaginatedQuery) =>
  rawGet<ApiResponse<PaginatedListResponse<StorageConfig>>>("/tenant/admin/v1/resource-configs/storages", { params });

/**
 * 获取存储配置详情
 */
export const getStorageConfig = (id: string) =>
  rawGet<ApiResponse<StorageConfig>>(`/tenant/admin/v1/resource-configs/storages/${id}`);

/**
 * 创建存储配置
 */
export const createStorageConfig = (data: ResourceCreate) =>
  rawPost<ApiResponse<StorageConfig>>("/tenant/admin/v1/resource-configs/storages", data);

/**
 * 更新存储配置
 */
export const updateStorageConfig = (id: string, data: ResourceUpdate) =>
  rawPut<ApiResponse<StorageConfig>>(`/tenant/admin/v1/resource-configs/storages/${id}`, data);

/**
 * 删除存储配置
 */
export const deleteStorageConfig = (id: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/resource-configs/storages/${id}`);

/**
 * 测试存储连接
 */
export const testStorageConnection = (id: string) =>
  rawPost<ApiResponse<ConnectionTestResult>>(
    `/tenant/admin/v1/resource-configs/storages/${id}/test-connection`
  );

// ==================== 缓存配置 ====================

/**
 * 获取缓存配置列表
 */
export const getCacheConfigs = (params?: ResourcePaginatedQuery) =>
  rawGet<ApiResponse<PaginatedListResponse<CacheConfig>>>("/tenant/admin/v1/resource-configs/caches", { params });

/**
 * 获取缓存配置详情
 */
export const getCacheConfig = (id: string) =>
  rawGet<ApiResponse<CacheConfig>>(`/tenant/admin/v1/resource-configs/caches/${id}`);

/**
 * 创建缓存配置
 */
export const createCacheConfig = (data: ResourceCreate) =>
  rawPost<ApiResponse<CacheConfig>>("/tenant/admin/v1/resource-configs/caches", data);

/**
 * 更新缓存配置
 */
export const updateCacheConfig = (id: string, data: ResourceUpdate) =>
  rawPut<ApiResponse<CacheConfig>>(`/tenant/admin/v1/resource-configs/caches/${id}`, data);

/**
 * 删除缓存配置
 */
export const deleteCacheConfig = (id: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/resource-configs/caches/${id}`);

/**
 * 测试缓存连接
 */
export const testCacheConnection = (id: string) =>
  rawPost<ApiResponse<ConnectionTestResult>>(
    `/tenant/admin/v1/resource-configs/caches/${id}/test-connection`
  );

// ==================== 队列配置 ====================

/**
 * 获取队列配置列表
 */
export const getQueueConfigs = (params?: ResourcePaginatedQuery) =>
  rawGet<ApiResponse<PaginatedListResponse<QueueConfig>>>("/tenant/admin/v1/resource-configs/queues", { params });

/**
 * 获取队列配置详情
 */
export const getQueueConfig = (id: string) =>
  rawGet<ApiResponse<QueueConfig>>(`/tenant/admin/v1/resource-configs/queues/${id}`);

/**
 * 创建队列配置
 */
export const createQueueConfig = (data: ResourceCreate) =>
  rawPost<ApiResponse<QueueConfig>>("/tenant/admin/v1/resource-configs/queues", data);

/**
 * 更新队列配置
 */
export const updateQueueConfig = (id: string, data: ResourceUpdate) =>
  rawPut<ApiResponse<QueueConfig>>(`/tenant/admin/v1/resource-configs/queues/${id}`, data);

/**
 * 删除队列配置
 */
export const deleteQueueConfig = (id: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/resource-configs/queues/${id}`);

/**
 * 测试队列连接
 */
export const testQueueConnection = (id: string) =>
  rawPost<ApiResponse<ConnectionTestResult>>(
    `/tenant/admin/v1/resource-configs/queues/${id}/test-connection`
  );

// ==================== 发布订阅配置 ====================

/**
 * 获取发布订阅配置列表
 */
export const getPubsubConfigs = (params?: ResourcePaginatedQuery) =>
  rawGet<ApiResponse<PaginatedListResponse<PubsubConfig>>>("/tenant/admin/v1/resource-configs/pubsubs", { params });

/**
 * 获取发布订阅配置详情
 */
export const getPubsubConfig = (id: string) =>
  rawGet<ApiResponse<PubsubConfig>>(`/tenant/admin/v1/resource-configs/pubsubs/${id}`);

/**
 * 创建发布订阅配置
 */
export const createPubsubConfig = (data: ResourceCreate) =>
  rawPost<ApiResponse<PubsubConfig>>("/tenant/admin/v1/resource-configs/pubsubs", data);

/**
 * 更新发布订阅配置
 */
export const updatePubsubConfig = (id: string, data: ResourceUpdate) =>
  rawPut<ApiResponse<PubsubConfig>>(`/tenant/admin/v1/resource-configs/pubsubs/${id}`, data);

/**
 * 删除发布订阅配置
 */
export const deletePubsubConfig = (id: string) =>
  rawDel<ApiResponse<void>>(`/tenant/admin/v1/resource-configs/pubsubs/${id}`);

/**
 * 测试发布订阅连接
 */
export const testPubsubConnection = (id: string) =>
  rawPost<ApiResponse<ConnectionTestResult>>(
    `/tenant/admin/v1/resource-configs/pubsubs/${id}/test-connection`
  );
