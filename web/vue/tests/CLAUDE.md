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
│       ├── fixtures.ts        # IAM 用户端测试 fixtures
│       ├── data-helpers.ts    # IAM 测试数据管理辅助函数
│       ├── smoke.spec.ts      # 菜单驱动冒烟测试
│       ├── users.spec.ts      # 用户管理 CRUD 测试
│       ├── roles.spec.ts      # 角色管理 CRUD 测试
│       ├── organizations.spec.ts  # 组织管理 CRUD 测试
│       ├── menus.spec.ts      # 菜单管理测试
│       └── permissions.spec.ts    # 权限管理测试
├── tenant/                # Tenant 模块测试
│   ├── unit/              # 单元测试
│   └── e2e/               # E2E 端到端测试
│       ├── fixtures.ts        # Tenant 管理端测试 fixtures
│       ├── data-helpers.ts    # Tenant 测试数据管理辅助函数
│       ├── login.spec.ts      # 管理员 UI 登录测试
│       ├── smoke.spec.ts      # 菜单驱动冒烟测试
│       ├── tenants-crud.spec.ts   # 租户管理 CRUD 测试
│       ├── resources-crud.spec.ts # 资源配置管理测试
│       ├── modules-crud.spec.ts   # 模块管理 CRUD 测试
│       └── data-helpers.test.ts   # 数据辅助函数单元测试
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
pnpm test:e2e tests/tenant/e2e/
pnpm test:e2e tests/iam/e2e/
pnpm test:e2e tests/ai/e2e/

# 带界面运行 E2E 测试
pnpm test:e2e:ui tests/iam/e2e/

# 运行测试覆盖缺失检测
pnpm test:coverage:check
```

## E2E 测试设计

### API 辅助登录

E2E 测试使用 API 辅助登录绕过 UI 登录流程，提升测试执行速度：

- **Tenant 管理端**: `adminLoginViaAPI(page, request)` - 使用 admin_token
- **IAM 用户端**: `iamUserLogin(page, request)` - 使用 token + tenant_id

### 测试数据管理

所有 E2E 测试数据使用 `e2e-` 前缀标记，支持自动清理：

```typescript
// 创建测试数据
const tenant = await createTenantViaAPI(request, token, { name: 'e2e-test' });

// 清理测试数据
await cleanupAllE2EData(request, token);
```

### 选择器策略

E2E 测试优先使用 `data-testid` 属性定位元素：

```typescript
// 推荐
await page.getByTestId('create-button').click();

// 避免
await page.locator('button:has-text("新建")').click();
```

## 模块测试说明

### Tenant 模块测试

| 目录 | 说明 |
|------|------|
| e2e/fixtures.ts | Tenant 管理端测试 fixtures，包含 API 辅助登录 |
| e2e/data-helpers.ts | 测试数据管理辅助函数 |
| e2e/login.spec.ts | 管理员 UI 登录测试（保留少量 UI 测试） |
| e2e/smoke.spec.ts | 菜单驱动冒烟测试，遍历所有可见菜单 |
| e2e/tenants-crud.spec.ts | 租户管理完整 CRUD 测试 |
| e2e/resources-crud.spec.ts | 资源配置测试（数据库/存储/缓存/队列/发布订阅） |
| e2e/modules-crud.spec.ts | 模块管理完整 CRUD 测试 |

### IAM 模块测试

| 目录 | 说明 |
|------|------|
| e2e/fixtures.ts | IAM 用户端测试 fixtures |
| e2e/data-helpers.ts | IAM 测试数据管理辅助函数 |
| e2e/smoke.spec.ts | 菜单驱动冒烟测试 |
| e2e/users.spec.ts | 用户管理 CRUD 测试 |
| e2e/roles.spec.ts | 角色管理 CRUD 测试 |
| e2e/organizations.spec.ts | 组织管理 CRUD 测试 |
| e2e/menus.spec.ts | 菜单管理测试 |
| e2e/permissions.spec.ts | 权限管理测试 |

### AI 模块测试

| 目录 | 说明 |
|------|------|
| unit/components/ | ModelSelector、ToolCallItem 组件测试 |
| unit/composables/ | useChat 组合式函数测试 |
| unit/pages/ | ConversationListPage 页面测试 |
| unit/stores/ | conversation Store 测试 |
| e2e/ | E2E 端到端测试（Playwright） |

详见 [tests/ai/e2e/TEST_PLAN.md](ai/e2e/TEST_PLAN.md)。

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

## 测试覆盖检测

运行 `pnpm test:coverage:check` 生成测试覆盖缺失报告，报告位于 `docs/tests/test-lose-item-{date}.md`。
