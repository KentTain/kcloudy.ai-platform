# E2E 测试运行指南

本文件为 Vue 前端 E2E 测试提供详细的使用指南和开发规范。

## 快速开始

```bash
# 运行所有 E2E 测试
pnpm test:e2e

# 运行特定模块 E2E 测试
pnpm test:e2e tests/tenant/e2e/
pnpm test:e2e tests/iam/e2e/

# 带界面运行
pnpm test:e2e:ui tests/iam/e2e/

# 生成测试覆盖缺失报告
pnpm test:coverage:check
```

## 测试目录结构

```
tests/
├── tenant/e2e/
│   ├── fixtures.ts              # Tenant 管理端测试 fixtures（API 辅助登录）
│   ├── data-helpers.ts          # 测试数据管理辅助函数
│   ├── login.spec.ts            # 管理员 UI 登录测试（10 个测试）
│   ├── smoke.spec.ts            # 菜单驱动冒烟测试（13 个测试）
│   ├── tenants-crud.spec.ts     # 租户管理 CRUD 测试（21 个测试）
│   ├── resources-crud.spec.ts   # 资源配置管理测试（~25 个测试）
│   └── modules-crud.spec.ts     # 模块管理 CRUD 测试（27 个测试）
├── iam/e2e/
│   ├── fixtures.ts              # IAM 用户端测试 fixtures
│   ├── data-helpers.ts          # IAM 测试数据管理辅助函数
│   ├── smoke.spec.ts            # 菜单驱动冒烟测试
│   ├── users.spec.ts            # 用户管理 CRUD 测试
│   ├── roles.spec.ts            # 角色管理 CRUD 测试（40 个测试）
│   ├── organizations.spec.ts    # 组织管理 CRUD 测试（20 个测试）
│   ├── menus.spec.ts            # 菜单管理测试（8 个测试）
│   └── permissions.spec.ts      # 权限管理测试（14 个测试）
├── test-results/                # 测试运行结果（所有模块共享）
└── playwright-report/           # HTML 测试报告
```

## 核心设计

### API 辅助登录

E2E 测试使用 API 辅助登录绕过 UI 登录流程，提升测试执行速度和稳定性：

```typescript
import { adminLoginViaAPI, userLoginViaAPI } from './fixtures';

// Tenant 管理端登录
test('示例', async ({ page, request }) => {
  await adminLoginViaAPI(page, request, 'admin', 'admin123');
  // 后续操作...
});

// IAM 用户端登录
test('示例', async ({ page, request }) => {
  await userLoginViaAPI(page, request, 'admin', 'admin123');
  // 后续操作...
});
```

**Token 存储常量**（与前端源码一致）：

| 常量 | localStorage Key | 说明 |
|------|-----------------|------|
| `ADMIN_TOKEN_KEY` | `admin_token` | 管理员认证 Token |
| `ADMIN_INFO_KEY` | `admin_info` | 管理员完整信息 |
| `ADMIN_ROLE_KEY` | `admin_role` | 管理员角色 |
| `ADMIN_PERMISSIONS_KEY` | `admin_permissions` | 管理员权限列表 |
| `ADMIN_MENUS_KEY` | `admin_menus` | 管理员菜单数据 |
| `TOKEN_KEY` | `token` | IAM 用户 Token |
| `TENANT_ID_KEY` | `tenant_id` | 当前租户 ID |

### 测试数据管理

每个测试独立准备数据，使用 `e2e-` 前缀标记，支持自动清理：

```typescript
import { createTenantViaAPI, deleteTenantViaAPI, cleanupAllE2EData } from './data-helpers';

test('创建租户', async ({ page, request }) => {
  const token = await adminLoginViaAPI(page, request);
  let tenantId: string;

  try {
    const tenant = await createTenantViaAPI(request, token, {
      name: 'e2e-test-租户',
      code: 'e2e_test_tenant'
    });
    tenantId = tenant.id;
    // 测试主体...
  } finally {
    if (tenantId) {
      await deleteTenantViaAPI(request, token, tenantId);
    }
  }
});

// 批量清理
test.afterAll(async ({ request }) => {
  const token = await getAdminToken(request);
  await cleanupAllE2EData(request, token);
});
```

### 选择器策略

| 场景 | 选择器 | 示例 |
|------|--------|------|
| CRUD 精确操作 | `data-testid` | `page.getByTestId('create-button')` |
| 冒烟文本匹配 | 通用选择器 | `page.locator('text=租户管理')` |
| 动态元素 | `data-testid` + 参数 | `page.getByTestId('tab-database')` |

