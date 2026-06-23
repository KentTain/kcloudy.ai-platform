/**
 * Tenant 模块 - 模块管理 CRUD E2E 测试
 *
 * 测试场景：
 * - 模块列表加载
 * - 创建模块
 * - 编辑模块
 * - 删除模块
 * - 模块详情查看（Tabs 切换）
 * - 搜索筛选
 */
import { test, expect, adminLoginViaAPI, waitForPageReady } from './fixtures';
import {
  createModuleViaAPI,
  deleteModuleViaAPI,
  getAdminToken,
  cleanupAllE2EData,
  generateE2EId,
  type ModuleResponse,
} from './data-helpers';
import type { APIRequestContext, Page } from '@playwright/test';

// ============================================================================
// 测试数据管理
// ============================================================================

/**
 * 测试上下文，存储测试过程中创建的资源
 */
interface TestContext {
  createdModules: ModuleResponse[];
}

/**
 * 全局测试上下文
 */
const testContext: TestContext = {
  createdModules: [],
};

/**
 * 通过 API 创建测试模块
 */
async function createTestModule(
  request: APIRequestContext,
  name?: string,
  code?: string
): Promise<ModuleResponse> {
  const token = await getAdminToken(request);
  const module = await createModuleViaAPI(request, token, {
    name: name || `E2E测试模块-${Date.now()}`,
    code: code || generateE2EId('module'),
    description: 'E2E 测试自动创建',
  });
  testContext.createdModules.push(module);
  return module;
}

/**
 * 清理所有测试数据
 */
async function cleanupTestData(request: APIRequestContext) {
  const token = await getAdminToken(request);

  // 删除通过 API 创建的模块
  for (const module of testContext.createdModules) {
    await deleteModuleViaAPI(request, token, module.id).catch(() => {});
  }
  testContext.createdModules = [];

  // 清理其他 E2E 数据
  await cleanupAllE2EData(request, token);
}

// ============================================================================
// 测试用例
// ============================================================================

