# 测试目录指南

本文件为 Claude Code 在 Vue 前端测试目录中工作时提供指导。

## 测试目录结构

```text
tests/
├── components/            # 通用组件测试
│   ├── unit/              # 单元测试
│   └── e2e/               # E2E 端到端测试
├── framework/             # Framework 模块测试
│   ├── unit/              # 单元测试
│   │   ├── components/    # 组件测试
│   │   ├── composables/   # Composable 测试
│   │   ├── events/        # 事件测试
│   │   ├── module/        # 模块系统测试
│   │   ├── stores/        # Store 测试
│   │   └── utils/         # 工具函数测试
│   └── e2e/               # E2E 端到端测试
├── iam/                   # IAM 模块测试
│   ├── unit/              # 单元测试
│   │   ├── api/           # API 测试
│   │   ├── components/    # 组件测试
│   │   └── stores/        # Store 测试
│   └── e2e/               # E2E 端到端测试
├── tenant/                # Tenant 模块测试
│   ├── unit/              # 单元测试
│   └── e2e/               # E2E 端到端测试
├── ai/                    # AI 模块测试
│   ├── unit/              # 单元测试
│   │   ├── components/    # 组件测试
│   │   ├── composables/   # Composable 测试
│   │   ├── pages/         # 页面测试
│   │   └── stores/        # Store 测试
│   └── e2e/               # E2E 端到端测试
├── demo/                  # Demo 模块测试
│   ├── unit/              # 单元测试
│   └── e2e/               # E2E 端到端测试
├── test-results/          # E2E 测试运行结果（所有模块共享）
└── playwright-report/     # E2E HTML 测试报告（所有模块共享）
```

## 运行测试

```bash
# 运行所有单元测试
pnpm test:unit

# 详细输出
pnpm test:unit -- --run

# 运行特定模块单元测试
pnpm test:unit tests/ai/unit/ --run
pnpm test:unit tests/iam/unit/ --run
pnpm test:unit tests/framework/unit/ --run
pnpm test:unit tests/demo/unit/ --run
pnpm test:unit tests/components/unit/ --run

# 生成覆盖率报告
pnpm test:unit -- --coverage

# 运行所有 E2E 测试
pnpm test:e2e

# 运行特定模块 E2E 测试
pnpm test:e2e tests/ai/e2e/

# 带界面运行 E2E 测试
pnpm test:e2e:ui tests/ai/e2e/
```

## 模块测试说明

### AI 模块测试

| 目录 | 说明 |
|------|------|
| unit/components/ | ModelSelector、ToolCallItem 组件测试 |
| unit/composables/ | useChat 组合式函数测试 |
| unit/pages/ | ConversationListPage 页面测试 |
| unit/stores/ | conversation Store 测试 |
| e2e/ | E2E 端到端测试（Playwright） |

#### E2E 测试

详见 [tests/ai/e2e/TEST_PLAN.md](ai/e2e/TEST_PLAN.md)。

### IAM 模块测试

| 目录 | 说明 |
|------|------|
| unit/api/ | auth、user、role、permission、organization API 测试 |
| unit/components/ | OrganizationTree、PermissionTree 组件测试 |
| unit/stores/ | auth、user、role、organization Store 测试 |

### Framework 模块测试

| 目录 | 说明 |
|------|------|
| unit/components/ | AppPage、AppNavbar、CommandPalette 等组件测试 |
| unit/composables/ | useMenuPermission 组合式函数测试 |
| unit/events/ | EventBus 事件系统测试 |
| unit/module/ | 模块注册、路由解析、动态路由测试 |
| unit/stores/ | app、menu、permission Store 测试 |
| unit/utils/ | tree 工具函数测试 |

### Components 测试

| 目录 | 说明 |
|------|------|
| unit/ | CommonCheckboxTree、CommonTree、CommonPagination 等通用组件测试 |

## 测试标记

| 标记 | 说明 |
|------|------|
| unit | 单元测试 |
| integration | 集成测试 |
| slow | 慢测试 |

## 常用 Fixtures

| Fixture | 说明 |
|---------|------|
| wrapper | Vue 组件包装器 |
| pinia | Pinia 测试实例 |
| router | Vue Router 测试实例 |
