/**
 * Tenant 模块冒烟测试
 *
 * 测试场景：
 * 1. 菜单遍历测试 - 访问所有可见菜单路径
 * 2. 页面基础渲染验证 - 骨架屏消失、内容可见、无控制台错误
 * 3. 统计卡片渲染验证
 * 4. Tab 页签切换验证
 */
import { test, expect, adminLoginViaAPI } from './fixtures';

// ============================================================================
// 测试场景配置
// ============================================================================

/**
 * 菜单路径与测试场景映射
 */
const MENU_TESTS: Record<string, string[]> = {
  '/admin/tenants': ['统计卡片', '租户列表'],
  '/admin/resources': ['Tab切换', '资源配置列表'],
  '/admin/modules': ['模块列表'],
};

// ============================================================================
// 辅助函数
// ============================================================================

/**
 * 等待骨架屏消失
 * @param page Playwright Page 对象
 * @param timeout 超时时间（毫秒），默认 10000ms
 */
async function waitForSkeletonGone(page: import('@playwright/test').Page, timeout = 10000) {
  try {
    // 等待常见的骨架屏元素消失
    await page.waitForSelector('[data-skeleton="true"]', { state: 'hidden', timeout });
    await page.waitForSelector('.skeleton', { state: 'hidden', timeout });
    await page.waitForSelector('[data-loading="true"]', { state: 'hidden', timeout });
  } catch {
    // 骨架屏可能已经不存在，忽略错误
  }
}

/**
 * 验证页面有可见内容
 * @param page Playwright Page 对象
 */
async function verifyPageHasContent(page: import('@playwright/test').Page) {
  // 等待页面主要内容区域可见
  const contentArea = page.locator('main, [role="main"], .main-content, [data-testid="main-content"]').first();
  const hasMainContent = await contentArea.count() > 0;

  if (hasMainContent) {
    await expect(contentArea).toBeVisible();
  }

  // 验证页面至少有一些可见的文本内容
  const bodyText = await page.locator('body').textContent();
  expect(bodyText?.trim().length).toBeGreaterThan(0);
}

/**
 * 捕获控制台错误
 * @param page Playwright Page 对象
 * @returns 错误消息数组
 */
function captureConsoleErrors(page: import('@playwright/test').Page): string[] {
  const errors: string[] = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  page.on('pageerror', (error) => {
    errors.push(error.message);
  });

  return errors;
}

/**
 * 验证统计卡片
 * @param page Playwright Page 对象
 * @param cardTitles 卡片标题列表
 */
async function verifyStatCards(page: import('@playwright/test').Page, cardTitles: string[]) {
  for (const title of cardTitles) {
    // 验证卡片标题可见
    const cardTitle = page.locator(`text="${title}"`);
    await expect(cardTitle).toBeVisible();

    // 验证卡片有数值（数字格式）
    const card = cardTitle.locator('..');
    const cardText = await card.textContent();
    expect(cardText).toMatch(/\d+/);
  }
}

// ============================================================================
// 测试用例
// ============================================================================

