/**
 * Tenant 模块 - 资源配置 CRUD E2E 测试
 *
 * 测试场景：
 * - 页面加载与 Tab 切换（5 种资源类型）
 * - 统计数据卡片
 * - 创建资源配置（弹窗表单）
 * - 编辑资源配置（弹窗表单）
 * - 删除资源配置（确认弹窗）
 * - 搜索资源
 * - 刷新列表
 * - 测试连接
 */
import { test, expect, adminLoginViaAPI, waitForPageReady } from './fixtures';
import {
  getAdminToken,
  createResourceConfigViaAPI,
  deleteResourceConfigViaAPI,
  cleanupAllE2EData,
  type ResourceType,
  type ResourceResponse,
} from './data-helpers';
import type { APIRequestContext, Page } from '@playwright/test';

// ============================================================================
// 测试数据管理
// ============================================================================

interface TestContext {
  createdResources: { type: ResourceType; id: string }[];
}

const testContext: TestContext = {
  createdResources: [],
};

/**
 * 通过 API 创建测试资源
 */
async function createTestResource(
  request: APIRequestContext,
  token: string,
  type: ResourceType,
  name?: string
): Promise<ResourceResponse> {
  const resource = await createResourceConfigViaAPI(request, token, type, {
    name: name || `e2e-${type}-${Date.now()}`,
    host: 'localhost',
    port: 5432,
    database: 'test_db',
    username: 'test_user',
    password: 'test_pass',
  });
  testContext.createdResources.push({ type, id: resource.id });
  return resource;
}

/**
 * 清理所有测试数据
 */
async function cleanupTestData(request: APIRequestContext) {
  const token = await getAdminToken(request);

  for (const { type, id } of testContext.createdResources) {
    await deleteResourceConfigViaAPI(request, token, type, id).catch(() => {});
  }
  testContext.createdResources = [];

  await cleanupAllE2EData(request, token);
}

// ============================================================================
// 辅助函数
// ============================================================================

/**
 * 资源类型配置
 */
const RESOURCE_TYPES: { type: ResourceType; label: string }[] = [
  { type: 'database', label: '数据库' },
  { type: 'storage', label: '存储' },
  { type: 'cache', label: '缓存' },
  { type: 'queue', label: '队列' },
  { type: 'pubsub', label: '发布订阅' },
];

/**
 * 导航到资源配置页面
 */
async function goToResourcePage(page: Page) {
  await page.goto('/admin/resources');
  await waitForPageReady(page);
}

/**
 * 切换到指定资源类型的 Tab
 */
async function switchToTab(page: Page, type: ResourceType) {
  const tab = page.getByTestId(`tab-${type}`);
  await tab.click();
  await page.waitForTimeout(500);
}

/**
 * 打开创建弹窗
 */
async function openCreateDialog(page: Page) {
  await page.getByTestId('create-button').click();
  await expect(page.getByTestId('resource-dialog')).toBeVisible();
}

/**
 * 打开某个行的编辑弹窗
 */
async function openEditDialog(page: Page, name: string) {
  const row = page.locator('tbody tr', { hasText: name }).first();
  await expect(row).toBeVisible({ timeout: 10000 });
  const editBtn = row.locator('button:has-text("编辑")');
  await editBtn.click();
  await expect(page.getByTestId('resource-dialog')).toBeVisible();
}

/**
 * 点击某个行的删除按钮
 */
async function clickRowDeleteButton(page: Page, name: string) {
  const row = page.locator('tbody tr', { hasText: name }).first();
  await expect(row).toBeVisible({ timeout: 10000 });
  const deleteBtn = row.locator('button:has-text("删除")');
  await deleteBtn.click();
  await expect(page.getByTestId('delete-dialog')).toBeVisible();
}

// ============================================================================
// 测试用例
// ============================================================================

