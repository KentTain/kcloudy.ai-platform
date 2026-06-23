# E2E 测试目录指南

本文件为 Claude Code 在 Vue 前端 E2E 测试目录中工作时提供指导。

详细文档见 [tests/README.md](README.md)。

## 快速运行

```bash
# 运行所有 E2E 测试
pnpm test:e2e

# 运行特定模块
pnpm test:e2e tests/tenant/e2e/
pnpm test:e2e tests/iam/e2e/

# UI 模式
pnpm test:e2e:ui tests/iam/e2e/

# 测试覆盖缺失检测
pnpm test:coverage:check
```

## 测试结构

```
tests/
├── tenant/e2e/        # Tenant 管理端 E2E 测试
│   ├── fixtures.ts    # API 辅助登录
│   ├── data-helpers.ts # 测试数据管理
│   ├── login.spec.ts  # UI 登录测试
│   ├── smoke.spec.ts  # 冒烟测试
│   ├── tenants-crud.spec.ts   # 租户 CRUD
│   ├── resources-crud.spec.ts # 资源配置
│   └── modules-crud.spec.ts   # 模块 CRUD
├── iam/e2e/           # IAM 用户端 E2E 测试
│   ├── fixtures.ts    # IAM fixtures
│   ├── data-helpers.ts # IAM 数据管理
│   ├── smoke.spec.ts  # 冒烟测试
│   ├── users.spec.ts  # 用户 CRUD
│   ├── roles.spec.ts  # 角色 CRUD
│   ├── organizations.spec.ts # 组织 CRUD
│   ├── menus.spec.ts  # 菜单管理
│   └── permissions.spec.ts # 权限管理
├── test-results/      # 测试运行结果
└── playwright-report/ # HTML 报告
```

## 核心选择器策略

| 场景 | 选择器 |
|------|--------|
| CRUD 操作 | `page.getByTestId('xxx')` |
| 冒烟/文本 | `page.locator('text=xxx')` |

## data-testid 命名

使用 `kebab-case`，格式：`{功能}-{类型}`，如 `create-button`、`search-input`、`tab-database`。

## 单元测试

```bash
pnpm test:unit                    # 所有单元测试
pnpm test:unit tests/ai/unit/ --run  # 特定模块
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `E2E_BASE_URL` | `http://localhost:5173` | 前端地址 |
| `E2E_API_BASE` | `http://localhost:8080/api` | 后端 API |
