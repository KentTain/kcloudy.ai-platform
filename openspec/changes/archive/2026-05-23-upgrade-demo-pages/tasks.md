## 1. 依赖安装

- [x] 1.1 安装 shadcn badge 组件：`npx shadcn-vue@latest add badge`（如已在 Change #3 中安装则跳过）

## 2. HomePage 重写

- [x] 2.1 重写 HomePage.vue — 使用 AppPage 骨架（title="欢迎使用 AI 助手平台", variant="list"）
- [x] 2.2 将功能介绍区域从 CommonCard 内嵌列表 → shadcn Card/CardHeader/CardContent 的 grid 卡片组
- [x] 2.3 移除 HomePage 中对 CommonCard 的导入和引用

## 3. HealthPage 重写

- [x] 3.1 重写 HealthPage.vue — 使用 AppPage 骨架（title="健康检查", variant="list"）
- [x] 3.2 健康状态展示：shadcn Card + Badge（healthy → variant="success", unhealthy → variant="destructive"）
- [x] 3.3 加载态替换：CommonLoading → Skeleton 行级占位
- [x] 3.4 错误态重试按钮替换：CommonButton → shadcn Button
- [x] 3.5 移除 HealthPage 中对 CommonCard/CommonButton/CommonLoading 的导入和引用

## 4. DatasetsPage 重写

- [x] 4.1 重写 DatasetsPage.vue — 使用 AppPage 骨架（title="知识库列表", variant="list", actions slot 放 "新建知识库" shadcn Button）
- [x] 4.2 实现搜索筛选区：AppPage header 下方添加 shadcn Input 搜索框
- [x] 4.3 数据集列表从 CommonCard 内嵌列表 → shadcn Table（列：名称、描述、状态 Badge、创建时间、操作）
- [x] 4.4 加载态替换：CommonLoading → Skeleton 行级占位（TableRow 内 Skeleton）
- [x] 4.5 空态处理：TableEmpty 组件显示"暂无知识库"
- [x] 4.6 操作按钮替换：CommonButton → shadcn Button（查看/删除）
- [x] 4.7 移除 DatasetsPage 中对 CommonCard/CommonButton/CommonLoading 的导入和引用

## 5. 测试

- [x] 5.1 更新 HomePage 测试：验证 AppPage 骨架 + shadcn Card 渲染
- [x] 5.2 更新 HealthPage 测试：验证 Badge 状态标记 + Skeleton 加载态
- [x] 5.3 更新 DatasetsPage 测试：验证 shadcn Table 列渲染 + 搜索筛选 + 空态