**data-testid 命名规范**：使用 `kebab-case`，格式为 `功能-类型`：
- `create-button`, `save-button`, `cancel-button`
- `search-input`, `search-status`
- `tab-database`, `tab-storage`, `tab-cache`
- `stats-total`, `stats-total-value`

### 测试文件组织原则

1. **按功能域拆分**：每个 spec 文件对应一个功能域
2. **并行执行**：`fullyParallel: true` 配置下多文件可并行
3. **独立数据**：每个测试独立准备和清理数据
4. **辅助函数复用**：fixtures 和 data-helpers 作为共享模块

## 环境配置

### Playwright 配置

配置文件：`playwright.config.ts`

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `testDir` | `./tests` | 测试文件目录 |
| `testMatch` | `**/e2e/*.spec.ts` | 只匹配 e2e 目录下的测试 |
| `fullyParallel` | `true` | 并行执行 |
| `retries` | `0`（本地）/ `2`（CI） | 失败重试次数 |
| `timeout` | `60000` | 单个测试超时 |
| `baseURL` | `http://localhost:5173` | 默认基础 URL |

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `E2E_API_BASE` | `http://localhost:8080/api` | 缺失检测脚本 API 地址 |
| `E2E_BASE_URL` | `http://localhost:5173` | Playwright 测试基础 URL |
| `CI` | - | CI 环境标识 |

### 后端依赖

E2E 测试需要后端 API 服务运行：

```bash
# 启动后端服务（Python 示例）
cd server/python && uvicorn main:app --host 0.0.0.0 --port 8000

# 或使用 Docker
docker-compose up
```

## 运行命令

```bash
# 运行所有 E2E 测试
pnpm test:e2e

# 运行 Tenant 模块 E2E 测试
pnpm test:e2e tests/tenant/e2e/

# 运行 IAM 模块 E2E 测试
pnpm test:e2e tests/iam/e2e/

# 运行 AI 模块 E2E 测试
pnpm test:e2e tests/ai/e2e/

# 带界面运行
pnpm test:e2e:ui tests/iam/e2e/

# 调试模式
pnpm test:e2e tests/tenant/e2e/ --debug

# 只运行失败的测试
pnpm test:e2e --last-failed

# 运行所有单元测试
pnpm test:unit

# 特定模块单元测试
pnpm test:unit tests/iam/unit/ --run
pnpm test:unit tests/tenant/unit/ --run

# 生成覆盖率报告
pnpm test:unit -- --coverage

# 测试覆盖缺失检测
pnpm test:coverage:check
```

## 缺失检测脚本

运行 `pnpm test:coverage:check` 可自动检测测试覆盖缺失并生成报告。

**工作流程**：
1. 通过 API 登录获取 Token
2. 调用 `/me` 接口获取菜单数据
3. 扫描 `tests/**/*.spec.ts` 文件提取测试名称
4. 对比菜单与测试覆盖，生成缺失报告
5. 报告输出：`docs/tests/test-lose-item-{YYYY-MM-DD}.md`

**报告内容**：
- 菜单列表表格（含覆盖状态 ✅/⚠️/❌）
- 缺失测试清单（按菜单分组）
- 统计信息（总菜单数、已覆盖、未覆盖、部分覆盖、覆盖率）

## CI/CD 集成

```yaml
# GitHub Actions 示例
e2e-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: pnpm/action-setup@v2
    - run: pnpm install
    - run: pnpm test:e2e
      env:
        CI: true
```

## 开发规范

### 编写新测试

1. **确定测试文件位置**：`tests/{module}/e2e/xxx.spec.ts`
2. **使用 API 辅助登录**：导入 `fixtures.ts` 中的登录函数
3. **为页面添加 data-testid**：在 Vue 组件中添加 `data-testid="xxx"` 属性
4. **用 try-finally 管理数据**：确保测试数据被清理
5. **使用稳定选择器**：优先 `getByTestId()`，其次语义化选择器

### 提交规范

```
test(e2e): 新增 {模块} - {功能} E2E 测试

- 为 {组件}.vue 添加 data-testid 属性
- 创建 {xxx}.spec.ts 测试文件
- 实现 {测试场景列表}
```

### 测试标记

| 标记 | 说明 |
|------|------|
| `@smoke` | 冒烟测试（快速验证） |
| `@slow` | 慢测试（需要较多时间） |
| `@crud` | CRUD 操作测试 |
| `@auth` | 认证相关测试 |