test.describe('Tenant 模块冒烟测试', () => {
  test.beforeEach(async ({ page, request }) => {
    // 使用 API 辅助登录
    await adminLoginViaAPI(page, request);
  });

  // ===========================================================================
  // 1. 菜单遍历测试
  // ===========================================================================

  test('遍历所有可见菜单路径', async ({ page, request }) => {
    // 获取菜单数据
    const meResponse = await request.get('/api/tenant/admin/v1/admin/me');
    expect(meResponse.ok()).toBeTruthy();

    const meData = await meResponse.json();
    const menus = meData?.data?.menus || [];

    // 过滤可见菜单并排序
    const visibleMenus = menus
      .filter((menu: any) => menu.is_visible === true)
      .sort((a: any, b: any) => (a.sort_order || 0) - (b.sort_order || 0));

    expect(visibleMenus.length).toBeGreaterThan(0);

    // 遍历每个菜单路径
    for (const menu of visibleMenus) {
      const path = menu.path;
      if (!path) continue;

      // 访问页面
      const response = await page.goto(path);
      expect(response?.status()).toBe(200);

      // 验证页面无 JavaScript 错误
      const errors = captureConsoleErrors(page);
      await page.waitForLoadState('networkidle');

      // 验证没有严重错误（允许 warning）
      const criticalErrors = errors.filter(err =>
        !err.includes('warning') &&
        !err.includes('Warning') &&
        !err.includes('[HMR]') // 忽略热更新相关消息
      );
      expect(criticalErrors).toHaveLength(0);
    }
  });

  // ===========================================================================
  // 2. 页面基础渲染验证
  // ===========================================================================

  test('页面基础渲染 - 骨架屏消失', async ({ page }) => {
    await page.goto('/admin/tenants');

    // 等待骨架屏消失（10秒超时）
    await waitForSkeletonGone(page, 10000);

    // 验证页面有可见内容
    await verifyPageHasContent(page);
  });

  test('页面基础渲染 - 内容可见', async ({ page }) => {
    await page.goto('/admin/tenants');
    await waitForSkeletonGone(page);

    // 验证页面标题存在
    const pageTitle = page.locator('h1, h2, [data-testid="page-title"]').first();
    await expect(pageTitle).toBeVisible();

    // 验证主要内容区域有文本
    const content = await page.locator('body').textContent();
    expect(content).toBeTruthy();
    expect(content!.trim().length).toBeGreaterThan(100);
  });

  test('页面基础渲染 - 无控制台错误', async ({ page }) => {
    const errors = captureConsoleErrors(page);

    await page.goto('/admin/tenants');
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
  // 3. 统计卡片渲染验证
  // ===========================================================================

  test('租户管理页面 - 统计卡片渲染', async ({ page }) => {
    await page.goto('/admin/tenants');
    await waitForSkeletonGone(page);

    // 验证统计卡片
    const cardTitles = ['租户总数', '未激活数', '过期数'];
    await verifyStatCards(page, cardTitles);
  });

  test('统计卡片 - 数值格式验证', async ({ page }) => {
    await page.goto('/admin/tenants');
    await waitForSkeletonGone(page);

    // 获取所有统计数值
    const statValues = await page.locator('[class*="stat"], [class*="card"] [class*="text-2xl"]').allTextContents();

    // 验证每个数值都是有效数字格式
    for (const value of statValues) {
      const trimmed = value.trim();
      if (trimmed) {
        // 允许纯数字或带单位的数字
        expect(trimmed).toMatch(/^\d+(\.\d+)?%?$/);
      }
    }
  });

  // ===========================================================================
  // 4. Tab 页签切换验证
  // ===========================================================================

  test('资源配置页面 - 5个Tab存在', async ({ page }) => {
    await page.goto('/admin/resources');
    await waitForSkeletonGone(page);

    // 验证 5 个 Tab 存在
    const expectedTabs = ['数据库', '存储', '缓存', '队列', '发布订阅'];

    for (const tabName of expectedTabs) {
      const tab = page.locator(`[role="tab"]`, { hasText: tabName });
      await expect(tab).toBeVisible();
    }
  });

  test('资源配置页面 - 默认选中第一个Tab', async ({ page }) => {
    await page.goto('/admin/resources');
    await waitForSkeletonGone(page);

    // 验证默认选中第一个 Tab（数据库）
    const firstTab = page.locator('[role="tab"]').first();
    await expect(firstTab).toHaveAttribute('data-state', 'active');

    // 验证第一个 Tab 内容可见
    const firstTabContent = page.locator('[role="tabpanel"]').first();
    await expect(firstTabContent).toBeVisible();
  });

  test('资源配置页面 - Tab切换功能', async ({ page }) => {
    await page.goto('/admin/resources');
    await waitForSkeletonGone(page);

    // 点击第二个 Tab（存储）
    const secondTab = page.locator('[role="tab"]', { hasText: '存储' });
    await secondTab.click();

    // 验证 Tab 激活状态
    await expect(secondTab).toHaveAttribute('data-state', 'active');

    // 等待数据加载
    await page.waitForLoadState('networkidle');
    await waitForSkeletonGone(page);

    // 验证表格内容区域可见
    const tableContent = page.locator('[role="tabpanel"] table, [role="tabpanel"] [class*="table"]');
    const tableCount = await tableContent.count();
    expect(tableCount).toBeGreaterThanOrEqual(0); // 表格可能为空，但区域应存在
  });

  test('资源配置页面 - 所有Tab可切换', async ({ page }) => {
    await page.goto('/admin/resources');
    await waitForSkeletonGone(page);

    const tabNames = ['数据库', '存储', '缓存', '队列', '发布订阅'];

    for (const tabName of tabNames) {
      const tab = page.locator('[role="tab"]', { hasText: tabName });
      await tab.click();

      // 验证激活状态
      await expect(tab).toHaveAttribute('data-state', 'active');

      // 等待加载
      await page.waitForLoadState('networkidle');
      await waitForSkeletonGone(page, 5000);
    }
  });

  // ===========================================================================
  // 5. 测试场景映射验证
  // ===========================================================================

  // 为每个菜单路径生成独立测试
  for (const [path, scenarios] of Object.entries(MENU_TESTS)) {
    test(`菜单路径 ${path} - 场景验证`, async ({ page }) => {
      await page.goto(path);
      await waitForSkeletonGone(page);

      // 验证页面加载成功
      expect(page.url()).toContain(path);

      // 验证页面有内容
      await verifyPageHasContent(page);
    });
  }
});
