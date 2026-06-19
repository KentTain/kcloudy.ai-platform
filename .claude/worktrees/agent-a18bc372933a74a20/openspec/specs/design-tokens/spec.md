# Design Tokens 规范

## Purpose

定义前端设计令牌系统，基于 Tailwind CSS v4 `@theme` 指令和 CSS 变量双轨制实现统一的视觉语言，兼容 shadcn-vue 主题系统。

## Requirements

### Requirement: 设计令牌定义

系统 SHALL 使用 Tailwind CSS v4 `@theme` 指令和 CSS 变量双轨制定义设计令牌，兼容 shadcn-vue 主题系统。

#### Scenario: shadcn-vue CSS 变量定义

- **WHEN** 开发者配置 shadcn-vue 主题
- **THEN** 系统 SHALL 在 `tokens.css` 中定义以下 CSS 变量：
  - `--background`: 页面背景色
  - `--foreground`: 默认文字色
  - `--primary`: 主色
  - `--primary-foreground`: 主色上的文字色
  - `--secondary`: 辅色
  - `--secondary-foreground`: 辅色上的文字色
  - `--destructive`: 危险色
  - `--destructive-foreground`: 危险色上的文字色
  - `--muted`: 弱化背景色
  - `--muted-foreground`: 弱化文字色
  - `--border`: 边框色
  - `--input`: 输入框边框色
  - `--ring`: 焦点环色
  - `--card`: 卡片背景色
  - `--card-foreground`: 卡片文字色
  - `--radius`: 默认圆角

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
  - 危险 `danger`: `#EF4444`
  - 一级文字 `text`: `#1F2937`
  - 二级文字 `text-muted`: `#6B7280`
  - 禁用 `text-disabled`: `#9CA3AF`
  - 边框 `border`: `#E5E7EB`
  - 边框强调 `border-primary`: `rgba(22, 119, 255, 0.35)`

#### Scenario: Tailwind @theme 令牌映射

- **WHEN** shadcn-vue CSS 变量定义完成
- **THEN** 系统 SHALL 在 `@theme` 块中将 CSS 变量映射为 Tailwind 色值：
  - `--color-background: var(--background)`
  - `--color-foreground: var(--foreground)`
  - `--color-primary: var(--primary)`
  - `--color-primary-foreground: var(--primary-foreground)`
  - `--color-secondary: var(--secondary)`
  - `--color-secondary-foreground: var(--secondary-foreground)`
  - `--color-destructive: var(--destructive)`
  - `--color-muted: var(--muted)`
  - `--color-muted-foreground: var(--muted-foreground)`
  - `--color-border: var(--border)`
  - `--color-input: var(--input)`
  - `--color-ring: var(--ring)`
  - `--color-card: var(--card)`
  - `--color-card-foreground: var(--card-foreground)`
  - `--radius-ui: var(--radius)`

#### Scenario: 颜色令牌值对齐

- **WHEN** 双轨制令牌定义完成
- **THEN** 系统 SHALL 确保 CSS 变量值与原有语义色值对齐：
  - `--background` = `#F5F7FA` (原 surface)
  - `--primary` = `#1677FF`
  - `--primary-foreground` = `#FFFFFF`
  - `--secondary` = `#FF5722`
  - `--destructive` = `#EF4444` (原 danger)
  - `--muted` = `#F5F7FA` (原 surface)
  - `--muted-foreground` = `#6B7280` (原 text-muted)
  - `--border` = `#E5E7EB`

#### Scenario: 字体令牌定义

- **WHEN** 开发者定义字体令牌
- **THEN** 系统 SHALL 提供以下字体配置：
  - UI 字体 `font-sans`: `Inter, PingFang SC, Microsoft YaHei, system-ui, sans-serif`
  - 数据/代码字体 `font-mono`: `JetBrains Mono, ui-monospace, monospace`

#### Scenario: 圆角令牌定义

- **WHEN** 开发者定义圆角令牌
- **THEN** 系统 SHALL 提供统一圆角配置：
  - `--radius` = `0.5rem` (即 8px)
  - UI 圆角 `radius-ui`: `6px`（保留原有定义）

### Requirement: 语义化 CSS 类名

系统 SHALL 基于设计令牌生成语义化 CSS 类名，供组件使用。

#### Scenario: 使用 shadcn-vue 语义色

- **WHEN** shadcn-vue 组件设置颜色
- **THEN** 系统 SHALL 支持以下类名：
  - `bg-background` - 页面背景
  - `bg-primary` - 主色背景
  - `bg-secondary` - 辅色背景
  - `bg-destructive` - 危险背景
  - `bg-muted` - 弱化背景
  - `bg-card` - 卡片背景
  - `text-foreground` - 默认文字
  - `text-primary-foreground` - 主色文字
  - `text-muted-foreground` - 弱化文字
  - `border-border` - 边框
  - `border-input` - 输入框边框

#### Scenario: 保留原有语义色类名

- **WHEN** 现有组件使用原有语义色类名
- **THEN** 系统 SHALL 继续支持以下类名：
  - `bg-surface` - 页面背景
  - `bg-surface-raised` - 卡片背景
  - `bg-primary-subtle` - 主色浅底
  - `text-text` - 一级文字
  - `text-text-muted` - 二级文字
  - `text-text-disabled` - 禁用文字

### Requirement: 主题扩展支持

系统 SHALL 预留 `data-theme` 属性支持主题切换。

#### Scenario: 浅色主题（默认）

- **WHEN** 页面加载时未设置 `data-theme`
- **THEN** 系统 SHALL 使用浅色主题令牌（CSS 变量默认值）

#### Scenario: 暗色主题扩展

- **WHEN** 页面设置 `data-theme="dark"`
- **THEN** 系统 SHALL 支持通过 `[data-theme="dark"]` 选择器覆盖 CSS 变量值（预留接口，暂不实现）