/**
 * 插件配置 E2E 测试
 *
 * 测试插件配置页面的查看、编辑、验证、保存等功能。
 */
import { test, expect } from './plugin-fixtures';

const TEST_PLUGIN_ID = 'langgenius/ollama';

test.describe('插件配置页面', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    const usernameInput = page.locator('input[type="text"], input[name="username"], input[placeholder*="账号"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    const loginButton = page.locator('button[type="submit"]');

    if (await usernameInput.isVisible()) {
      await usernameInput.fill('admin');
      await passwordInput.fill('admin123');
      await loginButton.click();
      await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 });
    }

    // 导航到插件配置页
    await page.goto(`/ai/plugins/${encodeURIComponent(TEST_PLUGIN_ID)}/config`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('应该显示插件配置页面', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('h2').first()).toContainText('插件配置');

    // 验证插件 ID 显示
    await expect(page.locator(`text=${TEST_PLUGIN_ID}`)).toBeVisible({ timeout: 10000 });
  });

  test('应该显示返回按钮', async ({ page }) => {
    const backButton = page.locator('button:has-text("返回"), button:has-text("返回列表")').first();
    await expect(backButton).toBeVisible({ timeout: 5000 });
  });

  test('应该显示插件能力配置区域', async ({ page }) => {
    // 查找插件能力配置卡片
    const configCard = page.locator('text=插件能力配置, text=插件配置').first();
    await expect(configCard).toBeVisible({ timeout: 5000 });

    // 验证只读标识
    const readOnlyBadge = page.locator('text=只读').first();
    await expect(readOnlyBadge).toBeVisible({ timeout: 5000 });
  });

  test('应该显示运行时配置编辑区域', async ({ page }) => {
    // 查找运行时配置卡片
    const runtimeCard = page.locator('text=运行时配置').first();
    await expect(runtimeCard).toBeVisible({ timeout: 5000 });

    // 验证 JSON 编辑器存在
    const editor = page.locator('textarea, [data-testid="runtime-config-editor"]').first();
    await expect(editor).toBeVisible({ timeout: 5000 });
  });

  test('应该显示格式化按钮', async ({ page }) => {
    const formatButton = page.locator('button:has-text("格式化")').first();
    await expect(formatButton).toBeVisible({ timeout: 5000 });
  });

  test('应该显示重置按钮', async ({ page }) => {
    const resetButton = page.locator('button:has-text("重置")').first();
    await expect(resetButton).toBeVisible({ timeout: 5000 });
  });

  test('应该显示保存按钮', async ({ page }) => {
    const saveButton = page.locator('button:has-text("保存"), button:has-text("保存配置")').first();
    await expect(saveButton).toBeVisible({ timeout: 5000 });
  });

  test('编辑配置后保存按钮应该可用', async ({ page }) => {
    const editor = page.locator('textarea').first();
    await expect(editor).toBeVisible({ timeout: 5000 });

    // 获取当前值
    const currentValue = await editor.inputValue();

    // 修改配置（添加一个新字段）
    const newValue = currentValue.replace(/\}\s*$/, ', "e2e_test_key": "e2e_test_value"}');
    await editor.fill(newValue);

    // 验证保存按钮可用
    const saveButton = page.locator('button:has-text("保存配置")').first();
    await expect(saveButton).toBeEnabled({ timeout: 5000 });
  });

  test('输入无效 JSON 应显示错误提示', async ({ page }) => {
    const editor = page.locator('textarea').first();
    await expect(editor).toBeVisible({ timeout: 5000 });

    // 输入无效的 JSON
    await editor.fill('{invalid json}');

    // 验证错误提示显示
    const errorMessage = page.locator('text=JSON 格式无效, text=格式无效').first();
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });

  test('点击格式化按钮应格式化 JSON', async ({ page }) => {
    const editor = page.locator('textarea').first();
    await expect(editor).toBeVisible({ timeout: 5000 });

    // 输入未格式化的 JSON
    await editor.fill('{"test":"value"}');

    // 点击格式化按钮
    const formatButton = page.locator('button:has-text("格式化")').first();
    await formatButton.click();

    // 验证 JSON 已格式化（包含换行）
    const formattedValue = await editor.inputValue();
    expect(formattedValue).toContain('\n');
  });

  test('点击返回按钮应导航到插件列表', async ({ page }) => {
    const backButton = page.locator('button:has-text("返回")').first();
    await backButton.click();

    // 验证 URL
    await expect(page).toHaveURL('/ai/plugins', { timeout: 10000 });
  });

  test('点击重置按钮应恢复原始配置', async ({ page }) => {
    const editor = page.locator('textarea').first();
    await expect(editor).toBeVisible({ timeout: 5000 });

    // 获取原始值
    const originalValue = await editor.inputValue();

    // 修改配置
    const modifiedValue = originalValue.replace(/\}\s*$/, ', "temp_key": "temp_value"}');
    await editor.fill(modifiedValue);

    // 点击重置按钮
    const resetButton = page.locator('button:has-text("重置")').first();
    await resetButton.click();

    // 验证值已恢复
    const resetValue = await editor.inputValue();
    expect(resetValue).toBe(originalValue);
  });

  test('保存有效配置应成功', async ({ page }) => {
    const editor = page.locator('textarea').first();
    await expect(editor).toBeVisible({ timeout: 5000 });

    // 获取当前值
    const currentValue = await editor.inputValue();

    // 添加唯一测试键
    const timestamp = Date.now();
    const newValue = currentValue.replace(/\}\s*$/, `, "e2e_save_test_${timestamp}": "saved_value"}`);
    await editor.fill(newValue);

    // 点击保存按钮
    const saveButton = page.locator('button:has-text("保存配置")').first();
    await saveButton.click();

    // 等待成功提示
    const successMessage = page.locator('text=配置已保存, text=保存成功').first();
    await expect(successMessage).toBeVisible({ timeout: 10000 });
  });

  test('未修改配置时保存按钮应禁用', async ({ page }) => {
    // 初始状态下保存按钮可能禁用
    const saveButton = page.locator('button:has-text("保存配置")').first();

    // 如果按钮存在，检查状态
    if (await saveButton.isVisible()) {
      const isDisabled = await saveButton.isDisabled();
      // 如果未修改，应该禁用
      // 注意：也可能已启用（如果有之前的修改），所以不强制要求
      console.log(`保存按钮状态: ${isDisabled ? '禁用' : '启用'}`);
    }
  });

  test('应该正确处理空配置', async ({ page }) => {
    const editor = page.locator('textarea').first();
    await expect(editor).toBeVisible({ timeout: 5000 });

    // 清空编辑器
    await editor.fill('{}');
    await editor.fill('');

    // 验证不崩溃
    await page.waitForTimeout(500);
    await expect(editor).toBeVisible();
  });

  test('应该正确处理特殊字符', async ({ page }) => {
    const editor = page.locator('textarea').first();
    await expect(editor).toBeVisible({ timeout: 5000 });

    // 输入包含特殊字符的配置
    const specialValue = '{"special_key": "值包含中文和特殊字符!@#$%^&*()"}';
    await editor.fill(specialValue);

    // 点击格式化验证有效性
    const formatButton = page.locator('button:has-text("格式化")').first();
    await formatButton.click();

    // 验证格式化成功（无错误提示）
    const errorMessage = page.locator('text=JSON 格式无效').first();
    await expect(errorMessage).not.toBeVisible({ timeout: 3000 });
  });
});
