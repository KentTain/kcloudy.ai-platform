# InitProject Web Frontend (Vue)

InitProject AI 助手平台前端应用（Vue 版本），基于 Vue 3 + TypeScript + Vite 构建。

## 技术栈

- **框架**: Vue 3.5 + TypeScript 5.8
- **构建工具**: Vite 6.x
- **路由**: Vue Router 4.x
- **状态管理**: Pinia 3.x
- **UI 组件库**: shadcn-vue
- **无样式原语**: Radix Vue
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
web/vue/
├── src/                       # 源码目录
│   ├── demo/                  # Demo 业务模块
│   ├── framework/             # Framework UI框架模块
│   ├── components/            # 通用组件
│   │   └── ui/                # shadcn-vue 组件
│   ├── composables/           # 组合式函数
│   ├── App.vue                # 根组件
│   └── main.ts                # 应用入口
├── tests/                     # 测试目录
│   ├── demo/                  # Demo 模块测试
│   └── framework/             # Framework 模块测试
├── public/                    # 静态文件
├── biome.jsonc                # Biome 配置
├── vite.config.ts             # Vite 配置
├── vitest.config.ts           # Vitest 测试配置
├── tsconfig.json              # TypeScript 配置
└── package.json               # 项目配置
```

## 开发说明

### API 代理

开发服务器配置了 API 代理，所有 `/api` 和 `/health` 请求会被转发到 `http://127.0.0.1:8000`。

确保后端服务在 8000 端口运行后，即可进行前后端联调。

## 测试

项目使用 Vitest 进行单元测试，测试文件位于 `tests/` 目录。

详细测试说明见 [tests/CLAUDE.md](tests/CLAUDE.md)。

## 开发指南

详细开发指南见 [CLAUDE.md](CLAUDE.md)。

## 推荐的 IDE 设置

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)

## License

Copyright © 2025 Moles. All Rights Reserved.
