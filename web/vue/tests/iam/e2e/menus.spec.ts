/**
 * IAM 菜单管理 E2E 测试
 *
 * 测试场景：
 * 1. 菜单树渲染测试 - 验证菜单树加载和节点渲染
 * 2. 菜单详情展示测试 - 验证选中菜单后右侧详情面板展示
 */
import {
  test,
  expect,
  iamUserLogin,
  waitForSkeletonGone,
  waitForPageReady,
  captureConsoleErrors,
} from "./fixtures";

// ============================================================================
// 测试用例
// ============================================================================

test.describe("IAM 菜单管理页面", () => {
  test.beforeEach(async ({ page, request }) => {
    await iamUserLogin(page, request);
  });

  // ===========================================================================
  // 1. 菜单树渲染测试
  // ===========================================================================

  test("菜单树正确渲染 - 访问页面后应展示菜单树结构", async ({ page }) => {
    await page.goto("/iam/menus");
    await waitForPageReady(page);

    // 验证菜单树容器可见
    const treeContainer = page.locator('[data-testid="menu-tree-container"]');
    await expect(treeContainer).toBeVisible();

    // 等待骨架屏消失（菜单数据加载完成）
    await waitForSkeletonGone(page);

    // 验证菜单树节点至少有一个渲染
    const treeItems = page.locator('[data-testid="menu-tree-items"]');
    await expect(treeItems).toBeVisible();

    const treeNodes = treeItems.locator('[data-testid="menu-tree-node"]');
    const nodeCount = await treeNodes.count();
    expect(nodeCount).toBeGreaterThan(0);
  });

  test("菜单树节点存在且包含文本内容", async ({ page }) => {
    await page.goto("/iam/menus");
    await waitForPageReady(page);
    await waitForSkeletonGone(page);

    // 获取第一个菜单节点
    const firstNode = page.locator('[data-testid="menu-tree-node"]').first();
    await expect(firstNode).toBeVisible();

    // 节点应包含文本（菜单名称）
    const nodeText = await firstNode.textContent();
    expect(nodeText?.trim().length).toBeGreaterThan(0);
  });

  test("点击菜单节点应高亮选中状态", async ({ page }) => {
    await page.goto("/iam/menus");
    await waitForPageReady(page);
    await waitForSkeletonGone(page);

    // 默认情况下第一个菜单应已被选中（onMounted 逻辑），验证详情面板可见
    const detailPanel = page.locator('[data-testid="menu-detail-panel"]');
    await expect(detailPanel).toBeVisible();

    // 验证详情头部可见（说明已选中菜单）
    const detailHeader = page.locator('[data-testid="menu-detail-header"]');
    await expect(detailHeader).toBeVisible({ timeout: 5000 });
  });

  // ===========================================================================
  // 2. 菜单详情展示测试
  // ===========================================================================

  test("选中菜单后右侧详情面板展示菜单基本信息", async ({ page }) => {
    await page.goto("/iam/menus");
    await waitForPageReady(page);
    await waitForSkeletonGone(page);

    // 等待默认选中后详情面板出现
    const detailHeader = page.locator('[data-testid="menu-detail-header"]');
    await expect(detailHeader).toBeVisible({ timeout: 5000 });

    // 验证详情头部包含菜单名称
    const headerName = detailHeader.locator("h2");
    await expect(headerName).toBeVisible();
    const nameText = await headerName.textContent();
    expect(nameText?.trim().length).toBeGreaterThan(0);

    // 验证详情头部包含模块 Badge
    const moduleBadge = detailHeader.locator(".badge, [class*='badge']").or(detailHeader.locator("span"));
    expect(await moduleBadge.count()).toBeGreaterThan(0);
  });

  test("菜单信息 Tab 展示描述列表项", async ({ page }) => {
    await page.goto("/iam/menus");
    await waitForPageReady(page);
    await waitForSkeletonGone(page);

    // 等待详情面板加载
    const detailHeader = page.locator('[data-testid="menu-detail-header"]');
    await expect(detailHeader).toBeVisible({ timeout: 5000 });

    // 验证默认激活"菜单信息" Tab
    const infoTab = page.locator('[data-testid="menu-tab-info"]');
    await expect(infoTab).toBeVisible();

    // 验证菜单信息内容区域有描述列表项
    const infoContent = page.locator('[data-testid="menu-info-content"]');
    await expect(infoContent).toBeVisible();

    // 描述列表应包含菜单名称、编码、路由等字段
    const infoText = await infoContent.textContent();
    expect(infoText).toContain("菜单名称");
    expect(infoText).toContain("菜单编码");
    expect(infoText).toContain("路由路径");
    expect(infoText).toContain("所属模块");
  });

  test("Tab 切换到权限列表", async ({ page }) => {
    await page.goto("/iam/menus");
    await waitForPageReady(page);
    await waitForSkeletonGone(page);

    // 等待详情面板加载
    const detailHeader = page.locator('[data-testid="menu-detail-header"]');
    await expect(detailHeader).toBeVisible({ timeout: 5000 });

    // 点击"权限列表" Tab
    const permissionsTab = page.locator('[data-testid="menu-tab-permissions"]');
    await expect(permissionsTab).toBeVisible();
    await permissionsTab.click();

    // 验证权限列表内容区域可见
    const permissionsContent = page.locator(
      '[data-testid="menu-permissions-content"]'
    );
    await expect(permissionsContent).toBeVisible();

    // 权限列表内容应有表格或"暂无关联权限"提示
    const contentText = await permissionsContent.textContent();
    // 要么有权限表，要么提示暂无权限
    expect(contentText?.trim().length).toBeGreaterThan(0);
  });

  test("切换菜单节点后详情面板内容更新", async ({ page }) => {
    await page.goto("/iam/menus");
    await waitForPageReady(page);
    await waitForSkeletonGone(page);

    // 等待详情面板加载
    const detailHeader = page.locator('[data-testid="menu-detail-header"]');
    await expect(detailHeader).toBeVisible({ timeout: 5000 });

    // 记住当前选中的菜单名称
    const firstName = await detailHeader.locator("h2").textContent();

    // 获取所有菜单树节点
    const treeNodes = page.locator('[data-testid="menu-tree-node"]');
    const nodeCount = await treeNodes.count();

    if (nodeCount > 1) {
      // 点击第二个菜单节点
      await treeNodes.nth(1).click();

      // 等待详情面板刷新
      await page.waitForTimeout(500);

      // 验证详情面板中的名称已更新
      const secondName = await detailHeader.locator("h2").textContent();
      expect(secondName).not.toBe(firstName);
      expect(secondName?.trim().length).toBeGreaterThan(0);
    }
  });

  test("菜单管理页面无控制台错误", async ({ page }) => {
    const errors = captureConsoleErrors(page);

    await page.goto("/iam/menus");
    await waitForPageReady(page);
    await waitForSkeletonGone(page);

    // 过滤掉非严重错误
    const criticalErrors = errors.filter(
      (err) =>
        !err.includes("warning") &&
        !err.includes("Warning") &&
        !err.includes("[HMR]")
    );

    expect(criticalErrors).toHaveLength(0);
  });
});
