# UI Components 规格说明

## ADDED Requirements

### Requirement: Button 按钮组件

系统 SHALL 提供 Button 组件，支持多种变体。

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

### Requirement: Input 输入框组件

系统 SHALL 提供 Input 组件，支持多种状态。

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

### Requirement: Select 下拉选择组件

系统 SHALL 提供 Select 组件，支持单选和多选。

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

### Requirement: Table 数据表格组件

系统 SHALL 提供 Table 组件，支持排序、分页。

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

### Requirement: Modal 对话框组件

系统 SHALL 提供 Modal 组件，支持多种尺寸。

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

### Requirement: Card 卡片组件

系统 SHALL 提供 Card 组件作为内容容器。

#### Scenario: 卡片样式

- **WHEN** Card 组件渲染完成
- **THEN** 系统 SHALL 显示：
  - 白底 `surface-raised`
  - 边框 `border`
  - 圆角 `radius-ui`
  - 阴影 `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08)`

### Requirement: Loading 加载组件

系统 SHALL 提供 Loading 组件显示加载状态。

#### Scenario: 加载动画

- **WHEN** Loading 组件显示
- **THEN** 系统 SHALL 显示：
  - 主色旋转动画
  - 可选加载文案

### Requirement: Form 表单组件

系统 SHALL 提供 Form 组件，支持校验。

#### Scenario: 表单校验

- **WHEN** 表单提交时
- **THEN** 系统 SHALL 校验所有字段并显示错误信息

#### Scenario: 表单布局

- **WHEN** 表单渲染完成
- **THEN** 系统 SHALL 支持水平和垂直两种布局
