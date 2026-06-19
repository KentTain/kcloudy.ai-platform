/**
 * MessageBox 服务
 * 类似 Element Plus 的 ElMessageBox，提供 Promise 风格的 API
 */

import { type App, createApp, h, ref } from "vue";

import type { MessageBoxOptions, MessageBoxType } from "./MessageBox.vue";
import MessageBoxComponent from "./MessageBox.vue";

/**
 * MessageBox 实例接口
 */
interface MessageBoxInstance {
  close: () => void;
  open: (options?: MessageBoxOptions) => void;
}

/**
 * MessageBox 服务类
 */
class MessageBoxService {
  private instance: MessageBoxInstance | null = null;
  private container: HTMLElement | null = null;
  private app: App | null = null;

  /**
   * 创建 MessageBox 实例并挂载到 DOM
   */
  private createInstance(): void {
    // 创建容器元素
    this.container = document.createElement("div");
    this.container.className = "message-box-container";
    document.body.appendChild(this.container);

    // 创建实例方法引用
    const instanceRef: MessageBoxInstance = {
      close: () => {},
      open: () => {},
    };

    // 创建 Vue 应用
    this.app = createApp({
      setup() {
        const messageBoxRef = ref<MessageBoxInstance>();

        // 当组件挂载后，将组件方法赋值给实例引用
        const updateInstance = () => {
          if (messageBoxRef.value) {
            instanceRef.open = (options?: MessageBoxOptions) => {
              messageBoxRef.value?.open(options);
            };
            instanceRef.close = () => {
              messageBoxRef.value?.close();
            };
          }
        };

        // 监听 messageBoxRef 变化
        return () =>
          h(
            MessageBoxComponent,
            {
              onVnodeMounted: updateInstance,
              ref: messageBoxRef,
            },
            {
              // 使用默认插槽
              default: () => null,
            },
          );
      },
    });

    // 挂载应用并保存实例引用
    this.app.mount(this.container);
    this.instance = instanceRef;
  }

  /**
   * 获取 MessageBox 实例
   */
  private getInstance(): MessageBoxInstance {
    if (!this.instance) {
      this.createInstance();
    }
    // createInstance() 确保 this.instance 被设置，使用非空断言
    return this.instance!;
  }

  /**
   * 显示确认对话框
   *
   * @param options - 对话框选项
   * @returns Promise，用户点击确认返回 true，取消抛出错误
   *
   * @example
   * ```ts
   * import { MessageBox } from '@/components/common/feedback/message-box';
   *
   * // 基础用法
   * MessageBox.confirm({
   *   title: '确认删除',
   *   content: '删除后数据将无法恢复',
   *   type: 'warning'
   * }).then(() => {
   *   // 用户点击确认
   *   console.log('已删除');
   * }).catch(() => {
   *   // 用户点击取消
   *   console.log('已取消');
   * });
   *
   * // async/await 用法
   * try {
   *   await MessageBox.confirm({
   *     title: '确认保存',
   *     type: 'info'
   *   });
   *   // 用户点击确认
   *   console.log('已保存');
   * } catch {
   *   // 用户点击取消
   *   console.log('已取消');
   * }
   * ```
   */
  confirm(options: MessageBoxOptions): Promise<boolean> {
    return new Promise((resolve, reject) => {
      const instance = this.getInstance();

      // 修改 beforeClose 以支持 Promise
      const modifiedOptions: MessageBoxOptions = {
        ...options,
        beforeClose: (action, done) => {
          // 如果用户传入了 beforeClose，先执行它
          if (options.beforeClose) {
            options.beforeClose(action, () => {
              if (action === "confirm") {
                resolve(true);
              } else {
                reject(new Error("User cancelled"));
              }
              done();
            });
          } else {
            // 没有自定义 beforeClose，直接返回结果
            if (action === "confirm") {
              resolve(true);
            } else {
              reject(new Error("User cancelled"));
            }
            done();
          }
        },
      };

      instance.open(modifiedOptions);
    });
  }

  /**
   * 快捷方法：显示警告对话框
   */
  alert(content: string, title = "提示"): Promise<boolean> {
    return this.confirm({
      content,
      showCancel: false,
      title,
      type: "warning",
    });
  }

  /**
   * 快捷方法：显示成功提示
   */
  success(content: string, title = "成功"): Promise<boolean> {
    return this.confirm({
      content,
      showCancel: false,
      title,
      type: "success",
    });
  }

  /**
   * 快捷方法：显示错误提示
   */
  error(content: string, title = "错误"): Promise<boolean> {
    return this.confirm({
      content,
      showCancel: false,
      title,
      type: "error",
    });
  }

  /**
   * 快捷方法：显示信息提示
   */
  info(content: string, title = "提示"): Promise<boolean> {
    return this.confirm({
      content,
      showCancel: false,
      title,
      type: "info",
    });
  }

  /**
   * 快捷方法：显示确认对话框（带取消按钮）
   */
  async confirmWithOptions(content: string, title = "确认", type: MessageBoxType = "warning"): Promise<boolean> {
    return this.confirm({
      content,
      title,
      type,
    });
  }
}

// 创建全局单例
const messageBoxService = new MessageBoxService();

// 导出服务对象
export const MessageBox = {
  alert: (content: string, title?: string) => messageBoxService.alert(content, title),
  confirm: (options: MessageBoxOptions) => messageBoxService.confirm(options),
  confirmWithOptions: (content: string, title?: string, type?: MessageBoxType) => messageBoxService.confirmWithOptions(content, title, type),
  error: (content: string, title?: string) => messageBoxService.error(content, title),
  info: (content: string, title?: string) => messageBoxService.info(content, title),
  success: (content: string, title?: string) => messageBoxService.success(content, title),
};

// 导出类型
export type { MessageBoxInstance };
