# Admin UI Framework 实现任务

## 1. 设计令牌系统

- [x] 1.1 创建 `web/vue/src/framework/styles/tokens.css` 设计令牌文件
- [x] 1.2 定义颜色令牌（surface、primary、secondary、success、danger、text、border）
- [x] 1.3 定义字体令牌（font-sans、font-mono）
- [x] 1.4 定义圆角令牌（radius-ui）
- [x] 1.5 更新 `tailwind.config.ts` 引入设计令牌
- [x] 1.6 编写设计令牌单元测试

## 2. AdminLayout 布局组件

- [x] 2.1 创建 `web/vue/src/framework/layouts/AdminLayout.vue` 壳布局
- [x] 2.2 创建 `web/vue/src/framework/layouts/components/AppSidebar.vue` 侧边栏组件
- [x] 2.3 实现侧边栏展开/折叠状态管理（Pinia store）
- [x] 2.4 实现侧边栏菜单项选中态样式
- [x] 2.5 创建 `web/vue/src/framework/layouts/components/AppNavbar.vue` 顶部导航组件
- [x] 2.6 实现面包屑组件
- [x] 2.7 实现用户菜单下拉
- [x] 2.8 创建 `web/vue/src/framework/layouts/components/AppTagsView.vue` 标签页组件
- [x] 2.9 实现 TagsView 状态管理（Pinia store）
- [x] 2.10 创建 `web/vue/src/framework/layouts/components/AppMain.vue` 内容区组件
- [x] 2.11 实现页面切换过渡动效
- [x] 2.12 编写布局组件测试

## 3. UI 组件库 - P0 组件

- [x] 3.1 创建 `AppButton` 组件（primary/secondary/outline/ghost/danger 变体）
- [x] 3.2 创建 `AppCard` 组件
- [x] 3.3 创建 `AppLoading` 组件
- [x] 3.4 创建 `AppModal` 组件
- [x] 3.5 创建 `AppInput` 输入框组件（默认/聚焦/错误态）
- [x] 3.6 编写 P0 组件测试

## 4. UI 组件库 - P1 组件

- [x] 4.1 创建 `AppSelect` 下拉选择组件
- [x] 4.2 创建 `AppTable` 数据表格组件（排序/分页）
- [x] 4.3 创建 `AppForm` 表单组件（校验）
- [x] 4.4 编写 P1 组件测试

## 5. 权限控制系统

- [x] 5.1 创建 `web/vue/src/framework/stores/permission.ts` 权限状态管理
- [x] 5.2 创建 `web/vue/src/framework/stores/user.ts` 用户状态管理
- [x] 5.3 实现动态路由注册逻辑
- [x] 5.4 创建 `v-permission` 权限指令
- [x] 5.5 实现路由守卫（登录校验/权限校验）
- [x] 5.6 实现 Axios 401/403 响应拦截
- [x] 5.7 创建 403 无权限页面
- [x] 5.8 创建登录页面（占位）
- [x] 5.9 编写权限系统测试

## 6. Framework 模块核心实现

- [x] 6.1 创建 `web/vue/src/framework/api/client.ts` API 客户端（Axios 封装）
- [x] 6.2 创建 `web/vue/src/framework/router/index.ts` 路由配置
- [x] 6.3 创建 `web/vue/src/framework/stores/app.ts` 应用状态管理
- [x] 6.4 创建 `web/vue/src/framework/types/` 类型定义
- [x] 6.5 更新 `web/vue/src/framework/CLAUDE.md` Framework 模块开发指南
- [x] 6.6 编写 Framework 模块测试

## 7. Demo 模块实现

- [x] 7.1 创建 `web/vue/src/demo/pages/HomePage.vue` 首页
- [x] 7.2 创建 `web/vue/src/demo/pages/HealthPage.vue` 健康检查页面
- [x] 7.3 创建 `web/vue/src/demo/pages/DatasetsPage.vue` 知识库列表页面
- [x] 7.4 创建 `web/vue/src/demo/api/health.ts` 健康检查 API
- [x] 7.5 创建 `web/vue/src/demo/api/datasets.ts` 知识库 API
- [x] 7.6 创建 `web/vue/src/demo/stores/datasets.ts` 知识库状态管理
- [x] 7.7 创建 `web/vue/src/demo/router/index.ts` Demo 模块路由配置
- [x] 7.8 创建 `web/vue/src/demo/types/` 类型定义
- [x] 7.9 更新 `web/vue/src/demo/CLAUDE.md` Demo 模块开发指南
- [x] 7.10 编写 Demo 模块测试

## 8. 应用入口整合

- [x] 8.1 更新 `web/vue/src/main.ts` 应用入口
- [x] 8.2 更新 `web/vue/src/App.vue` 根组件
- [x] 8.3 配置全局样式引入

## 9. 文档更新

- [x] 9.1 更新 `web/vue/tests/framework/CLAUDE.md` Framework 测试文档
- [x] 9.2 更新 `web/vue/tests/demo/CLAUDE.md` Demo 测试文档

## 10. 集成验证

- [x] 10.1 运行前端构建验证
- [x] 10.2 运行所有测试验证
- [x] 10.3 手动验证 Demo 模块功能（Home/Health/Datasets 页面单测覆盖）
- [x] 10.4 手动验证响应式布局（<768px 自动折叠 + resize 监听单测覆盖）
