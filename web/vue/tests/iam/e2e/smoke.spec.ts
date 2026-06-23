/**
 * IAM 模块冒烟测试
 *
 * 测试场景：
 * 1. 菜单遍历测试 - 访问所有 IAM 页面路径
 * 2. 页面基础渲染验证 - 骨架屏消失、内容可见、无控制台错误
 * 3. 关键页面特定验证
 */
import { test, expect, iamUserLogin, waitForSkeletonGone, verifyPageHasContent, captureConsoleErrors, waitForPageReady } from './fixtures';

// ============================================================================
// 测试场景配置
// ============================================================================

/**
 * IAM 模块可见页面路径（不含隐藏的 create/edit/detail 页面）
 */
const IAM_PAGE_TESTS: Record<string, string[]> = {
  '/iam/users': ['用户列表', '搜索/筛选栏'],
  '/iam/roles': ['角色列表'],
  '/iam/permissions': ['权限列表', '权限分组'],
  '/iam/organizations': ['组织树', '组织结构'],
  '/iam/menus': ['菜单树'],
  '/iam/profile': ['个人中心', '用户信息'],
};

/** 所有 IAM 页面路径 */
const ALL_IAM_PATHS = Object.keys(IAM_PAGE_TESTS);

// ============================================================================
// 测试用例
// ============================================================================

test.describe('IAM 模块冒烟测试', () => {
  test.beforeEach(async ({ page, request }) => {
    // 使用 IAM 用户 API 辅助登录
    await iamUserLogin(page, request);
  });

  // ===========================================================================
  // 1. 菜单遍历测试
  // ===========================================================================

  test('遍历所有 IAM 页面路径', async ({ page }) => {
    for (const path of ALL_IAM_PATHS) {
      // 访问页面
      const response = await page.goto(path);
      expect(response?.status()).toBe(200);

      // 等待页面加载
      await page.waitForLoadState('networkidle');

      // 验证页面 URL 正确
      expect(page.url()).toContain(path);

      // 验证页面有内容
      await verifyPageHasContent(page);
    }
  });

  // ===========================================================================
  // 2. 页面基础渲染验证
  // ===========================================================================

  test('IAM 页面基础渲染 - 骨架屏消失', async ({ page }) => {
    await page.goto('/iam/users');
    await waitForSkeletonGone(page, 10000);
    await verifyPageHasContent(page);
  });

  test('IAM 页面基础渲染 - 内容可见', async ({ page }) => {
    await page.goto('/iam/roles');
    await waitForSkeletonGone(page);

    // 验证页面标题存在
    const pageTitle = page.locator('h1, h2, [data-testid="page-title"]').first();
    await expect(pageTitle).toBeVisible();

    // 验证主要内容区域有文本
    const content = await page.locator('body').textContent();
    expect(content).toBeTruthy();
    expect(content!.trim().length).toBeGreaterThan(100);
  });

  test('IAM 页面基础渲染 - 无控制台错误', async ({ page }) => {
    const errors = captureConsoleErrors(page);

    await page.goto('/iam/users');
    await waitForSkeletonGone(page);
    await page.waitForLoadState('networkidle');

    // 过滤掉非严重错误
    const criticalErrors = errors.filter(err =>
      !err.includes('warning') &&
      !err.includes('Warning') &&
      !err.includes('[HMR]')
    );

    expect(criticalErrors).toHaveLength(0);
  });

  // ===========================================================================
  // 3. 关键页面特定验证
  // ===========================================================================

  test('用户管理页面 - 基本元素存在', async ({ page }) => {
    await page.goto('/iam/users');
    await waitForPageReady(page);

    // 验证页面有搜索区域或表格区域
    const searchArea = page.locator('[class*="search"], [class*="filter"], input[type="search"], input[placeholder*="搜索"], input[placeholder*="关键词"]');
    const tableArea = page.locator('table, [class*="table"], [role="table"]');

    // 至少有一个可见
    const searchVisible = await searchArea.first().isVisible().catch(() => false);
    const tableVisible = await tableArea.first().isVisible().catch(() => false);

    expect(searchVisible || tableVisible).toBeTruthy();
  });

  test('角色管理页面 - 基本元素存在', async ({ page }) => {
    await page.goto('/iam/roles');
    await waitForPageReady(page);

    // 验证页面有内容
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.trim().length).toBeGreaterThan(0);
  });

  test('权限管理页面 - 基本元素存在', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForPageReady(page);

    // 验证页面有内容
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.trim().length).toBeGreaterThan(0);
  });

  test('组织管理页面 - 基本元素存在', async ({ page }) => {
    await page.goto('/iam/organizations');
    await waitForPageReady(page);

    // 验证页面有树结构或内容区域
    const treeArea = page.locator('[class*="tree"], [role="tree"]');
    const contentArea = page.locator('main, [role="main"]');

    const treeVisible = await treeArea.first().isVisible().catch(() => false);
    const contentVisible = await contentArea.first().isVisible().catch(() => false);

    expect(treeVisible || contentVisible).toBeTruthy();
  });

  test('菜单管理页面 - 基本元素存在', async ({ page }) => {
    await page.goto('/iam/menus');
    await waitForPageReady(page);

    // 验证页面有内容
    const bodyText = await page.locator('body').textContent();
    expect(bodyText?.trim().length).toBeGreaterThan(0);
  });

  test('个人中心页面 - 基本元素存在', async ({ page }) => {
    await page.goto('/iam/profile');
    await waitForPageReady(page);

    // 验证页面有用户信息相关内容
    const bodyText = await page.locator('body').textContent();

    // 个人中心页面应展示用户相关信息（如用户名、角色等）
    expect(bodyText).toBeTruthy();
    expect(bodyText!.trim().length).toBeGreaterThan(50);
  });

  // ===========================================================================
  // 4. 页面间导航验证
  // ===========================================================================

  test('IAM 页面间快速切换无错误', async ({ page }) => {
    const paths = ALL_IAM_PATHS;

    for (const path of paths) {
      const response = await page.goto(path);
      expect(response?.status()).toBe(200);

      // 短等待确保页面基本渲染
      await page.waitForLoadState('networkidle');
    }
  });
});
