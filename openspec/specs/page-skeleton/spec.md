# page-skeleton Specification

## Purpose
TBD - created by archiving change framework-page-skeleton. Update Purpose after archive.
## Requirements
### Requirement: AppPage 页面骨架组件

系统 SHALL 提供 AppPage 组件作为所有业务页面的统一骨架，提供标题、描述、操作区等标准页面头部区域。

#### Scenario: 页面头部区域渲染

- **WHEN** 使用 AppPage 组件并传入 title、eyebrow、description
- **THEN** 系统 SHALL 渲染以下头部区域：
  - eyebrow 为小字标题上方提示文字，使用 `text-muted-foreground text-xs font-medium` 样式
  - title 为页面主标题，使用 `text-2xl font-semibold tracking-normal` 样式
  - description 为页面功能描述，使用 `text-muted-foreground max-w-3xl text-sm` 样式

#### Scenario: 操作区渲染

- **WHEN** 使用 AppPage 组件并在 actions slot 中传入内容
- **THEN** 系统 SHALL 在标题区域右侧渲染操作按钮区，使用 `flex shrink-0 flex-wrap items-center gap-2` 样式

#### Scenario: 页面内容区渲染

- **WHEN** 使用 AppPage 组件并在 default slot 中传入页面主体内容
- **THEN** 系统 SHALL 在头部区域下方渲染内容区，与头部区域间距为 `gap-5`

#### Scenario: 不传可选 prop

- **WHEN** 使用 AppPage 组件但不传入 eyebrow 或 description
- **THEN** 系统 SHALL 不渲染对应的元素（eyebrow 的 p 标签和 description 的 p 标签不显示）

#### Scenario: 不使用 actions slot

- **WHEN** 使用 AppPage 组件但不使用 actions slot
- **THEN** 系统 SHALL 不渲染操作区容器

### Requirement: AppPage 页面变体

系统 SHALL 支持 4 种页面变体，通过 variant prop 控制页面背景色与视觉风格。

#### Scenario: list 列表页变体

- **WHEN** AppPage variant 为 `list`（默认值）
- **THEN** 系统 SHALL 使用 `bg-background` 背景色，适用于数据列表页

#### Scenario: workbench 工作台变体

- **WHEN** AppPage variant 为 `workbench`
- **THEN** 系统 SHALL 使用 `bg-muted/20` 背景色，适用于沉浸式操作页面

#### Scenario: detail 详情页变体

- **WHEN** AppPage variant 为 `detail`
- **THEN** 系统 SHALL 使用 `bg-background` 背景色，适用于数据详情页

#### Scenario: governance 管理页变体

- **WHEN** AppPage variant 为 `governance`
- **THEN** 系统 SHALL 使用 `bg-background` 背景色，适用于系统管理页面

### Requirement: AppPage 容器高度

系统 SHALL 设置 AppPage 容器高度为视口高度减去 header 高度，确保页面内容区恰好填满可视区域。

#### Scenario: 桌面端容器高度

- **WHEN** 在桌面端浏览器中使用 AppPage
- **THEN** 系统 SHALL 设置容器高度为 `calc(100svh - 3.5rem)`，使用 `svh` 单位避免移动端地址栏影响

#### Scenario: 内容溢出滚动

- **WHEN** 页面内容超出容器高度
- **THEN** 系统 SHALL 在 AppPage 容器上启用 `overflow-auto`，允许内容滚动

### Requirement: AppPage 页面间距与布局

系统 SHALL 在 AppPage 内部提供统一的间距和布局。

#### Scenario: 页面内部间距

- **WHEN** AppPage 渲染完成
- **THEN** 系统 SHALL 在内容容器上使用 `mx-auto flex min-h-full w-full flex-col gap-5 p-4 md:p-6` 样式
  - 移动端 padding 4（1rem）
  - 桌面端 padding 6（1.5rem）
  - 各区域间距 gap-5（1.25rem）

#### Scenario: 头部区域布局

- **WHEN** AppPage 渲染头部区域
- **THEN** 系统 SHALL 使用 `flex flex-col gap-3 md:flex-row md:items-end md:justify-between` 样式
  - 移动端：标题和操作区垂直排列
  - 桌面端：标题左对齐，操作区右对齐

#### Scenario: 标题文字截断

- **WHEN** title 内容过长
- **THEN** 系统 SHALL 使用 `truncate` 类确保标题不超出容器宽度

