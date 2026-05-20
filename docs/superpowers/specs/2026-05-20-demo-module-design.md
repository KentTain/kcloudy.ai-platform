# Demo 模块设计规格

## 概述

在 `web/vue/src/demo/` 下实现测试示例模块，用于测试 API 连通性和 UI 组件交互。采用单路由 `/demo` + 标签页切换的交互方式。

## 文件结构

遵循 `web/vue/src/{模块}/` 规范：

```
src/demo/
├── pages/
│   └── DemoPage.vue          # 主页面，标签切换
├── components/
│   ├── ApiTestPanel.vue       # API 测试标签页
│   └── ComponentTestPanel.vue # 组件交互标签页
├── types/
│   └── index.ts              # demo 相关类型
└── composables/
    └── useApiTest.ts          # API 测试逻辑复用
```

路由变更：`src/router/index.ts` 添加 `/demo` → `DemoPage`。

## 标签页设计

三个标签页：**API 测试**、**组件交互**、**扩展预留**。

### API 测试标签

每个 API 端点一个卡片，点击按钮发起请求，展示响应结果。

| 测试项 | 端点 | 操作 |
|--------|------|------|
| 健康检查 | `GET /health` | 发送请求，显示状态 |
| 知识库列表 | `GET /v1/datasets` | 发送请求，显示 JSON |
| 创建知识库 | `POST /v1/datasets` | 表单输入，提交创建 |
| 删除知识库 | `DELETE /v1/datasets/:id` | 输入 ID，确认删除 |
| AI 对话 | `POST /v1/chat` | 占位卡片，显示"即将支持" |

每个卡片展示：请求状态（loading/success/error）、响应耗时、响应内容（JSON 格式化）。

`useApiTest` composable 封装请求状态管理：

```typescript
interface ApiTestResult {
  status: 'idle' | 'loading' | 'success' | 'error'
  data: unknown
  error: string | null
  duration: number | null
}
```

### 组件交互标签

| 测试项 | 组件 | 交互行为 |
|--------|------|----------|
| AppButton | 按钮组件 | 点击计数、variant 切换、disabled 状态 |
| AppCard | 卡片组件 | 有/无 title、内容切换 |
| AppModal | 弹窗组件 | 打开/关闭、表单提交 |
| AppLoading | 加载组件 | 尺寸切换 |

每个测试区展示组件当前状态和交互结果。

### 扩展预留标签

占位标签页，提示"更多测试功能开发中"，列出未来可添加的测试项：

- WebSocket 连接测试
- 流式响应（SSE）测试
- 文件上传测试
- 权限认证测试

## 技术约束

- 复用现有 `src/api/` 中的 API 函数和 `src/components/ui/` 中的 UI 组件
- 使用 Tailwind CSS 样式，与项目现有风格一致
- 组件使用 `<script setup lang="ts">` 语法
- 不引入新的依赖
