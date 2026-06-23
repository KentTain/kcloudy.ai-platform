# 测试目录指南

本文件为 Claude Code 在 Vue 前端测试目录中工作时提供指导。

详细 E2E 测试文档见 [tests/README.md](README.md)。

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
│       ├── fixtures.ts        # IAM 用户端测试 fixtures
│       ├── data-helpers.ts    # 测试数据管理辅助函数
│       ├── smoke.spec.ts      # 冒烟测试
│       ├── users.spec.ts      # 用户管理 CRUD 测试
│       ├── roles.spec.ts      # 角色管理 CRUD 测试
│       ├── organizations.spec.ts  # 组织管理 CRUD 测试
│       ├── menus.spec.ts      # 菜单管理测试
│       └── permissions.spec.ts    # 权限管理测试
├── tenant/                # Tenant 模块测试
│   ├── unit/              # 单元测试
│   └── e2e/               # E2E 端到端测试
│       ├── fixtures.ts        # Tenant 管理端测试 fixtures
│       ├── data-helpers.ts    # 测试数据管理辅助函数
│       ├── login.spec.ts      # 管理员 UI 登录测试
│       ├── smoke.spec.ts      # 冒烟测试
│       ├── tenants-crud.spec.ts   # 租户管理 CRUD 测试
│       ├── resources-crud.spec.ts # 资源配置管理测试
│       └── modules-crud.spec.ts   # 模块管理 CRUD 测试
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
pnpm test:unit tests/tenant/unit/ --run

# 生成覆盖率报告
pnpm test:unit -- --coverage

# 运行所有 E2E 测试
pnpm test:e2e

# 运行特定模块 E2E 测试
pnpm test:e2e tests/ai/e2e/
pnpm test:e2e tests/tenant/e2e/
pnpm test:e2e tests/iam/e2e/

# 带界面运行 E2E 测试
pnpm test:e2e:ui tests/iam/e2e/

# 运行测试覆盖缺失检测
pnpm test:coverage:check
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
| e2e/ | E2E 端到端测试（用户、角色、组织、菜单、权限管理） |

### Tenant 模块测试

| 目录 | 说明 |
|------|------|
| e2e/fixtures.ts | Tenant 管理端测试 fixtures，包含 API 辅助登录 |
| e2e/data-helpers.ts | 测试数据管理辅助函数 |
| e2e/login.spec.ts | 管理员 UI 登录测试 |
| e2e/smoke.spec.ts | 菜单驱动冒烟测试 |
| e2e/tenants-crud.spec.ts | 租户管理 CRUD 测试 |
| e2e/resources-crud.spec.ts | 资源配置管理测试（数据库/存储/缓存/队列/发布订阅） |
| e2e/modules-crud.spec.ts | 模块管理 CRUD 测试 |

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

## E2E 测试核心设计

### API 辅助登录

E2E 测试使用 API 辅助登录绕过 UI 登录流程，提升测试执行速度：

```typescript
import { adminLoginViaAPI, userLoginViaAPI } from './fixtures';

// Tenant 管理端登录
await adminLoginViaAPI(page, request, 'admin', 'admin123');

// IAM 用户端登录
await userLoginViaAPI(page, request, 'admin', 'admin123');
```

### 测试数据管理

测试数据使用 `e2e-` 前缀标记，支持自动清理：

```typescript
import { createTenantViaAPI, deleteTenantViaAPI, cleanupAllE2EData } from './data-helpers';

const tenant = await createTenantViaAPI(request, token);
await deleteTenantViaAPI(request, token, tenant.id);
await cleanupAllE2EData(request, token);
```

### 选择器策略

| 场景 | 选择器 | 示例 |
|------|--------|------|
| CRUD 操作 | `data-testid` | `page.getByTestId('create-button')` |
| 冒烟/文本匹配 | 通用选择器 | `page.locator('text=租户管理')` |

**data-testid 命名**：使用 `kebab-case`，如 `create-button`、`search-input`、`tab-database`。

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
