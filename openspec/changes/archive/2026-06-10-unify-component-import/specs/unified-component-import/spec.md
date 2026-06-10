## ADDED Requirements

### 需求:统一组件入口必须提供单一导入路径

系统必须在 `@/components/index.ts` 提供统一的组件导入入口，开发者可以从单一位置导入所有常用组件。

#### 场景:从统一入口导入 common 组件

- **当** 开发者从 `@/components` 导入 Button、Input、Card、Select、Table、Tree、Loading、Modal、Pagination 组件
- **那么** 系统必须返回 `@/components/common/` 目录下的业务封装版本

#### 场景:从统一入口导入高频 ui 组件

- **当** 开发者从 `@/components` 导入 Badge、Skeleton、Label、Checkbox、Switch、Textarea、Dialog、Tabs、FormField、FormItem、FormLabel、FormControl、FormMessage 组件
- **那么** 系统必须返回 `@/components/ui/` 目录下的原始组件

#### 场景:导入统一入口不存在的低频组件

- **当** 开发者尝试从 `@/components` 导入 Sidebar、Breadcrumb、Avatar、DropdownMenu、ScrollArea、Collapsible、Separator、Accordion、HoverCard、Tooltip、Command、Popover、Progress、Spinner 组件
- **那么** 系统必须不返回该组件，开发者必须从 `@/components/ui/xxx` 单独导入

### 需求:同名组件必须优先使用 common 版本

系统必须确保同名组件在统一入口中优先导出 common 版本，覆盖 ui 版本。

#### 场景:Button 组件优先使用 common 版本

- **当** 开发者从 `@/components` 导入 Button 组件
- **那么** 系统必须返回 common/Button，该组件必须包含 loading、block、type 属性
- **并且** 组件必须支持 variant 映射（primary→default, danger→destructive）

#### 场景:Input 组件优先使用 common 版本

- **当** 开发者从 `@/components` 导入 Input 组件
- **那么** 系统必须返回 common/Input，该组件必须包含 clearable、error、size 属性
- **并且** 组件必须提供 prefix、suffix 插槽

#### 场景:Select 组件使用声明式 API

- **当** 开发者从 `@/components` 导入 Select 组件
- **那么** 系统必须返回 common/Select，该组件必须接受 options 数组属性
- **并且** 组件必须支持 clearable、placeholder、size 属性

#### 场景:Table 组件使用声明式 API

- **当** 开发者从 `@/components` 导入 Table 组件
- **那么** 系统必须返回 common/Table，该组件必须接受 columns、data 数组属性
- **并且** 组件必须支持 loading、stripe、border 属性

### 需求:Tree 组件必须不进入统一入口

系统必须不在统一入口中导出 Tree 组件，因为 common/Tree 与 ui/Tree 数据结构不兼容。

#### 场景:开发者需要展示树

- **当** 开发者需要简单的树形展示（click/toggle 事件）
- **那么** 开发者必须从 `@/components` 导入 Tree（返回 common/Tree）

#### 场景:开发者需要功能树

- **当** 开发者需要带 checkbox、cascade、异步加载的功能树
- **那么** 开发者必须从 `@/components/ui/tree` 显式导入 Tree 和 TreeNodeType 类型

### 需求:统一入口必须导出类型定义

系统必须在统一入口中导出所有 common 组件的类型定义。

#### 场景:导入 TreeSelectProps 类型

- **当** 开发者从 `@/components` 导入 TreeSelectProps 类型
- **那么** 系统必须返回该类型定义

#### 场景:导入 DescriptionItem 类型

- **当** 开发者从 `@/components` 导入 DescriptionItem 类型
- **那么** 系统必须返回该类型定义

#### 场景:导入 DataTableState 类型

- **当** 开发者从 `@/components` 导入 DataTableState 类型
- **那么** 系统必须返回该类型定义

#### 场景:导入 MessageBox 相关类型

- **当** 开发者从 `@/components` 导入 MessageBoxOptions、MessageBoxType、MessageBoxAction、BeforeCloseCallback 类型
- **那么** 系统必须返回这些类型定义

### 需求:原有导入路径必须保持兼容

系统必须保持原有 `@/components/ui/xxx` 和 `@/components/common` 导入路径可用。

#### 场景:从 ui 路径导入组件

- **当** 开发者从 `@/components/ui/button` 导入 Button
- **那么** 系统必须返回 ui 版本的 Button 组件（不受统一入口影响）

#### 场景:从 common 路径导入组件

- **当** 开发者从 `@/components/common` 导入 Button
- **那么** 系统必须返回 common 版本的 Button 组件（不受统一入口影响）

### 需求:组件查找优先级必须文档化

CLAUDE.md 必须明确记录组件查找优先级，约束 Claude 和开发者的组件选择行为。

#### 场景:Claude 选择组件

- **当** Claude 需要在业务页面中使用组件
- **那么** Claude 必须优先从 `@/components` 统一入口导入
- **并且** 仅当统一入口不包含该组件时，才从 `@/components/ui/xxx` 导入

#### 场景:开发者查看文档

- **当** 开发者查看 `web/vue/src/CLAUDE.md` 文档
- **那么** 文档必须包含"组件导入规范"章节
- **并且** 章节必须列出统一入口组件清单和低频组件清单
