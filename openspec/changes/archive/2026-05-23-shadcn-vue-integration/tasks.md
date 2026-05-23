## 1. 项目初始化

- [x] 1.1 运行 `pnpm install` 安装新增依赖（radix-vue、class-variance-authority、clsx、tailwind-merge、lucide-vue-next）
- [x] 1.2 运行 `npx shadcn-vue@latest init` 初始化 shadcn-vue，生成 `components.json` 配置文件
- [x] 1.3 创建 `src/lib/utils.ts`，实现 `cn` 函数（clsx + tailwind-merge）

## 2. 设计令牌双轨制

- [x] 2.1 在 `src/framework/styles/main.css` 中添加 shadcn-vue CSS 变量定义（--background、--primary、--foreground 等）
- [x] 2.2 在 `@theme` 块中添加 CSS 变量到 Tailwind 的映射（--color-background: var(--background) 等）
- [x] 2.3 确保原有语义色类名（bg-surface、text-text-muted 等）继续可用
- [x] 2.4 验证 shadcn-vue 组件样式与原有设计令牌视觉一致

## 3. 组件目录结构调整

- [x] 3.1 将 `src/components/ui/CommonButton.vue` 移至 `src/components/CommonButton.vue`
- [x] 3.2 将 `src/components/ui/CommonCard.vue` 移至 `src/components/CommonCard.vue`
- [x] 3.3 将 `src/components/ui/CommonInput.vue` 移至 `src/components/CommonInput.vue`
- [x] 3.4 将 `src/components/ui/CommonModal.vue` 移至 `src/components/CommonModal.vue`
- [x] 3.5 将 `src/components/ui/CommonSelect.vue` 移至 `src/components/CommonSelect.vue`
- [x] 3.6 将 `src/components/ui/CommonTable.vue` 移至 `src/components/CommonTable.vue`
- [x] 3.7 将 `src/components/ui/CommonLoading.vue` 移至 `src/components/CommonLoading.vue`
- [x] 3.8 更新所有业务模块中的组件导入路径（demo、framework、iam）

## 4. shadcn-vue 原语组件引入

- [x] 4.1 运行 `npx shadcn-vue@latest add button` 添加 Button 原语
- [x] 4.2 运行 `npx shadcn-vue@latest add dialog` 添加 Dialog 原语
- [x] 4.3 运行 `npx shadcn-vue@latest add input` 添加 Input 原语
- [x] 4.4 运行 `npx shadcn-vue@latest add select` 添加 Select 原语
- [x] 4.5 运行 `npx shadcn-vue@latest add table` 添加 Table 原语
- [x] 4.6 运行 `npx shadcn-vue@latest add card` 添加 Card 原语

## 5. Common 组件重构（基于 shadcn-vue 原语）

- [x] 5.1 重构 CommonButton：基于 shadcn-vue Button，扩展 loading/block 属性
- [x] 5.2 重构 CommonCard：基于 shadcn-vue Card，封装 shadow/padding 属性
- [x] 5.3 重构 CommonInput：基于 shadcn-vue Input，扩展 clearable/error/prefix/suffix
- [x] 5.4 重构 CommonModal：基于 shadcn-vue Dialog，封装 size/maskClosable
- [x] 5.5 重构 CommonSelect：基于 shadcn-vue Select，封装 options/clearable
- [x] 5.6 重构 CommonTable：基于 shadcn-vue Table，封装 columns/loading/empty
- [x] 5.7 CommonLoading 保留手写实现，调整为使用 CSS 变量令牌

## 6. 测试验证

- [x] 6.1 更新现有组件测试（导入路径变更）
- [x] 6.2 为每个重构后的 Common 组件编写功能验证测试
- [x] 6.3 验证 shadcn-vue 原语组件的可访问性（键盘导航、ARIA）
- [x] 6.4 验证设计令牌双轨制兼容性（视觉一致性检查）
- [x] 6.5 运行完整测试套件 `pnpm test:unit --run` 确认无回归
