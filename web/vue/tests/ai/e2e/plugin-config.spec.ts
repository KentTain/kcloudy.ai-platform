/**
 * 插件配置 E2E 测试
 *
 * 测试插件配置页面的查看、编辑、验证、保存、测试连接等功能。
 */
import { test, expect } from './plugin-fixtures';
import { userLoginViaAPI } from './plugin-fixtures';

const TEST_PLUGIN_ID = 'langgenius/ollama';

test.describe('插件配置页面', () => {
  test.beforeEach(async ({ page, request }) => {
    await userLoginViaAPI(page, request, 'admin', 'admin123');
    await page.goto(`/ai/plugins/${encodeURIComponent(TEST_PLUGIN_ID)}/config`);
    await page.waitForLoadState('networkidle');
  });

  test('应该显示插件配置页面', async ({ page }) => {
    await expect(page.getByTestId('plugin-config-page')).toBeVisible({ timeout: 15000 });
  });

  test('应该显示返回按钮', async ({ page }) => {
    await expect(page.getByTestId('back-btn')).toBeVisible({ timeout: 10000 });
  });

  test('应该显示格式化按钮', async ({ page }) => {
    await expect(page.getByTestId('format-btn')).toBeVisible({ timeout: 10000 });
  });

  test('应该显示重置按钮', async ({ page }) => {
    await expect(page.getByTestId('reset-btn')).toBeVisible({ timeout: 10000 });
  });

  test('应该显示保存按钮', async ({ page }) => {
    await expect(page.getByTestId('save-btn')).toBeVisible({ timeout: 10000 });
  });

  test('应该显示运行时配置编辑器', async ({ page }) => {
    await expect(page.getByTestId('runtime-config-editor')).toBeVisible({ timeout: 10000 });
  });

  test('编辑配置后保存按钮应该可用', async ({ page }) => {
    const editor = page.getByTestId('runtime-config-editor');
    await expect(editor).toBeVisible({ timeout: 10000 });

    const currentValue = await editor.inputValue();
    const newValue = currentValue.replace(/\}\s*$/, ', "e2e_test_key": "e2e_test_value"}');
    await editor.fill(newValue);

    const saveBtn = page.getByTestId('save-btn');
    await expect(saveBtn).toBeEnabled({ timeout: 5000 });
  });

  test('输入无效 JSON 应显示错误提示', async ({ page }) => {
    const editor = page.getByTestId('runtime-config-editor');
    await expect(editor).toBeVisible({ timeout: 10000 });

    await editor.fill('{invalid json}');

    const errorMessage = page.locator('text=JSON 格式无效');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });

  test('点击格式化按钮应格式化 JSON', async ({ page }) => {
    const editor = page.getByTestId('runtime-config-editor');
    await expect(editor).toBeVisible({ timeout: 10000 });

    await editor.fill('{"test":"value"}');

    const formatBtn = page.getByTestId('format-btn');
    await formatBtn.click();

    const formattedValue = await editor.inputValue();
    expect(formattedValue).toContain('\n');
  });

  test('点击重置按钮应恢复原始配置', async ({ page }) => {
    const editor = page.getByTestId('runtime-config-editor');
    await expect(editor).toBeVisible({ timeout: 10000 });

    const originalValue = await editor.inputValue();
    await editor.fill('{"modified": true}');

    const resetBtn = page.getByTestId('reset-btn');
    await expect(resetBtn).toBeEnabled();
    await resetBtn.click();

    const resetValue = await editor.inputValue();
    expect(resetValue).toBe(originalValue);
  });

  test('页面不应崩溃', async ({ page }) => {
    await expect(page.getByTestId('plugin-config-page')).toBeVisible();
  });

  // ===========================================================================
  // 测试连接功能
  // ===========================================================================

  test('测试连接按钮存在', async ({ page }) => {
    await expect(page.getByTestId('test-connection-btn')).toBeVisible({ timeout: 10000 });
  });

  test('点击测试连接应显示结果弹窗', async ({ page }) => {
    const testBtn = page.getByTestId('test-connection-btn');
    await expect(testBtn).toBeVisible({ timeout: 10000 });

    await testBtn.click();

    // 等待 API 响应和弹窗出现
    await expect(page.getByTestId('test-result-dialog')).toBeVisible({ timeout: 30000 });
  });

  test('测试结果弹窗可关闭', async ({ page }) => {
    const testBtn = page.getByTestId('test-connection-btn');
    await expect(testBtn).toBeVisible({ timeout: 10000 });

    await testBtn.click();
    await expect(page.getByTestId('test-result-dialog')).toBeVisible({ timeout: 30000 });

    // 点击关闭按钮
    const closeBtn = page.getByTestId('test-result-dialog').locator('button:has-text("关闭")');
    await closeBtn.click();

    // 验证弹窗消失
    await expect(page.getByTestId('test-result-dialog')).not.toBeVisible({ timeout: 5000 });
  });
});
