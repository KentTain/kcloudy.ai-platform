## 新增需求

### 需求:事件总线基本功能

系统必须提供 EventBus 类，实现发布-订阅模式。

EventBus 必须提供以下方法：
- `on(event: string, handler: Function)`: 订阅事件，返回取消订阅函数
- `emit(event: string, payload?: any)`: 发布事件
- `off(event: string, handler: Function)`: 取消订阅

#### 场景:订阅并接收事件
- **当** 使用 on() 订阅事件后，emit() 发布该事件
- **那么** 订阅的回调函数被调用，接收 payload 参数

#### 场景:取消订阅
- **当** 调用 on() 返回的取消订阅函数
- **那么** 后续 emit() 不再触发该回调

#### 场景:多次订阅同一事件
- **当** 同一事件有多个订阅者
- **那么** emit() 时所有订阅者按注册顺序被调用

### 需求:预定义事件类型

系统必须提供 ModuleEvents 常量，定义标准事件类型。

ModuleEvents 必须包含以下事件：
- `USER_LOGGED_IN`: 用户登录成功
- `USER_LOGGED_OUT`: 用户登出
- `TENANT_CHANGED`: 租户切换
- `MODULE_LOADED`: 模块加载完成
- `MODULE_ERROR`: 模块加载错误
- `DATA_REFRESH_REQUESTED`: 数据刷新请求

#### 场景:使用预定义事件
- **当** 模块使用 ModuleEvents.USER_LOGGED_IN 订阅事件
- **那么** 用户登录后收到通知

### 需求:组件生命周期集成

事件订阅必须支持 Vue 组件生命周期。

使用 on() 返回的取消订阅函数，应在 onUnmounted 中调用。

#### 场景:组件卸载时取消订阅
- **当** 组件在 onMounted 中订阅事件
- **那么** 组件卸载时应调用取消订阅函数，避免内存泄漏

## 修改需求

无。

## 移除需求

无。
