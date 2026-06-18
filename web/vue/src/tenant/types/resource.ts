/**
 * 资源配置类型定义
 */

import type { BasePaginatedQuery } from "@/framework/types";

// 资源配置基础接口
export interface ResourceConfig {
  id: string;
  name: string;
  tenant_count?: number; // 被引用的租户数量
  is_default?: boolean; // 是否为默认配置
  created_at: string;
  updated_at?: string;
}

// 数据库配置
export interface DatabaseConfig extends ResourceConfig {
  type: "database";
  host: string;
  port: number;
  database: string;
  username: string;
  password?: string;
}

// 存储配置
export interface StorageConfig extends ResourceConfig {
  type: "storage";
  endpoint: string;
  bucket: string;
  access_key: string;
  secret_key?: string;
  region?: string;
}

// 缓存配置
export interface CacheConfig extends ResourceConfig {
  type: "cache";
  host: string;
  port: number;
  password?: string;
  db?: number;
}

// 队列配置
export interface QueueConfig extends ResourceConfig {
  type: "queue";
  host: string;
  port: number;
  username?: string;
  password?: string;
  vhost?: string;
}

// 发布订阅配置
export interface PubsubConfig extends ResourceConfig {
  type: "pubsub";
  type_name: "kafka" | "rabbitmq" | "redis";
  brokers?: string[];
  host?: string;
  port?: number;
  username?: string;
  password?: string;
}

// 连通性测试结果
export interface ConnectionTestResult {
  success: boolean;
  latency?: number;
  error?: string;
}

// 资源配置查询参数
export interface ResourcePaginatedQuery extends BasePaginatedQuery {}

// 创建资源配置参数（扁平化结构）
export interface ResourceCreate {
  name: string;
  [key: string]: any; // 其他字段根据具体资源类型而定
}

// 更新资源配置参数（扁平化结构）
export interface ResourceUpdate {
  name?: string;
  [key: string]: any; // 其他字段根据具体资源类型而定
}
