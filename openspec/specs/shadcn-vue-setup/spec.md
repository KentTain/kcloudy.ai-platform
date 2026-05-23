# shadcn-vue Setup 规范

## Purpose

定义 shadcn-vue 项目初始化配置和工具函数，为前端 UI 组件提供统一的基础设施。

## Requirements

### Requirement: shadcn-vue 项目初始化配置

系统 SHALL 通过 `npx shadcn-vue@latest init` 命令初始化 shadcn-vue，生成 `components.json` 配置文件。

#### Scenario: components.json 配置文件生成

- **WHEN** 执行 shadcn-vue 初始化命令
- **THEN** 系统 SHALL 在 `web/vue/` 目录下生成 `components.json`，包含以下配置：
  - `style`: "default"
  - `typescript`: true
  - `tailwind.config`: 对应 Tailwind CSS v4 配置路径
  - `framework`: "vue"
  - 组件输出目录: `src/components/ui/`
  - 工具文件路径: `src/lib/utils.ts`

### Requirement: cn 工具函数

系统 SHALL 提供 `cn` 工具函数用于合并 Tailwind CSS 类名，消除类名冲突。

#### Scenario: 类名合并

- **WHEN** 多个 Tailwind 类名传入 `cn` 函数
- **THEN** 系统 SHALL 使用 clsx + tailwind-merge 合并类名，相同功能的类名后者覆盖前者（如 `px-4 px-2` → `px-2`）

#### Scenario: 条件类名

- **WHEN** 条件表达式传入 `cn` 函数
- **THEN** 系统 SHALL 根据 clsx 规则处理条件类名（如 `cn("base", { active: true })` → `"base active"`）

### Requirement: shadcn-vue CLI 添加组件

系统 SHALL 支持通过 shadcn-vue CLI 命令添加 UI 原语组件到项目。

#### Scenario: 添加单个组件

- **WHEN** 执行 `npx shadcn-vue@latest add <component>` 命令
- **THEN** 系统 SHALL 将组件源码复制到 `src/components/ui/<component>.vue`
- **THEN** 组件 SHALL 自动导入所需依赖（reka-ui、@lucide/vue 等）

#### Scenario: 组件文件可定制

- **WHEN** shadcn-vue 组件文件存在于项目中
- **THEN** 开发者 SHALL 可以直接修改组件源码，不受 npm 包约束