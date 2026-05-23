## 1. 组件实现

- [x] 1.1 创建 `web/vue/src/framework/layouts/components/AppPage.vue`，实现页面骨架组件（title/eyebrow/description/actions slot/default slot/variant prop）
- [x] 1.2 实现 variant 计算属性，根据 list/workbench/detail/governance 返回对应背景色 class

## 2. 测试

- [x] 2.1 创建 `web/vue/tests/framework/components/app-page.test.ts`，测试 AppPage 各 prop 和 slot 渲染
- [x] 2.2 测试 variant 默认值为 list，各 variant 对应正确的背景色 class
- [x] 2.3 测试可选 prop（eyebrow、description）不传时不渲染对应元素
- [x] 2.4 测试 actions slot 不使用时不渲染操作区容器
- [x] 2.5 测试容器高度计算（h-[calc(100svh-3.5rem)]）和 overflow-auto

## 3. 文档更新

- [x] 3.1 更新 `web/vue/src/framework/CLAUDE.md`，在布局组件章节补充 AppPage 文档（Props/Slots/variant 说明）
- [x] 3.2 更新 `web/vue/src/CLAUDE.md`，在功能模块表格中补充 AppPage 说明