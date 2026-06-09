/**
 * 资源配置类型定义
 */

// 资源配置基础接口
export interface ResourceConfig {
  id: string;
  name: string;
  type: "database" | "storage" | "cache" | "queue" | "pubsub";
  config: Record<string, any>;
  tenant_count?: number; // 被引用的租户数量
  created_at: string;
  updated_at?: string;
}

// 数据库配置
export interface DatabaseConfig extends ResourceConfig {
  type: "database";
  config: {
    host: string;
    port: number;
    database: string;
    username: string;
    password?: string;
    ssl_mode?: string;
  };
}

// 存储配置
export interface StorageConfig extends ResourceConfig {
  type: "storage";
  config: {
    endpoint: string;
    bucket: string;
    access_key: string;
    secret_key?: string;
    region?: string;
  };
}

// 缓存配置
export interface CacheConfig extends ResourceConfig {
  type: "cache";
  config: {
    host: string;
    port: number;
    password?: string;
    db?: number;
  };
}

// 队列配置
export interface QueueConfig extends ResourceConfig {
  type: "queue";
  config: {
    host: string;
    port: number;
    username?: string;
    password?: string;
    vhost?: string;
  };
}

// 发布订阅配置
export interface PubsubConfig extends ResourceConfig {
  type: "pubsub";
  config: {
    type: "kafka" | "rabbitmq" | "redis";
    brokers?: string[];
    host?: string;
    port?: number;
    username?: string;
    password?: string;
  };
}

// 连通性测试结果
export interface ConnectionTestResult {
  success: boolean;
  latency?: number;
  error?: string;
}

// 资源配置查询参数
export interface ResourceConfigQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
}

// 创建资源配置参数
export interface CreateResourceConfigParams {
  name: string;
  config: Record<string, any>;
}

// 更新资源配置参数
export interface UpdateResourceConfigParams {
  name?: string;
  config?: Record<string, any>;
}
