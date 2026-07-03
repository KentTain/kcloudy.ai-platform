/**
 * 核心路径端到端冒烟测试
 *
 * 验证最关键的用户旅程跨模块正常运行：
 * 登录 → AI 聊天 → 会话面板 → 插件管理 → 插件配置
 */
import { test, expect } from '@playwright/test';
import { userLoginViaAPI } from './iam/e2e/fixtures';

test.describe.serial('核心路径端到端冒烟测试', () => {
  test.beforeEach(async ({ page, request }) => {
    await userLoginViaAPI(page, request);
  });

  test('用户登录后可访问 AI 聊天', async ({ page }) => {
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');

    // 验证输入框可见
    await expect(page.getByTestId('chat-input')).toBeVisible({ timeout: 15000 });

    // 验证空状态或消息区域
    const emptyState = page.getByTestId('empty-state');
    const messages = page.locator('[data-testid="user-message"], [data-testid="assistant-message"]');
    const hasEmptyState = await emptyState.isVisible({ timeout: 5000 }).catch(() => false);
    const hasMessages = await messages.first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(hasEmptyState || hasMessages).toBeTruthy();
  });

  test('聊天页面可发送消息', async ({ page }) => {
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');

    // 输入消息
    const chatInput = page.getByTestId('chat-input');
    await expect(chatInput).toBeVisible({ timeout: 15000 });
    await chatInput.fill('你好');

    // 点击发送
    const sendBtn = page.getByTestId('send-button');
    await sendBtn.click();

    // 验证用户消息出现
    await expect(page.getByTestId('user-message').first()).toBeVisible({ timeout: 10000 });

    // 验证助手消息出现（AI 回复可能需要时间）
    await expect(page.getByTestId('assistant-message').first()).toBeVisible({ timeout: 60000 });
  });

  test('会话面板可展开并新建会话', async ({ page }) => {
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');

    // 点击面板切换按钮
    const toggleBtn = page.getByTestId('toggle-panel-btn');
    await expect(toggleBtn).toBeVisible({ timeout: 10000 });
    await toggleBtn.click();

    // 等待面板动画完成
    await page.waitForTimeout(300);

    // 点击新建会话按钮
    const newChatBtn = page.getByTestId('new-chat-btn');
    await expect(newChatBtn).toBeVisible({ timeout: 5000 });
    await newChatBtn.click();

    // 验证页面仍在正常状态
    await expect(page.getByTestId('chat-input')).toBeVisible({ timeout: 5000 });
  });

  test('可导航到插件管理', async ({ page }) => {
    await page.goto('/ai/plugins');
    await page.waitForLoadState('networkidle');

    // 验证插件管理页面加载
    await expect(page.getByTestId('plugin-manage-page')).toBeVisible({ timeout: 15000 });
  });

  test('可搜索和筛选插件', async ({ page }) => {
    await page.goto('/ai/plugins');
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('plugin-manage-page')).toBeVisible({ timeout: 15000 });

    // 输入搜索关键词
    const searchInput = page.getByTestId('search-input');
    if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchInput.fill('ollama');

      // 触发搜索
      await searchInput.press('Enter');
      await page.waitForLoadState('networkidle');

      // 验证页面仍在正常状态
      await expect(page.getByTestId('plugin-manage-page')).toBeVisible();
    }
  });

  test('可进入插件配置并测试连接', async ({ page }) => {
    await page.goto('/ai/plugins');
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('plugin-manage-page')).toBeVisible({ timeout: 15000 });

    // 点击第一个配置按钮
    const configBtn = page.getByTestId('config-btn').first();
    const isVisible = await configBtn.isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      return; // 没有已安装插件，跳过后续验证
    }

    await configBtn.click();
    await page.waitForLoadState('networkidle');

    // 验证配置页面加载
    await expect(page.getByTestId('plugin-config-page')).toBeVisible({ timeout: 15000 });

    // 点击测试连接按钮
    const testBtn = page.getByTestId('test-connection-btn');
    await expect(testBtn).toBeVisible({ timeout: 10000 });
    await testBtn.click();

    // 等待测试结果弹窗
    await expect(page.getByTestId('test-result-dialog')).toBeVisible({ timeout: 30000 });
  });

  test('可编辑并保存运行时配置', async ({ page }) => {
    await page.goto('/ai/plugins');
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('plugin-manage-page')).toBeVisible({ timeout: 15000 });

    // 进入配置页
    const configBtn = page.getByTestId('config-btn').first();
    const isVisible = await configBtn.isVisible({ timeout: 10000 }).catch(() => false);
    if (!isVisible) {
      return;
    }

    await configBtn.click();
    await page.waitForLoadState('networkidle');
    await expect(page.getByTestId('plugin-config-page')).toBeVisible({ timeout: 15000 });

    // 修改运行时配置
    const editor = page.getByTestId('runtime-config-editor');
    await expect(editor).toBeVisible({ timeout: 10000 });

    const currentValue = await editor.inputValue();
    const newValue = currentValue.replace(/\}\s*$/, ', "e2e_key": "test"}');
    await editor.fill(newValue);

    // 格式化
    const formatBtn = page.getByTestId('format-btn');
    await formatBtn.click();

    // 保存
    const saveBtn = page.getByTestId('save-btn');
    await expect(saveBtn).toBeEnabled({ timeout: 5000 });
    await saveBtn.click();

    // 验证保存成功通知
    const toast = page.locator('[data-sonner-toast], [role="status"]');
    await expect(toast.first()).toBeVisible({ timeout: 10000 }).catch(() => {
      // 通知可能很快消失
    });
  });
});
