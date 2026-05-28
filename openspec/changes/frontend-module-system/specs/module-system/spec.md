## 新增需求

### 需求:模块描述符接口

系统必须提供 ModuleDescriptor 接口，定义模块的标准契约。

ModuleDescriptor 必须包含以下必填字段：
- `name`: 模块名称（string）
- `version`: 模块版本（string）
- `getRoutes()`: 返回路由配置的方法

ModuleDescriptor 必须支持以下可选字段：
- `dependencies`: 依赖的其他模块名称数组
- `icon`: 模块图标
- `getMenuItems()`: 返回菜单项的方法
- `getStores()`: 返回 Pinia stores 的方法
- `setup()`: 模块初始化钩子

#### 场景:定义符合接口的模块
- **当** 创建一个包含 name、version、getRoutes() 的对象
- **那么** 该对象被识别为有效的 ModuleDescriptor

#### 场景:缺少必填字段
- **当** 创建一个缺少 name 字段的对象
- **那么** 类型检查必须报错

### 需求:模块注册中心

系统必须提供 ModuleRegistry 单例，支持模块的注册和查询。

ModuleRegistry 必须提供以下方法：
- `register(module)`: 注册模块
- `get(name)`: 根据名称获取模块
- `getAll()`: 获取所有已注册模块
- `has(name)`: 检查模块是否已注册

#### 场景:注册模块
- **当** 调用 `register(demoModule)`
- **那么** `has('demo')` 返回 true

#### 场景:获取已注册模块
- **当** 调用 `get('demo')`
- **那么** 返回 demoModule 对象

#### 场景:获取未注册模块
- **当** 调用 `get('nonexistent')`
- **那么** 返回 undefined

#### 场景:重复注册同名模块
- **当** 尝试注册同名模块
- **那么** 系统必须抛出错误并记录警告

### 需求:依赖解析

系统必须支持模块依赖声明和依赖解析。

依赖解析必须检测循环依赖，并在检测到循环依赖时抛出错误。

依赖解析必须按拓扑顺序返回模块列表，确保依赖模块先于依赖者初始化。

#### 场景:解析无依赖模块
- **当** 模块 A 无 dependencies
- **那么** A 直接加入初始化列表

#### 场景:解析有依赖模块
- **当** 模块 B 依赖模块 A
- **那么** 初始化顺序为 [A, B]

#### 场景:检测循环依赖
- **当** 模块 A 依赖 B，B 依赖 A
- **那么** 系统必须抛出 CyclicDependencyError

#### 场景:依赖未注册模块
- **当** 模块 A 依赖模块 X，但 X 未注册
- **那么** 系统必须抛出 ModuleNotFoundError

### 需求:模块加载器

系统必须提供 ModuleLoader，按依赖顺序加载和初始化模块。

ModuleLoader 必须按依赖拓扑顺序调用每个模块的 `setup()` 方法（如果存在）。

#### 场景:加载模块
- **当** 调用 `loadModules()`
- **那么** 所有已注册模块按依赖顺序初始化

#### 场景:模块初始化失败
- **当** 模块 A 的 `setup()` 抛出错误
- **那么** 系统必须记录错误并继续加载其他模块

### 需求:模块上下文

系统必须通过 Vue Provide/Inject 提供模块上下文。

模块上下文必须包含：
- `moduleRegistry`: 模块注册中心实例
- `eventBus`: 事件总线实例

#### 场景:组件访问模块注册中心
- **当** 组件内调用 `inject('moduleRegistry')`
- **那么** 返回 ModuleRegistry 实例

#### 场景:组件访问事件总线
- **当** 组件内调用 `inject('eventBus')`
- **那么** 返回事件总线实例
