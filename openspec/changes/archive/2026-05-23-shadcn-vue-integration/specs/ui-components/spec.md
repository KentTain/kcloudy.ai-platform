## MODIFIED Requirements

### Requirement: Button 按钮组件

系统 SHALL 提供 Button 组件，基于 shadcn-vue Button 原语封装，支持多种变体和业务扩展。

#### Scenario: 主按钮样式

- **WHEN** 按钮变体为 `primary`
- **THEN** 系统 SHALL 显示：
  - 背景色 `primary`
  - 文字白色
  - 悬停背景 `primary-hover`
  - 禁用时降低透明度

#### Scenario: 强调按钮样式

- **WHEN** 按钮变体为 `secondary`
- **THEN** 系统 SHALL 显示：
  - 背景色 `secondary`
  - 文字白色
  - 悬停背景 `secondary-hover`

#### Scenario: 次按钮样式

- **WHEN** 按钮变体为 `outline`
- **THEN** 系统 SHALL 显示：
  - 白底 + `primary` 1px 描边
  - 文字 `primary`
  - 悬停背景 `primary-subtle`

#### Scenario: 幽灵按钮样式

- **WHEN** 按钮变体为 `ghost`
- **THEN** 系统 SHALL 显示：
  - 透明底
  - 文字 `text-muted`
  - 悬停文字变 `primary`

#### Scenario: 危险按钮样式

- **WHEN** 按钮变体为 `danger`
- **THEN** 系统 SHALL 显示：
  - 背景色 `danger`
  - 文字白色

#### Scenario: 加载状态

- **WHEN** 按钮 `loading` 属性为 true
- **THEN** 系统 SHALL 显示旋转 Spinner 替代按钮文字
- **THEN** 按钮 SHALL 禁用交互

#### Scenario: 全宽模式

- **WHEN** 按钮 `block` 属性为 true
- **THEN** 系统 SHALL 按钮宽度撑满父容器

### Requirement: Input 输入框组件

系统 SHALL 提供 Input 组件，基于 shadcn-vue Input 原语封装，支持多种状态和业务扩展。

#### Scenario: 默认状态

- **WHEN** 输入框处于默认状态
- **THEN** 系统 SHALL 显示：
  - 白底 `#FFFFFF`
  - 1px 边框 `border`
  - 圆角 6px

#### Scenario: 聚焦状态

- **WHEN** 输入框获得焦点
- **THEN** 系统 SHALL 显示：
  - 边框颜色 `primary`
  - 外圈阴影 `box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.15)`

#### Scenario: 错误状态

- **WHEN** 输入框校验失败
- **THEN** 系统 SHALL 显示：
  - 边框颜色 `danger`
  - 下方显示错误文案

#### Scenario: 占位符样式

- **WHEN** 输入框显示占位符
- **THEN** 系统 SHALL 使用：
  - 颜色 `text-disabled`
  - 字体 `font-sans`

#### Scenario: 可清除

- **WHEN** 输入框 `clearable` 属性为 true 且有值
- **THEN** 系统 SHALL 在输入框右侧显示清除图标
- **THEN** 点击清除图标 SHALL 清空输入值

#### Scenario: 前缀/后缀插槽

- **WHEN** 输入框使用 `prefix` 或 `suffix` 插槽
- **THEN** 系统 SHALL 在输入框左侧或右侧显示插槽内容

### Requirement: Select 下拉选择组件

系统 SHALL 提供 Select 组件，基于 shadcn-vue Select 原语封装，支持键盘导航和可访问性。

#### Scenario: 触发器样式

- **WHEN** Select 组件渲染完成
- **THEN** 系统 SHALL 显示：
  - 同 Input 样式
  - 右侧 Chevron 图标，颜色 `text-muted`

#### Scenario: 下拉面板样式

- **WHEN** 下拉面板展开
- **THEN** 系统 SHALL 显示：
  - 白底 + 边框 + `shadow-lg`
  - 选项悬停背景 `primary-subtle`
  - 选中项文字 `primary` 加粗

#### Scenario: 键盘导航

- **WHEN** 下拉面板展开
- **THEN** 系统 SHALL 支持上下方向键选择选项
- **THEN** Enter 键 SHALL 确认选择
- **THEN** Escape 键 SHALL 关闭面板

#### Scenario: 可清除

- **WHEN** Select `clearable` 属性为 true 且有选中值
- **THEN** 系统 SHALL 显示清除按钮
- **THEN** 点击清除按钮 SHALL 清空选中值

### Requirement: Table 数据表格组件

系统 SHALL 提供 Table 组件，基于 shadcn-vue Table 原语封装，支持排序和分页。

#### Scenario: 表格行悬停

- **WHEN** 鼠标悬停表格行
- **THEN** 系统 SHALL 显示：
  - 行背景 `surface`
  - 左侧 3px `primary` 指示条

#### Scenario: 排序功能

- **WHEN** 用户点击可排序列头
- **THEN** 系统 SHALL 切换升序/降序

#### Scenario: 分页功能

- **WHEN** 数据量超过每页条数
- **THEN** 系统 SHALL 显示分页器

#### Scenario: 空数据状态

- **WHEN** 表格数据为空
- **THEN** 系统 SHALL 显示空数据提示文案

### Requirement: Modal 对话框组件

系统 SHALL 提供 Modal 组件，基于 shadcn-vue Dialog 原语封装，支持可访问性。

#### Scenario: 对话框样式

- **WHEN** 对话框打开
- **THEN** 系统 SHALL 显示：
  - 居中显示
  - 白底 `surface-raised`
  - 圆角 8px
  - 遮罩层半透明黑色

#### Scenario: 关闭对话框

- **WHEN** 用户点击遮罩层或关闭按钮
- **THEN** 系统 SHALL 关闭对话框

#### Scenario: 键盘关闭

- **WHEN** 用户按 Escape 键
- **THEN** 系统 SHALL 关闭对话框

#### Scenario: 焦点锁定

- **WHEN** 对话框打开
- **THEN** 系统 SHALL 将焦点锁定在对话框内部
- **THEN** Tab 键 SHALL 仅在对话框元素间循环

### Requirement: Card 卡片组件

系统 SHALL 提供 Card 组件，基于 shadcn-vue Card 原语封装。

#### Scenario: 卡片样式

- **WHEN** Card 组件渲染完成
- **THEN** 系统 SHALL 显示：
  - 白底 `surface-raised`
  - 边框 `border`
  - 圆角 `radius-ui`
  - 阴影 `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08)`

#### Scenario: 卡片区块

- **WHEN** Card 使用 Header/Content/Footer 区块
- **THEN** 系统 SHALL 提供对应插槽区域

### Requirement: Loading 加载组件

系统 SHALL 提供 Loading 组件显示加载状态。此组件无 shadcn-vue 对应原语，保留手写实现。

#### Scenario: 加载动画

- **WHEN** Loading 组件显示
- **THEN** 系统 SHALL 显示：
  - 主色旋转动画
  - 可选加载文案

#### Scenario: 全屏遮罩

- **WHEN** Loading `fullscreen` 属性为 true
- **THEN** 系统 SHALL 显示全屏半透明遮罩层覆盖