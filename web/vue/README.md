# InitProject Web Frontend (Vue)

InitProject AI 助手平台前端应用（Vue 版本），基于 Vue 3 + TypeScript + Vite 构建。

## 技术栈

- **框架**: Vue 3.5 + TypeScript 5.8
- **构建工具**: Vite 6.x
- **路由**: Vue Router 4.x
- **状态管理**: Pinia 3.x
- **样式**: Tailwind CSS v4
- **HTTP 客户端**: Axios
- **代码质量**: Biome
- **测试**: Vitest + @vue/test-utils

## 环境要求

- Node.js >= 22.0.0
- pnpm >= 10.0.0

## 开发命令

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 生产构建
pnpm build

# 预览生产构建
pnpm preview

# 类型检查
pnpm type-check

# 代码检查和格式化
pnpm check          # 检查
pnpm check:fix      # 检查并自动修复

# 测试
pnpm test:unit              # 运行测试（监听模式）
pnpm test:unit -- --run     # 运行一次
pnpm test:unit -- --coverage # 运行并生成覆盖率报告
```

## 项目结构

```text
src/
├── api/              # API 客户端
├── assets/           # 静态资源
├── components/       # 通用组件
│   └── ui/           # UI 基础组件
├── composables/      # 组合式函数
├── layouts/          # 布局组件
├── pages/            # 页面组件
├── router/           # 路由配置
├── stores/           # Pinia 状态管理
├── styles/           # 全局样式
├── types/            # TypeScript 类型定义
├── App.vue           # 根组件
└── main.ts           # 应用入口

tests/                # 单元测试
├── components/       # 组件测试
├── composables/      # Composable 测试
└── stores/           # Store 测试
```

## 开发说明

### API 代理

开发服务器配置了 API 代理，所有 `/api` 和 `/health` 请求会被转发到 `http://127.0.0.1:8000`。

确保后端服务在 8000 端口运行后，即可进行前后端联调。

### 路由配置

应用使用 Vue Router 4，路由配置位于 `src/router/index.ts`。支持以下路由：

- `/` - 首页
- `/datasets` - 知识库列表
- `/datasets/:id` - 知识库详情
- `/:pathMatch(.*)*` - 404 页面

### 状态管理

使用 Pinia 进行状态管理，Store 位于 `src/stores/` 目录。当前包含：

- `datasets` - 知识库列表状态

## 测试

项目使用 Vitest 进行单元测试，测试文件位于 `tests/` 目录。

### 测试文件组织

- 组件测试：`tests/components/`
- Store 测试：`tests/stores/`
- Composable 测试：`tests/composables/`

### 编写测试

```typescript
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import MyComponent from "@/components/MyComponent.vue";

describe("MyComponent", () => {
  it("renders correctly", () => {
    const wrapper = mount(MyComponent);
    expect(wrapper.text()).toContain("expected text");
  });
});
```

## 推荐的 IDE 设置

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)

## 推荐的浏览器扩展

- [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)

## License

Copyright © 2025 Moles. All Rights Reserved.
