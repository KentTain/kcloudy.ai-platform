## 为什么

当前项目 E2E 测试覆盖率极低：Tenant 模块仅有基础导航测试，IAM 模块完全空白。随着功能迭代，手动回归测试成本持续上升，缺乏自动化保障导致潜在风险难以早期发现。根据需求文档 `docs/tests/使用playwright进行e2e测试需求.md`，需要为 Tenant 和 IAM 两个核心模块建立完整的 E2E 测试体系。

## 变更内容

### 新增

- **API 辅助登录机制**：通过后端接口获取 Token 并注入浏览器 localStorage，跳过 UI 登录流程，提升测试执行速度和稳定性
- **菜单驱动冒烟测试**：从 `/me` 接口动态获取菜单数据，自动遍历验证每个页面的可访问性和基础渲染
- **测试缺失检测脚本**：独立 Node 脚本，对比菜单与测试覆盖，生成缺失报告
- **Tenant 模块完整 CRUD 测试**：覆盖租户管理、资源配置（5个Tab）、模块管理
- **IAM 模块完整 CRUD 测试**：覆盖用户、角色、组织、菜单、权限管理
- **data-testid 属性注入**：为 CRUD 精细测试场景添加测试标识符

### 修改

- 重构 `tests/tenant/e2e/fixtures.ts`：从 UI 登录模式改为 API 辅助登录模式
- 更新 `playwright.config.ts`：调整超时和重试策略以适应大规模测试场景

## 功能 (Capabilities)

### 新增功能

- `e2e-auth-helpers`: API 辅助登录工具函数，支持 Tenant 管理端和 IAM 用户端两种认证场景
- `e2e-data-helpers`: 测试数据准备与清理工具函数，通过 API 创建/删除测试数据
- `e2e-smoke-testing`: 菜单驱动的冒烟测试框架，自动遍历可见菜单项验证页面可访问性
- `e2e-coverage-checker`: 独立脚本，检测测试覆盖缺失并生成报告文档
- `tenant-e2e-tests`: Tenant 模块完整 E2E 测试套件（冒烟 + CRUD）
- `iam-e2e-tests`: IAM 模块完整 E2E 测试套件（冒烟 + CRUD）

### 修改功能

无现有功能需求变更。

## 影响

### 代码影响

| 目录 | 影响说明 |
|------|---------|
| `web/vue/tests/tenant/e2e/` | 新增多个 spec 文件，重构 fixtures.ts |
| `web/vue/tests/iam/e2e/` | 新增完整测试套件 |
| `web/vue/scripts/` | 新增 e2e-check-coverage.ts |
| `web/vue/src/tenant/pages/` | 添加 data-testid 属性（CRUD 测试需要） |
| `web/vue/src/iam/pages/` | 添加 data-testid 属性（CRUD 测试需要） |

### 测试执行

- 新增测试用例数量：预计 70+ 个测试场景
- 预计执行时间：冒烟测试 < 30s，完整测试套件 < 5min（并行执行）

### 依赖项

- 现有依赖：`@playwright/test` 1.60.0（已安装）
- 新增依赖：无（使用 Node.js 原生模块实现缺失检测脚本）

### CI/CD 影响

- 可在 CI 流水线中新增 E2E 测试阶段
- 缺失检测脚本可作为 pre-commit hook 或独立 CI job 执行
