// Module System - 前端模块系统
// 提供模块描述符接口、类型守卫和注册中心

export { isModuleDescriptor, type MenuItem, type ModuleDescriptor } from "./types";
export { ModuleRegistry } from "./registry";
export {
  setupFramework,
  getModuleRegistry,
  getEventBus,
  isDynamicRoutesReady,
  type SetupFrameworkOptions,
} from "./setup";
export { EventBus, ModuleEvents } from "@/framework/events";
