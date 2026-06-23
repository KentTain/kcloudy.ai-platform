## 上下文

当前项目 E2E 测试基础设施薄弱，Tenant 模块仅有基础的导航测试（通过 UI 登录），IAM 模块完全空白。需求文档 `docs/tests/使用playwright进行e2e测试需求.md` 定义了完整的测试场景（~70 个），但缺乏系统化的实现框架。

**约束条件**：
- 前端 Vue 3 + TypeScript，测试框架 Playwright 1.60.0 已配置
- 后端 API 需要认证，Tenant 管理端使用 `admin_token`，IAM 用户端使用 `token` + `X-Tenant-Id`
- 测试执行环境为 Headless Chromium

**利益相关者**：
- 开发团队：需要快速反馈的测试套件
- CI/CD：需要稳定的自动化测试流水线

## 目标 / 非目标

**目标：**
- 建立 API 辅助登录机制，跳过 UI 登录流程，提升测试执行速度
- 实现菜单驱动的冒烟测试框架，自动发现未覆盖的页面
- 为 Tenant 和 IAM 核心模块建立完整的 CRUD 测试覆盖
- 提供测试覆盖缺失检测能力，生成可追踪的报告

**非目标：**
- 不覆盖 AI 模块的 E2E 测试（已有独立测试套件）
- 不实现"测试连接"等需要真实外部资源的场景
- 不引入额外的测试框架或依赖库

## 决策

### 决策 1：API 辅助登录 vs UI 登录

**选择**：API 辅助登录为主，保留 1-2 个 UI 登录测试

**理由**：
- API 登录耗时 ~0.5s，UI 登录耗时 ~3-5s
- 70+ 测试场景若每次都 UI 登录，光登录环节就占 3-6 分钟
- API 登录更稳定，不受 UI 变化影响

**替代方案**：
- 纯 UI 登录：太慢，不适合大规模测试
- 纯 API 登录：丢失登录页面的测试覆盖

### 决策 2：选择器策略

**选择**：冒烟测试用通用选择器，CRUD 测试用 `data-testid`

**理由**：
- 通用选择器（`text=租户管理`、`button:has-text("新建")`）可立即使用，无需修改源码
- `data-testid` 更稳定，适合精细的 CRUD 操作验证
- 分层策略平衡了快速覆盖与长期可维护性

**Token 存储机制**（从源码确认）：
```typescript
// Tenant 管理端
localStorage: {
  admin_token: string,
  admin_info: JSON string,
  admin_menus: JSON string,
  admin_permissions: JSON string,
  admin_role: string
}

// IAM 用户端
localStorage: {
  token: string,
  tenant_id: string,
  // ...
}
```

### 决策 3：测试文件组织

**选择**：按功能域拆分多个 spec 文件

**理由**：
- `fullyParallel: true` 配置下，多文件可并行执行
- 单文件失败不影响其他测试
- 资源配置 5 个 Tab 拆分为 5 个独立文件，职责清晰

**目录结构**：
```
tests/tenant/e2e/
  fixtures.ts                    # API 登录 + 数据 helper
  login.spec.ts                  # UI 登录测试（保留）
  smoke.spec.ts                  # 菜单驱动冒烟
  tenants-crud.spec.ts           # 租户 CRUD
  resources-database.spec.ts     # 数据库 Tab
  resources-storage.spec.ts      # 存储 Tab
  resources-cache.spec.ts        # 缓存 Tab
  resources-queue.spec.ts        # 队列 Tab
  resources-pubsub.spec.ts       # 发布订阅 Tab
  modules-crud.spec.ts           # 模块 CRUD
```

### 决策 4：测试数据管理

**选择**：独立准备 + API 清理

**实现模式**：
```typescript
test("新增租户", async ({ page, request }) => {
  const tenant = await createTenantViaAPI(request, token, {
    name: `e2e-test-${Date.now()}`,
    code: `e2e_${Date.now()}`
  });

  try {
    // 测试主体
  } finally {
    await deleteTenantViaAPI(request, token, tenant.id);
  }
});
```

**理由**：
- 每个测试独立，不依赖执行顺序
- API 清理比 UI 操作快 10 倍以上
- `finally` 块保证清理一定执行

### 决策 5：缺失检测实现方式

**选择**：独立 Node.js 脚本

**理由**：
- 不依赖 Playwright 环境，可独立运行
- 可集成到 pre-commit hook 或 CI job
- 使用 axios + glob + fs，无额外依赖

**输出格式**：
```
docs/tests/test-lose-item-{YYYY-MM-DD}.md
```

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|---------|
| API 登录绕过了登录页面的测试 | 保留独立的 `login.spec.ts` 验证 UI 登录流程 |
| `data-testid` 需要修改源码 | 先用通用选择器覆盖冒烟，CRUD 测试时逐步添加 |
| 测试数据残留（清理失败） | 命名使用 `e2e-{timestamp}` 前缀，易于识别和手动清理 |
| 菜单结构变化导致冒烟测试失效 | 缺失检测脚本会自动发现差异，生成报告提醒更新 |
| Headless 模式下某些动画/交互可能行为不同 | 测试中避免依赖动画时序，使用 `waitForSelector` 等待状态 |

## 实现路线

```
Phase 1: 基础设施（1-2 天）
───────────────────────────
  □ fixtures.ts 重构
  □ 缺失检测脚本

Phase 2: Tenant 冒烟（0.5 天）
───────────────────────────
  □ smoke.spec.ts

Phase 3: Tenant CRUD（2-3 天）
───────────────────────────
  □ tenants-crud.spec.ts
  □ resources-*.spec.ts (5个)
  □ modules-crud.spec.ts

Phase 4: IAM 模块（1-2 天）
───────────────────────────
  □ 同样模式重复
```

## 开放问题

- [ ] 是否需要为测试数据创建专用的测试租户/用户？
- [ ] CI 环境下的测试数据库初始化策略？
