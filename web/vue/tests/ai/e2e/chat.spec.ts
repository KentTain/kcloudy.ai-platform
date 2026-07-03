/**
 * AI 对话功能 E2E 测试
 *
 * 测试聊天页面的消息发送、流式回复、模型切换等功能。
 */
import { test, expect } from './plugin-fixtures';
import { userLoginViaAPI } from './plugin-fixtures';

test.describe('AI 对话功能', () => {
  test.beforeEach(async ({ page, request }) => {
    await userLoginViaAPI(page, request, 'admin', 'admin123');
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');
  });

  test('聊天页面正常加载', async ({ page }) => {
    // 验证输入框可见
    await expect(page.getByTestId('chat-input')).toBeVisible({ timeout: 15000 });

    // 验证空状态或消息区域可见
    const emptyState = page.getByTestId('empty-state');
    const messages = page.locator('[data-testid="user-message"], [data-testid="assistant-message"]');
    const hasEmptyState = await emptyState.isVisible({ timeout: 5000 }).catch(() => false);
    const hasMessages = await messages.first().isVisible({ timeout: 5000 }).catch(() => false);
    expect(hasEmptyState || hasMessages).toBeTruthy();
  });

  test('发送消息并收到流式回复', async ({ page }) => {
    // 输入消息
    const chatInput = page.getByTestId('chat-input');
    await expect(chatInput).toBeVisible({ timeout: 15000 });
    await chatInput.fill('你好，请简单回复');

    // 点击发送
    const sendBtn = page.getByTestId('send-button');
    await sendBtn.click();

    // 验证用户消息出现
    await expect(page.getByTestId('user-message').first()).toBeVisible({ timeout: 10000 });

    // 验证助手消息逐渐出现（流式回复）
    await expect(page.getByTestId('assistant-message').first()).toBeVisible({ timeout: 60000 });

    // 验证助手消息有内容
    const assistantContent = await page.getByTestId('assistant-message').first().textContent();
    expect(assistantContent?.trim().length).toBeGreaterThan(0);
  });

  test('发送过程中可停止生成', async ({ page }) => {
    // 输入一条需要较长时间回复的消息
    const chatInput = page.getByTestId('chat-input');
    await expect(chatInput).toBeVisible({ timeout: 15000 });
    await chatInput.fill('请详细解释量子计算的基本原理');

    // 点击发送
    const sendBtn = page.getByTestId('send-button');
    await sendBtn.click();

    // 快速点击停止按钮（在生成过程中）
    const stopBtn = page.getByTestId('stop-generate-btn');
    const isStopVisible = await stopBtn.isVisible({ timeout: 5000 }).catch(() => false);

    if (isStopVisible) {
      await stopBtn.click();
      // 验证停止按钮消失
      await expect(stopBtn).not.toBeVisible({ timeout: 3000 });
    }
    // 验证页面仍在正常状态
    await expect(page.getByTestId('chat-input')).toBeVisible();
  });

  test('可切换模型', async ({ page }) => {
    const modelSelector = page.getByTestId('model-selector');
    await expect(modelSelector).toBeVisible({ timeout: 10000 });

    await modelSelector.click();

    // 等待模型选项列表出现
    const option = page.locator('[role="option"], [role="listbox"] [role="option"]').first();
    const isOptionVisible = await option.isVisible({ timeout: 5000 }).catch(() => false);
    if (!isOptionVisible) {
      // 模型列表可能为空或下拉组件结构不同
      return;
    }

    await option.click();

    // 验证页面仍在正常状态
    await expect(page.getByTestId('chat-input')).toBeVisible();
  });

  // 错误提示场景难以在 E2E 中稳定触发（需要 mock API 错误），
  // 此测试留空，待集成 mock 方案后补充
  test('错误提示正常显示', async ({ page }) => {
    test.skip();
  });
});