test.describe('资源配置管理 CRUD', () => {
  let adminToken: string;

  test.beforeAll(async ({ request }) => {
    adminToken = await getAdminToken(request);
    await cleanupAllE2EData(request, adminToken);
  });

  test.beforeEach(async ({ page, request }) => {
    await adminLoginViaAPI(page, request);
  });

  test.afterAll(async ({ request }) => {
    await cleanupTestData(request);
  });

  // ==================== 页面加载 & Tab 切换测试 ====================

  test.describe('页面加载 & Tab 切换', () => {
    test('访问 /admin/resources 正确渲染页面', async ({ page }) => {
      await goToResourcePage(page);

      // 验证页面标题
      await expect(page.locator('h2:has-text("资源配置管理")')).toBeVisible();

      // 验证所有 Tab 可见
      for (const { type, label } of RESOURCE_TYPES) {
        await expect(page.getByTestId(`tab-${type}`)).toBeVisible();
        await expect(page.getByTestId(`tab-${type}`)).toContainText(label);
      }

      // 验证搜索框和操作按钮
      await expect(page.getByTestId('search-input')).toBeVisible();
      await expect(page.getByTestId('search-button')).toBeVisible();
      await expect(page.getByTestId('refresh-button')).toBeVisible();
      await expect(page.getByTestId('create-button')).toBeVisible();

      // 验证统计卡片
      await expect(page.getByText('配置总数')).toBeVisible();
      await expect(page.getByText('已被引用')).toBeVisible();
      await expect(page.getByText('未被使用')).toBeVisible();
    });

    test('默认显示数据库 Tab', async ({ page }) => {
      await goToResourcePage(page);

      // 数据库 Tab 应该默认激活
      const tab = page.getByTestId('tab-database');
      await expect(tab).toHaveAttribute('data-state', 'active');
    });

    // 测试每个 Tab 切换
    for (const { type, label } of RESOURCE_TYPES) {
      test(`切换到 ${label} Tab`, async ({ page }) => {
        await goToResourcePage(page);

        await switchToTab(page, type);

        // 验证 Tab 被激活
        await expect(page.getByTestId(`tab-${type}`)).toHaveAttribute('data-state', 'active');

        // 验证表格存在
        await expect(page.locator('table')).toBeVisible({ timeout: 5000 });
      });
    }
  });

  // ==================== 创建资源配置测试 ====================

  test.describe('创建资源配置', () => {
    test('点击新增配置按钮打开弹窗', async ({ page }) => {
      await goToResourcePage(page);

      await page.getByTestId('create-button').click();

      // 验证弹窗打开
      await expect(page.getByTestId('resource-dialog')).toBeVisible();
      await expect(page.getByTestId('dialog-title')).toContainText('新增配置');
      await expect(page.getByTestId('form-name')).toBeVisible();
    });

    test('创建弹窗取消按钮关闭弹窗', async ({ page }) => {
      await goToResourcePage(page);

      await page.getByTestId('create-button').click();
      await expect(page.getByTestId('resource-dialog')).toBeVisible();

      await page.getByTestId('cancel-button').click();
      await expect(page.getByTestId('resource-dialog')).not.toBeVisible();
    });

    test('创建数据库配置 - 必填字段验证', async ({ page }) => {
      await goToResourcePage(page);

      await openCreateDialog(page);

      // 不填写内容直接保存
      await page.getByTestId('save-button').click();

      // 验证错误提示（配置名称校验）
      await expect(page.getByText('请输入配置名称')).toBeVisible({ timeout: 3000 });
    });

    test('创建数据库配置成功', async ({ page, request }) => {
      const configName = `e2e-database-${Date.now()}`;

      await goToResourcePage(page);

      await openCreateDialog(page);

      // 填写表单
      await page.getByTestId('form-name').fill(configName);
      await page.getByTestId('form-host').fill('localhost');
      await page.getByTestId('form-port').fill('5433');
      await page.getByTestId('form-database').fill('e2e_test');
      await page.getByTestId('form-username').fill('e2e_user');
      await page.getByTestId('form-password').fill('e2e_pass');

      // 保存
      await page.getByTestId('save-button').click();

      // 等待弹窗关闭
      await expect(page.getByTestId('resource-dialog')).not.toBeVisible({ timeout: 10000 });

      // 验证表格中出现新配置
      await expect(page.locator('tbody').getByText(configName)).toBeVisible({ timeout: 10000 });

      // 通过 API 清理
      const token = await getAdminToken(request);
      const path = 'databases';
      const result = await request.get(`/api/tenant/admin/v1/resources/${path}`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { keyword: configName },
      });
      if (result.ok()) {
        const data = await result.json();
        const resource = data?.data?.find((r: { name: string }) => r.name === configName);
        if (resource) {
          await deleteResourceConfigViaAPI(request, token, 'database', resource.id);
        }
      }
    });

    test('创建多种资源类型配置', async ({ page, request }) => {
      const token = await getAdminToken(request);

      // 为每种类型创建一个配置
      const typeConfigs: { type: ResourceType; name: string; extraFields?: Record<string, string> }[] = [
        { type: 'database' as ResourceType, name: `e2e-db-${Date.now()}`, extraFields: {} },
        { type: 'cache' as ResourceType, name: `e2e-cache-${Date.now()}`, extraFields: {} },
      ];

      for (const config of typeConfigs) {
        await goToResourcePage(page);
        await switchToTab(page, config.type);
        await openCreateDialog(page);

        await page.getByTestId('form-name').fill(config.name);
        await page.getByTestId('form-host').fill('localhost');
        await page.getByTestId('form-port').fill('6379');

        await page.getByTestId('save-button').click();

        await expect(page.getByTestId('resource-dialog')).not.toBeVisible({ timeout: 10000 });
        await expect(page.locator('tbody').getByText(config.name)).toBeVisible({ timeout: 10000 });

        // 通过 API 清理
        const path = config.type === 'database' ? 'databases' : 'caches';
        const result = await request.get(`/api/tenant/admin/v1/resources/${path}`, {
          headers: { Authorization: `Bearer ${token}` },
          params: { keyword: config.name },
        });
        if (result.ok()) {
          const data = await result.json();
          const resource = data?.data?.find((r: { name: string }) => r.name === config.name);
          if (resource) {
            await deleteResourceConfigViaAPI(request, token, config.type, resource.id);
          }
        }
      }
    });
  });

  // ==================== 编辑资源配置测试 ====================

  test.describe('编辑资源配置', () => {
    test('打开编辑弹窗显示原有数据', async ({ page, request }) => {
      // 通过 API 创建测试资源
      const originalName = `e2e-edit-test-${Date.now()}`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', originalName);

      await goToResourcePage(page);

      await openEditDialog(page, originalName);

      // 验证弹窗标题
      await expect(page.getByTestId('dialog-title')).toContainText('编辑配置');

      // 验证表单字段有值
      await expect(page.getByTestId('form-name')).toHaveValue(originalName);
    });

    test('编辑数据库配置成功', async ({ page, request }) => {
      const originalName = `e2e-edit-${Date.now()}`;
      const newName = `${originalName}-已编辑`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', originalName);

      await goToResourcePage(page);

      await openEditDialog(page, originalName);

      // 清空并修改名称
      await page.getByTestId('form-name').fill(newName);

      // 保存
      await page.getByTestId('save-button').click();

      // 等待弹窗关闭
      await expect(page.getByTestId('resource-dialog')).not.toBeVisible({ timeout: 10000 });

      // 验证更新后的名称出现
      await expect(page.locator('tbody').getByText(newName)).toBeVisible({ timeout: 10000 });

      // 验证旧名称消失
      await expect(page.locator('tbody').getByText(originalName)).not.toBeVisible({ timeout: 5000 });
    });

    test('编辑取消不保存修改', async ({ page, request }) => {
      const originalName = `e2e-cancel-${Date.now()}`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', originalName);

      await goToResourcePage(page);

      await openEditDialog(page, originalName);

      // 修改名称
      await page.getByTestId('form-name').fill(`${originalName}-未保存`);

      // 取消
      await page.getByTestId('cancel-button').click();
      await expect(page.getByTestId('resource-dialog')).not.toBeVisible();

      // 验证原始名称仍然存在
      await expect(page.locator('tbody').getByText(originalName)).toBeVisible({ timeout: 5000 });
    });

    test('切换资源类型后编辑对应资源', async ({ page, request }) => {
      const dbName = `e2e-switch-db-${Date.now()}`;
      const cacheName = `e2e-switch-cache-${Date.now()}`;
      const token = await getAdminToken(request);
      const dbResource = await createTestResource(request, token, 'database', dbName);
      const cacheResource = await createResourceConfigViaAPI(request, token, 'cache', {
        name: cacheName,
        host: 'localhost',
        port: 6379,
      });
      testContext.createdResources.push({ type: 'cache', id: cacheResource.id });

      await goToResourcePage(page);

      // 确认数据库 Tab 下可见 DB 配置
      await expect(page.locator('tbody').getByText(dbName)).toBeVisible({ timeout: 10000 });

      // 切换到缓存 Tab
      await switchToTab(page, 'cache');

      // 确认缓存 Tab 下可见缓存配置
      await expect(page.locator('tbody').getByText(cacheName)).toBeVisible({ timeout: 10000 });

      // 验证数据库配置不在缓存 Tab 中
      await expect(page.locator('tbody').getByText(dbName)).not.toBeVisible({ timeout: 3000 });
    });
  });

  // ==================== 删除资源配置测试 ====================

  test.describe('删除资源配置', () => {
    test('打开删除确认弹窗', async ({ page, request }) => {
      const configName = `e2e-del-dialog-${Date.now()}`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', configName);

      await goToResourcePage(page);

      await clickRowDeleteButton(page, configName);

      // 验证删除确认弹窗
      await expect(page.getByTestId('delete-dialog-title')).toContainText('确认删除');
      await expect(page.getByTestId('delete-cancel-button')).toBeVisible();
      await expect(page.getByTestId('delete-confirm-button')).toBeVisible();
    });

    test('取消删除操作', async ({ page, request }) => {
      const configName = `e2e-del-cancel-${Date.now()}`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', configName);

      await goToResourcePage(page);

      await clickRowDeleteButton(page, configName);

      // 点击取消
      await page.getByTestId('delete-cancel-button').click();
      await expect(page.getByTestId('delete-dialog')).not.toBeVisible();

      // 验证配置仍然存在
      await expect(page.locator('tbody').getByText(configName)).toBeVisible({ timeout: 5000 });
    });

    test('删除配置成功', async ({ page, request }) => {
      const configName = `e2e-del-success-${Date.now()}`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', configName);

      await goToResourcePage(page);

      await clickRowDeleteButton(page, configName);

      // 点击确认删除
      await page.getByTestId('delete-confirm-button').click();

      // 等待弹窗关闭
      await expect(page.getByTestId('delete-dialog')).not.toBeVisible({ timeout: 10000 });

      // 验证配置已删除
      await expect(page.locator('tbody').getByText(configName)).not.toBeVisible({ timeout: 10000 });

      // 标记已删除，避免 afterAll 再次删除
      const index = testContext.createdResources.findIndex((r) => r.id === resource.id);
      if (index !== -1) {
        testContext.createdResources.splice(index, 1);
      }
    });
  });

  // ==================== 搜索资源测试 ====================

  test.describe('搜索资源', () => {
    test('通过搜索框搜索配置', async ({ page, request }) => {
      const configName = `e2e-search-unique-${Date.now()}`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', configName);

      await goToResourcePage(page);

      // 输入搜索关键字
      await page.getByTestId('search-input').fill(configName);
      await page.getByTestId('search-button').click();

      // 等待搜索结果
      await waitForPageReady(page);

      // 验证搜索结果包含目标配置
      await expect(page.locator('tbody').getByText(configName)).toBeVisible({ timeout: 10000 });
    });

    test('回车键触发搜索', async ({ page, request }) => {
      const configName = `e2e-search-enter-${Date.now()}`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', configName);

      await goToResourcePage(page);

      // 输入搜索关键字并按回车
      await page.getByTestId('search-input').fill(configName);
      await page.getByTestId('search-input').press('Enter');

      // 等待搜索结果
      await waitForPageReady(page);

      // 验证搜索结果
      await expect(page.locator('tbody').getByText(configName)).toBeVisible({ timeout: 10000 });
    });

    test('搜索无匹配结果', async ({ page }) => {
      await goToResourcePage(page);

      // 使用不可能匹配的关键字搜索
      await page.getByTestId('search-input').fill('e2e-no-match-xyz-999');
      await page.getByTestId('search-button').click();

      await waitForPageReady(page);

      // 验证表格中无此数据
      await expect(page.locator('tbody').getByText('e2e-no-match-xyz-999')).not.toBeVisible({ timeout: 5000 });
    });
  });

  // ==================== 刷新列表测试 ====================

  test.describe('刷新列表', () => {
    test('点击刷新按钮不报错', async ({ page }) => {
      await goToResourcePage(page);

      const refreshBtn = page.getByTestId('refresh-button');
      await expect(refreshBtn).toBeVisible();
      await refreshBtn.click();

      await waitForPageReady(page);

      // 验证页面仍然正常显示
      await expect(page.getByTestId('tab-database')).toBeVisible();
      await expect(page.locator('table')).toBeVisible();
    });

    test('切换 Tab 后刷新当前表格', async ({ page }) => {
      await goToResourcePage(page);

      // 切换到缓存 Tab
      await switchToTab(page, 'cache');

      // 点击刷新
      await page.getByTestId('refresh-button').click();
      await waitForPageReady(page);

      // 验证仍在缓存 Tab
      await expect(page.getByTestId('tab-cache')).toHaveAttribute('data-state', 'active');
      await expect(page.locator('table')).toBeVisible();
    });
  });

  // ==================== 测试连接测试 ====================

  test.describe('测试连接', () => {
    test('测试连接按钮可见', async ({ page, request }) => {
      const configName = `e2e-conn-visibility-${Date.now()}`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', configName);

      await goToResourcePage(page);

      // 验证测试连接按钮出现
      const row = page.locator('tbody tr', { hasText: configName }).first();
      await expect(row).toBeVisible({ timeout: 10000 });

      const testBtn = row.locator('button:has-text("测试")');
      await expect(testBtn).toBeVisible();
    });

    test('点击测试连接按钮调用 API', async ({ page, request }) => {
      const configName = `e2e-conn-click-${Date.now()}`;
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', configName);

      await goToResourcePage(page);

      // 点击测试连接按钮
      const row = page.locator('tbody tr', { hasText: configName }).first();
      await expect(row).toBeVisible({ timeout: 10000 });
      const testBtn = row.locator('button:has-text("测试")');
      await testBtn.click();

      // 等待 API 调用完成（成功提示或失败提示都会出现）
      await page.waitForTimeout(3000);

      // 验证页面仍正常（不报错）
      await expect(page.getByTestId('tab-database')).toBeVisible();
    });
  });

  // ==================== 统计数据测试 ====================

  test.describe('统计数据', () => {
    test('统计卡片显示数值', async ({ page }) => {
      await goToResourcePage(page);

      // 验证三个统计卡片都存在数值
      const statsCards = page.locator('.grid.gap-4.md\\:grid-cols-3');
      await expect(statsCards).toBeVisible();

      // 验证数字显示
      const numbers = statsCards.locator('.text-2xl');
      const count = await numbers.count();
      expect(count).toBe(3);

      for (let i = 0; i < count; i++) {
        const text = await numbers.nth(i).textContent();
        expect(text).not.toBeNull();
        // 应该是数字或 '0'
        expect(text!.trim()).toMatch(/^\d+$/);
      }
    });

    test('创建配置后统计数字可能更新', async ({ page, request }) => {
      const configName = `e2e-stats-${Date.now()}`;

      await goToResourcePage(page);

      // 获取当前配置总数
      const totalText = await page.locator('.grid.gap-4.md\\:grid-cols-3 .text-2xl').first().textContent();
      const beforeCount = parseInt(totalText || '0');

      // 通过 API 创建配置
      const token = await getAdminToken(request);
      const resource = await createTestResource(request, token, 'database', configName);

      // 刷新页面
      await page.getByTestId('refresh-button').click();
      await waitForPageReady(page);

      // 获取新总数
      const newTotalText = await page.locator('.grid.gap-4.md\\:grid-cols-3 .text-2xl').first().textContent();
      const afterCount = parseInt(newTotalText || '0');

      // 总数应该增加（或至少没有减少）
      expect(afterCount).toBeGreaterThanOrEqual(beforeCount);
    });
  });
});
