# Design Tokens 规格说明

## ADDED Requirements

### Requirement: 设计令牌定义

系统 SHALL 使用 Tailwind CSS v4 `@theme` 指令定义设计令牌，包括颜色、字体、间距、圆角等。

#### Scenario: 颜色令牌定义

- **WHEN** 开发者定义颜色令牌
- **THEN** 系统 SHALL 提供以下语义色：
  - 页面背景 `surface`: `#F5F7FA`
  - 抬升面 `surface-raised`: `#FFFFFF`
  - 浅蓝底 `primary-subtle`: `#E8F3FF`
  - 主色蔚蓝 `primary`: `#1677FF`
  - 主色悬停 `primary-hover`: `#0958D9`
  - 主色按下 `primary-active`: `#003EB3`
  - 辅色橙红 `secondary`: `#FF5722`
  - 辅色悬停 `secondary-hover`: `#E64A19`
  - 辅色浅底 `secondary-subtle`: `#FFF3E0`
  - 成功 `success`: `#10B981`
  - 警示 `danger`: `#EF4444`
  - 一级文字 `text`: `#1F2937`
  - 二级文字 `text-muted`: `#6B7280`
  - 禁用 `text-disabled`: `#9CA3AF`
  - 边框 `border`: `#E5E7EB`
  - 边框强调 `border-primary`: `rgba(22, 119, 255, 0.35)`

#### Scenario: 字体令牌定义

- **WHEN** 开发者定义字体令牌
- **THEN** 系统 SHALL 提供以下字体配置：
  - UI 字体 `font-sans`: `Inter, PingFang SC, Microsoft YaHei, system-ui, sans-serif`
  - 数据/代码字体 `font-mono`: `JetBrains Mono, ui-monospace, monospace`

#### Scenario: 圆角令牌定义

- **WHEN** 开发者定义圆角令牌
- **THEN** 系统 SHALL 提供统一圆角配置：
  - UI 圆角 `radius-ui`: `6px`

### Requirement: 语义化 CSS 类名

系统 SHALL 基于设计令牌生成语义化 CSS 类名，供组件使用。

#### Scenario: 使用语义化背景色

- **WHEN** 组件需要设置背景色
- **THEN** 系统 SHALL 支持以下类名：
  - `bg-surface` - 页面背景
  - `bg-surface-raised` - 卡片背景
  - `bg-primary` - 主色背景
  - `bg-primary-subtle` - 主色浅底
  - `bg-secondary` - 辅色背景
  - `bg-secondary-subtle` - 辅色浅底

#### Scenario: 使用语义化文字色

- **WHEN** 组件需要设置文字色
- **THEN** 系统 SHALL 支持以下类名：
  - `text-text` - 一级文字
  - `text-text-muted` - 二级文字
  - `text-text-disabled` - 禁用文字
  - `text-primary` - 主色文字
  - `text-secondary` - 辅色文字

### Requirement: 主题扩展支持

系统 SHALL 预留 `data-theme` 属性支持主题切换。

#### Scenario: 浅色主题（默认）

- **WHEN** 页面加载时未设置 `data-theme`
- **THEN** 系统 SHALL 使用浅色主题令牌

#### Scenario: 暗色主题扩展

- **WHEN** 页面设置 `data-theme="dark"`
- **THEN** 系统 SHALL 支持自定义暗色令牌覆盖（预留接口，暂不实现）
