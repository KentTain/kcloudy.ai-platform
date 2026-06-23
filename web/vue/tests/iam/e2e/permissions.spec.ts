/**
 * IAM 模块权限管理 E2E 测试
 *
 * 测试场景（来自 spec.md）：
 * 1. 权限列表渲染 - 访问 /iam/permissions 页面，左侧权限列表正确渲染，显示权限名称和编码
 * 2. 权限关联展示 - 选中某个权限，右侧显示角色列表、菜单列表 Tabs，关联的角色和菜单信息正确展示
 * 3. 权限搜索 - 在搜索框输入权限名称或编码，权限列表过滤显示匹配结果（弹窗内，属于角色权限分配）
 */
import { test, expect, iamUserLogin, waitForPageReady, waitForSkeletonGone } from './fixtures';

// ============================================================================
// 测试用例
// ============================================================================

test.describe('权限管理测试', () => {
  test.beforeEach(async ({ page, request }) => {
    // 使用 IAM 用户 API 辅助登录
    await iamUserLogin(page, request);
  });

  // ===========================================================================
  // 1. 权限列表渲染测试
  // ===========================================================================

  test('权限列表渲染 - 页面加载成功', async ({ page }) => {
    // 访问权限管理页面
    await page.goto('/iam/permissions');
    await waitForPageReady(page);

    // 验证页面 URL 正确
    expect(page.url()).toContain('/iam/permissions');

    // 验证页面标题存在
    const pageTitle = page.locator('h1, h2').filter({ hasText: '权限管理' });
    await expect(pageTitle).toBeVisible();
  });

  test('权限列表渲染 - 权限列表容器存在', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForPageReady(page);

    // 验证权限列表容器存在
    const permissionList = page.locator('[data-testid="permission-list"]');
    await expect(permissionList).toBeVisible();

    // 验证列表标题存在
    const listTitle = permissionList.locator('text=权限列表');
    await expect(listTitle).toBeVisible();
  });

  test('权限列表渲染 - 权限项显示', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 等待权限数据加载
    const permissionItems = page.locator('[data-testid^="permission-item-"]');
    const count = await permissionItems.count();

    // 验证至少有一个权限项
    expect(count).toBeGreaterThan(0);
  });

  test('权限列表渲染 - 权限项内容完整', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 获取第一个权限项
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await expect(firstPermission).toBeVisible();

    // 验证权限名称存在
    const permissionName = firstPermission.locator('[data-testid="permission-item-name"]');
    await expect(permissionName).toBeVisible();
    const nameText = await permissionName.textContent();
    expect(nameText?.trim().length).toBeGreaterThan(0);

    // 验证权限编码存在
    const permissionCode = firstPermission.locator('[data-testid="permission-item-code"]');
    await expect(permissionCode).toBeVisible();
    const codeText = await permissionCode.textContent();
    expect(codeText?.trim().length).toBeGreaterThan(0);
  });

  test('权限列表渲染 - 选中权限高亮显示', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 点击第一个权限项
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await firstPermission.click();

    // 验证选中状态（按钮有 bg-accent 类）
    await expect(firstPermission).toHaveClass(/bg-accent/);
  });

  // ===========================================================================
  // 2. 权限关联展示测试
  // ===========================================================================

  test('权限关联展示 - 选中权限显示详情', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 点击第一个权限项
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await firstPermission.click();

    // 等待详情显示
    const permissionDetail = page.locator('[data-testid="permission-detail"]');
    await expect(permissionDetail).toBeVisible();

    // 验证详情内容完整
    const detailName = page.locator('[data-testid="permission-detail-name"]');
    await expect(detailName).toBeVisible();

    const detailCode = page.locator('[data-testid="permission-detail-code"]');
    await expect(detailCode).toBeVisible();

    const detailResource = page.locator('[data-testid="permission-detail-resource"]');
    await expect(detailResource).toBeVisible();

    const detailAction = page.locator('[data-testid="permission-detail-action"]');
    await expect(detailAction).toBeVisible();
  });

  test('权限关联展示 - Tabs 容器存在', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 点击第一个权限项
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await firstPermission.click();

    // 验证 Tabs 容器存在
    const tabs = page.locator('[data-testid="permission-tabs"]');
    await expect(tabs).toBeVisible();

    // 验证角色列表 Tab 存在
    const rolesTab = page.locator('[data-testid="permission-tab-roles"]');
    await expect(rolesTab).toBeVisible();
    await expect(rolesTab).toContainText('角色列表');

    // 验证菜单列表 Tab 存在
    const menusTab = page.locator('[data-testid="permission-tab-menus"]');
    await expect(menusTab).toBeVisible();
    await expect(menusTab).toContainText('菜单列表');
  });

  test('权限关联展示 - 角色列表 Tab 内容', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 点击第一个权限项
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await firstPermission.click();

    // 点击角色列表 Tab
    const rolesTab = page.locator('[data-testid="permission-tab-roles"]');
    await rolesTab.click();

    // 等待角色内容加载
    const rolesContent = page.locator('[data-testid="permission-roles-content"]');
    await expect(rolesContent).toBeVisible();

    // 验证角色计数显示
    const rolesCount = page.locator('[data-testid="permission-roles-count"]');
    await expect(rolesCount).toBeVisible();
    const countText = await rolesCount.textContent();
    expect(countText).toContain('个角色');
  });

  test('权限关联展示 - 菜单列表 Tab 内容', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 点击第一个权限项
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await firstPermission.click();

    // 点击菜单列表 Tab
    const menusTab = page.locator('[data-testid="permission-tab-menus"]');
    await menusTab.click();

    // 等待菜单内容加载
    const menusContent = page.locator('[data-testid="permission-menus-content"]');
    await expect(menusContent).toBeVisible();

    // 验证菜单计数显示
    const menusCount = page.locator('[data-testid="permission-menus-count"]');
    await expect(menusCount).toBeVisible();
    const countText = await menusCount.textContent();
    expect(countText).toContain('个菜单');
  });

  test('权限关联展示 - Tabs 切换正常', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 点击第一个权限项
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await firstPermission.click();

    // 初始在角色列表 Tab
    const rolesContent = page.locator('[data-testid="permission-roles-content"]');
    await expect(rolesContent).toBeVisible();

    // 切换到菜单列表 Tab
    const menusTab = page.locator('[data-testid="permission-tab-menus"]');
    await menusTab.click();
    await page.waitForTimeout(300); // 等待动画完成

    // 验证菜单内容可见
    const menusContent = page.locator('[data-testid="permission-menus-content"]');
    await expect(menusContent).toBeVisible();

    // 切换回角色列表 Tab
    const rolesTab = page.locator('[data-testid="permission-tab-roles"]');
    await rolesTab.click();
    await page.waitForTimeout(300);

    // 验证角色内容可见
    await expect(rolesContent).toBeVisible();
  });

  test('权限关联展示 - 切换权限项更新详情', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 点击第一个权限项
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await firstPermission.click();

    // 获取第一个权限的名称
    const firstName = await page.locator('[data-testid="permission-detail-name"]').textContent();

    // 点击第二个权限项（如果存在）
    const permissionItems = page.locator('[data-testid^="permission-item-"]');
    const count = await permissionItems.count();

    if (count > 1) {
      const secondPermission = permissionItems.nth(1);
      await secondPermission.click();

      // 验证详情已更新
      const secondName = await page.locator('[data-testid="permission-detail-name"]').textContent();
      expect(secondName).not.toBe(firstName);
    }
  });

  // ===========================================================================
  // 3. 边界情况测试
  // ===========================================================================

  test('权限列表渲染 - 加载状态', async ({ page }) => {
    // 拦截 API 请求延迟
    await page.route('**/iam/admin/v1/permissions*', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      route.continue();
    });

    await page.goto('/iam/permissions');

    // 验证加载骨架屏存在
    const loadingSkeleton = page.locator('[data-testid="permission-loading"]');
    await expect(loadingSkeleton).toBeVisible();

    // 等待加载完成
    await waitForSkeletonGone(page, 5000);

    // 验证加载状态消失
    await expect(loadingSkeleton).not.toBeVisible();
  });

  test('权限关联展示 - 默认选中第一个权限', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 验证默认选中第一个权限
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await expect(firstPermission).toHaveClass(/bg-accent/);

    // 验证详情显示
    const permissionDetail = page.locator('[data-testid="permission-detail"]');
    await expect(permissionDetail).toBeVisible();
  });

  test('权限关联展示 - 角色表格数据加载', async ({ page }) => {
    await page.goto('/iam/permissions');
    await waitForSkeletonGone(page, 10000);
    await page.waitForLoadState('networkidle');

    // 点击第一个权限项
    const firstPermission = page.locator('[data-testid^="permission-item-"]').first();
    await firstPermission.click();

    // 等待角色内容加载
    const rolesContent = page.locator('[data-testid="permission-roles-content"]');
    await expect(rolesContent).toBeVisible();

    // 验证表格存在
    const table = rolesContent.locator('table, [role="table"]');
    const tableVisible = await table.isVisible().catch(() => false);

    // 如果表格可见，验证有数据
    if (tableVisible) {
      const rows = table.locator('tr, [role="row"]');
      const rowCount = await rows.count();
      expect(rowCount).toBeGreaterThan(0);
    }
  });
});
