/**
 * 事件处理器类型
 */
export type EventHandler = (payload?: unknown) => void;

/**
 * 预定义模块事件常量
 */
export const ModuleEvents = {
  /** 用户登录成功 */
  USER_LOGGED_IN: "user:logged-in",
  /** 用户登出 */
  USER_LOGGED_OUT: "user:logged-out",
  /** 租户切换 */
  TENANT_CHANGED: "tenant:changed",
  /** 模块加载完成 */
  MODULE_LOADED: "module:loaded",
  /** 模块加载错误 */
  MODULE_ERROR: "module:error",
  /** 数据刷新请求 */
  DATA_REFRESH_REQUESTED: "data:refresh-requested",
} as const;

/**
 * 事件总线
 * 实现发布-订阅模式，支持跨模块通信
 */
export class EventBus {
  private handlers: Map<string, Set<EventHandler>> = new Map();

  /**
   * 订阅事件
   * @param event 事件名称
   * @param handler 事件处理器
   * @returns 取消订阅函数
   */
  on(event: string, handler: EventHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);

    return () => this.off(event, handler);
  }

  /**
   * 发布事件
   * @param event 事件名称
   * @param payload 事件数据
   */
  emit(event: string, payload?: unknown): void {
    const handlers = this.handlers.get(event);
    if (!handlers) return;

    for (const handler of handlers) {
      handler(payload);
    }
  }

  /**
   * 取消订阅
   * @param event 事件名称
   * @param handler 事件处理器
   */
  off(event: string, handler: EventHandler): void {
    const handlers = this.handlers.get(event);
    if (!handlers) return;

    handlers.delete(handler);
  }
}

/**
 * 全局事件总线实例
 */
let globalEventBus: EventBus | null = null;

/**
 * 获取全局事件总线实例
 * @returns EventBus 实例
 */
export function getEventBus(): EventBus {
  if (!globalEventBus) {
    globalEventBus = new EventBus();
  }
  return globalEventBus;
}
