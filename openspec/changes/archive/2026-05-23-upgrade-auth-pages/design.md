## Context

当前 LoginPage、ForbiddenPage、NotFoundPage 使用旧 CommonXxx 封装组件，视觉风格与已完成现代化的 AdminLayout 不一致。LoginPage 是居中单卡片布局，缺少品牌展示和表单校验。403/404 页各自独立风格未统一。

这些页面路由独立（不在 AdminLayout 壳内），改动隔离性好。

## Goals / Non-Goals

**Goals:**
- LoginPage 采用两列布局：左侧品牌展示区（渐变背景 + logo + 描述文字），右侧表单区
- 登录表单引入 vee-validate + zod schema 校验，替代手写 ref 验证
- 使用 shadcn Card/Input/FormField/FormItem/FormLabel/FormMessage 构建表单
- 403 和 404 页统一错误页视觉风格（居中布局 + 大号错误码 + 描述 + 操作按钮）
- 移除 3 个页面中对 CommonXxx 组件的依赖

**Non-Goals:**
- 不引入租户选择功能（kbhub 有但本项目暂不需要）
- 不引入 RSA 密码加密
- 不改变路由结构或认证流程
- 不重构 authStore 内部逻辑

## Decisions

### D1: 登录页布局 — 两列 vs 居中卡片

**选择：两列布局（`lg:grid lg:grid-cols-2`）**

参考 kbhub login.vue，左侧品牌区提供视觉吸引力，右侧表单区功能聚焦。移动端（< lg）回退为单列，仅显示表单区。

替代方案：保持居中卡片 — 视觉升级有限，与 kbhub 设计范式脱节。

### D2: 表单校验 — vee-validate + zod vs 手写 ref

**选择：vee-validate + zod**

与 kbhub 统一校验范式，schema 可复用、错误消息自动管理、与 shadcn FormField 生态天然兼容。

替代方案：继续手写 ref 校验 — 代码量少但无 schema 复用能力，错误消息管理散乱。

### D3: shadcn Form 组件安装

项目当前缺少 shadcn `form` 组件包。需通过 `npx shadcn-vue@latest add form` 安装，该组件内置 vee-validate 集成（FormField/FormItem/FormLabel/FormControl/FormMessage）。

### D4: 错误页统一风格

403 和 404 共用同一布局模式（居中 + 大号错误码 + 描述 + Button 操作行），仅错误码数字和文案不同。不抽取共享组件——3 个页面文件量少，抽取过度设计。

## Risks / Trade-offs

- [shadcn form 组件未安装] → 安装前需确认 `npx shadcn-vue@latest add form` 在项目 pnpm 环境下正常工作
- [vee-validate/zod 新依赖] → 增加包体积，但 shadcn form 组件已内置依赖这些库
- [移动端回退] → 两列布局在 < lg 断点隐藏品牌区，需确认视觉过渡平滑