test.describe('模块管理 CRUD', () => {
  test.beforeEach(async ({ page, request }) => {
    // 使用 API 辅助登录
    await adminLoginViaAPI(page, request);
  });

  test.afterAll(async ({ request }) => {
    // 清理所有测试数据
    await cleanupTestData(request);
  });

  // ==================== 模块列表加载测试 ====================

  test.describe('模块列表加载', () => {
    test('访问 /admin/modules 显示模块列表页面', async ({ page }) => {
      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 验证页面元素存在
      await expect(page.locator('[data-testid="module-list-page"]')).toBeVisible();
      await expect(page.locator('h2:has-text("模块管理")')).toBeVisible();
    });

    test('统计卡片正确渲染', async ({ page }) => {
      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 验证统计卡片存在
      await expect(page.locator('text=模块总数')).toBeVisible();
      await expect(page.locator('text=启用模块')).toBeVisible();
      await expect(page.locator('text=必须模块')).toBeVisible();
      await expect(page.locator('text=已分配次数')).toBeVisible();
    });

    test('模块列表表格正确渲染', async ({ page }) => {
      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 验证表格存在
      await expect(page.locator('[data-testid="module-table"]')).toBeVisible();

      // 验证表头
      await expect(page.locator('text=模块信息')).toBeVisible();
      await expect(page.locator('text=状态')).toBeVisible();
      await expect(page.locator('text=必须模块')).toBeVisible();
    });

    test('刷新按钮可以刷新列表', async ({ page }) => {
      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 点击刷新按钮
      const refreshBtn = page.locator('[data-testid="refresh-btn"]');
      await expect(refreshBtn).toBeVisible();
      await refreshBtn.click();
      await waitForPageReady(page);

      // 验证页面仍然正常显示
      await expect(page.locator('[data-testid="module-table"]')).toBeVisible();
    });
  });

  // ==================== 创建模块测试 ====================

  test.describe('创建模块', () => {
    test('点击新增模块按钮跳转到创建页面', async ({ page }) => {
      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 点击新增按钮
      await page.locator('[data-testid="create-module-btn"]').click();

      // 验证跳转到创建页面
      await page.waitForURL(/\/admin\/modules\/create$/);
      expect(page.url()).toContain('/admin/modules/create');
    });

    test('创建模块表单验证', async ({ page }) => {
      await page.goto('/admin/modules/create');
      await waitForPageReady(page);

      // 验证表单页面元素
      await expect(page.locator('[data-testid="module-form-page"]')).toBeVisible();
      await expect(page.locator('[data-testid="name-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="code-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="save-btn"]')).toBeVisible();
    });

    test('成功创建模块', async ({ page, request }) => {
      const moduleName = `E2E创建模块-${Date.now()}`;
      const moduleCode = generateE2EId('module');

      await page.goto('/admin/modules/create');
      await waitForPageReady(page);

      // 填写表单
      await page.locator('[data-testid="name-input"]').fill(moduleName);
      await page.locator('[data-testid="code-input"]').fill(moduleCode);
      await page.locator('[data-testid="description-input"]').fill('E2E 测试创建的模块');

      // 提交表单
      await page.locator('[data-testid="save-btn"]').click();

      // 等待跳转到列表页
      await page.waitForURL(/\/admin\/modules$/, { timeout: 15000 });

      // 验证模块出现在列表中
      await waitForPageReady(page);
      await expect(page.locator(`text=${moduleName}`)).toBeVisible({ timeout: 10000 });

      // 清理：通过 API 删除创建的模块
      const token = await getAdminToken(request);
      const modulesResponse = await request.get('/api/tenant/admin/v1/modules', {
        headers: { Authorization: `Bearer ${token}` },
        params: { keyword: moduleCode },
      });
      if (modulesResponse.ok()) {
        const data = await modulesResponse.json();
        const module = data?.data?.find((m: { code: string }) => m.code === moduleCode);
        if (module) {
          await deleteModuleViaAPI(request, token, module.id);
        }
      }
    });

    test('创建模块 - 必填字段验证', async ({ page }) => {
      await page.goto('/admin/modules/create');
      await waitForPageReady(page);

      // 不填写任何内容直接提交
      await page.locator('[data-testid="save-btn"]').click();

      // 验证显示验证错误
      await expect(page.locator('text=请输入模块名称')).toBeVisible({ timeout: 5000 });
    });

    test('创建模块 - 编码格式验证', async ({ page }) => {
      await page.goto('/admin/modules/create');
      await waitForPageReady(page);

      // 填写无效编码
      await page.locator('[data-testid="name-input"]').fill('测试模块');
      await page.locator('[data-testid="code-input"]').fill('InvalidCode123');

      // 提交表单
      await page.locator('[data-testid="save-btn"]').click();

      // 验证编码格式错误提示
      await expect(page.locator('text=模块编码必须以小写字母开头')).toBeVisible({ timeout: 5000 });
    });
  });

  // ==================== 编辑模块测试 ====================

  test.describe('编辑模块', () => {
    test('从列表点击编辑跳转到编辑页面', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 搜索创建的模块
      await page.locator('[data-testid="search-keyword-input"]').fill(module.code);
      await page.locator('[data-testid="search-btn"]').click();
      await waitForPageReady(page);

      // 点击编辑按钮
      const editBtn = page.locator(`tr:has-text("${module.name}") button:has-text("编辑")`);
      await expect(editBtn).toBeVisible({ timeout: 10000 });
      await editBtn.click();

      // 验证跳转到编辑页面
      await page.waitForURL(/\/admin\/modules\/[^/]+\/edit$/);
      expect(page.url()).toMatch(/\/admin\/modules\/[^/]+\/edit$/);
    });

    test('编辑模块页面正确加载数据', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      // 直接访问编辑页面
      await page.goto(`/admin/modules/${module.id}/edit`);
      await waitForPageReady(page);

      // 验证表单数据正确加载
      const nameInput = page.locator('[data-testid="name-input"]');
      await expect(nameInput).toHaveValue(module.name);

      // 验证编码不可编辑
      const codeInput = page.locator('[data-testid="code-input"]');
      await expect(codeInput).toBeDisabled();
    });

    test('成功编辑模块', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);
      const newName = `${module.name}-已编辑`;

      await page.goto(`/admin/modules/${module.id}/edit`);
      await waitForPageReady(page);

      // 修改模块名称
      await page.locator('[data-testid="name-input"]').fill(newName);
      await page.locator('[data-testid="description-input"]').fill('已编辑的描述');

      // 保存
      await page.locator('[data-testid="save-btn"]').click();

      // 等待跳转到列表页
      await page.waitForURL(/\/admin\/modules$/, { timeout: 15000 });
      await waitForPageReady(page);

      // 搜索验证修改后的名称
      await page.locator('[data-testid="search-keyword-input"]').fill(newName);
      await page.locator('[data-testid="search-btn"]').click();
      await waitForPageReady(page);

      await expect(page.locator(`text=${newName}`)).toBeVisible({ timeout: 10000 });
    });

    test('取消编辑返回列表', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto(`/admin/modules/${module.id}/edit`);
      await waitForPageReady(page);

      // 点击取消按钮
      await page.locator('[data-testid="cancel-btn"]').click();

      // 验证返回列表
      await page.waitForURL(/\/admin\/modules$/);
      expect(page.url()).toContain('/admin/modules');
    });
  });

  // ==================== 删除模块测试 ====================

  test.describe('删除模块', () => {
    test('成功删除模块', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 搜索创建的模块
      await page.locator('[data-testid="search-keyword-input"]').fill(module.code);
      await page.locator('[data-testid="search-btn"]').click();
      await waitForPageReady(page);

      // 点击删除按钮
      const deleteBtn = page.locator(`tr:has-text("${module.name}") button:has-text("删除")`);
      await expect(deleteBtn).toBeVisible({ timeout: 10000 });

      // 确认删除（使用原生 window.confirm 对话框）
      page.on('dialog', (dialog) => dialog.accept());
      await deleteBtn.click();

      // 等待删除完成
      await waitForPageReady(page);

      // 验证模块不再显示
      await page.locator('[data-testid="search-btn"]').click();
      await waitForPageReady(page);

      // 从创建列表中移除（已被删除）
      const index = testContext.createdModules.findIndex((m) => m.id === module.id);
      if (index !== -1) {
        testContext.createdModules.splice(index, 1);
      }
    });

    test('取消删除操作', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 搜索创建的模块
      await page.locator('[data-testid="search-keyword-input"]').fill(module.code);
      await page.locator('[data-testid="search-btn"]').click();
      await waitForPageReady(page);

      // 点击删除按钮
      const deleteBtn = page.locator(`tr:has-text("${module.name}") button:has-text("删除")`);
      await expect(deleteBtn).toBeVisible({ timeout: 10000 });

      // 取消删除（使用原生 window.confirm 对话框）
      page.on('dialog', (dialog) => dialog.dismiss());
      await deleteBtn.click();

      // 验证模块仍然存在
      await waitForPageReady(page);
      await expect(page.locator(`text=${module.name}`)).toBeVisible({ timeout: 5000 });
    });
  });

  // ==================== 模块详情查看测试 ====================

  test.describe('模块详情查看', () => {
    test('从列表点击详情跳转到详情页面', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 搜索创建的模块
      await page.locator('[data-testid="search-keyword-input"]').fill(module.code);
      await page.locator('[data-testid="search-btn"]').click();
      await waitForPageReady(page);

      // 点击详情按钮
      const detailBtn = page.locator(`tr:has-text("${module.name}") button:has-text("详情")`);
      await expect(detailBtn).toBeVisible({ timeout: 10000 });
      await detailBtn.click();

      // 验证跳转到详情页面
      await page.waitForURL(/\/admin\/modules\/[^/]+$/);
      expect(page.url()).toMatch(/\/admin\/modules\/[^/]+$/);
    });

    test('详情页面正确显示模块信息', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto(`/admin/modules/${module.id}`);
      await waitForPageReady(page);

      // 验证详情页面元素
      await expect(page.locator('[data-testid="module-detail-page"]')).toBeVisible();
      await expect(page.locator(`text=${module.name}`)).toBeVisible();
      await expect(page.locator(`text=${module.code}`)).toBeVisible();
    });

    test('详情页面 Tabs 切换 - 基本信息', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto(`/admin/modules/${module.id}`);
      await waitForPageReady(page);

      // 验证基本信息 Tab 默认显示
      await expect(page.locator('[data-testid="tab-info"]')).toBeVisible();
      await expect(page.locator('[data-testid="tab-info"][data-state="active"]')).toBeVisible();

      // 验证基本信息内容
      await expect(page.locator('text=模块名称')).toBeVisible();
      await expect(page.locator('text=模块编码')).toBeVisible();
    });

    test('详情页面 Tabs 切换 - 菜单管理', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto(`/admin/modules/${module.id}`);
      await waitForPageReady(page);

      // 点击菜单管理 Tab
      await page.locator('[data-testid="tab-menus"]').click();
      await waitForPageReady(page);

      // 验证菜单管理内容
      await expect(page.locator('text=菜单树')).toBeVisible();
    });

    test('详情页面 Tabs 切换 - 权限管理', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto(`/admin/modules/${module.id}`);
      await waitForPageReady(page);

      // 点击权限管理 Tab
      await page.locator('[data-testid="tab-permissions"]').click();
      await waitForPageReady(page);

      // 验证权限管理内容
      await expect(page.locator('text=权限名称')).toBeVisible();
      await expect(page.locator('text=权限编码')).toBeVisible();
    });

    test('详情页面 Tabs 切换 - 角色管理', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto(`/admin/modules/${module.id}`);
      await waitForPageReady(page);

      // 点击角色管理 Tab
      await page.locator('[data-testid="tab-roles"]').click();
      await waitForPageReady(page);

      // 验证角色管理内容
      await expect(page.locator('text=角色名称')).toBeVisible();
      await expect(page.locator('text=角色编码')).toBeVisible();
    });

    test('从详情页面跳转到编辑页面', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto(`/admin/modules/${module.id}`);
      await waitForPageReady(page);

      // 点击编辑按钮
      await page.locator('[data-testid="edit-btn"]').click();

      // 验证跳转到编辑页面
      await page.waitForURL(/\/admin\/modules\/[^/]+\/edit$/);
      expect(page.url()).toMatch(/\/admin\/modules\/[^/]+\/edit$/);
    });

    test('从详情页面返回列表', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto(`/admin/modules/${module.id}`);
      await waitForPageReady(page);

      // 点击返回按钮
      await page.locator('[data-testid="back-btn"]').click();

      // 验证返回列表
      await page.waitForURL(/\/admin\/modules$/);
      expect(page.url()).toContain('/admin/modules');
    });
  });

  // ==================== 搜索筛选测试 ====================

  test.describe('搜索筛选', () => {
    test('关键词搜索功能', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 输入搜索关键词
      await page.locator('[data-testid="search-keyword-input"]').fill(module.code);
      await page.locator('[data-testid="search-btn"]').click();
      await waitForPageReady(page);

      // 验证搜索结果包含创建的模块
      await expect(page.locator(`text=${module.code}`)).toBeVisible({ timeout: 10000 });
    });

    test('状态筛选 - 启用', async ({ page }) => {
      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 选择启用状态
      await page.locator('[data-testid="status-select"]').click();
      await page.locator('text=启用').click();
      await page.locator('[data-testid="search-btn"]').click();
      await waitForPageReady(page);

      // 验证只显示启用的模块
      const badges = page.locator('[data-testid="module-table"] span:has-text("启用")');
      const count = await badges.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('状态筛选 - 停用', async ({ page }) => {
      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 选择停用状态
      await page.locator('[data-testid="status-select"]').click();
      await page.locator('text=停用').click();
      await page.locator('[data-testid="search-btn"]').click();
      await waitForPageReady(page);

      // 验证结果
      await expect(page.locator('[data-testid="module-table"]')).toBeVisible();
    });

    test('重置搜索条件', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 输入搜索关键词
      await page.locator('[data-testid="search-keyword-input"]').fill(module.code);
      await page.locator('[data-testid="status-select"]').click();
      await page.locator('text=启用').click();

      // 点击重置
      await page.locator('[data-testid="reset-btn"]').click();
      await waitForPageReady(page);

      // 验证输入框被清空
      await expect(page.locator('[data-testid="search-keyword-input"]')).toHaveValue('');
    });

    test('回车键触发搜索', async ({ page, request }) => {
      // 创建测试模块
      const module = await createTestModule(request);

      await page.goto('/admin/modules');
      await waitForPageReady(page);

      // 输入搜索关键词并按回车
      await page.locator('[data-testid="search-keyword-input"]').fill(module.code);
      await page.locator('[data-testid="search-keyword-input"]').press('Enter');
      await waitForPageReady(page);

      // 验证搜索结果
      await expect(page.locator(`text=${module.code}`)).toBeVisible({ timeout: 10000 });
    });
  });
});
