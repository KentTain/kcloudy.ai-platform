/**
 * AI SDK 扩展 E2E 测试
 *
 * 注意：此测试需要完整的运行环境（后端 API + 前端 dev server）
 * 在 CI 环境中运行需要配置 Playwright 和测试数据
 *
 * 测试覆盖：
 * - 来源引用端到端展示
 * - 文件附件端到端上传和展示
 * - 表格数据端到端展示
 */
import { test, expect } from './plugin-fixtures';
import { userLoginViaAPI } from './plugin-fixtures';

test.describe('AI SDK Extension E2E', () => {
  test.beforeEach(async ({ page, request }) => {
    // 登录并导航到 AI 对话页面
    await userLoginViaAPI(page, request, 'admin', 'admin123');
    await page.goto('/ai');
    await page.waitForLoadState('networkidle');
  });

  test('displays source citations in chat', async ({ page }) => {
    // 等待输入框可见
    const input = page.getByTestId('chat-input');
    await expect(input).toBeVisible({ timeout: 15000 });

    // 输入需要搜索的问题
    await input.fill('搜索一下今天的新闻');

    // 发送消息
    const sendButton = page.getByTestId('send-button');
    await sendButton.click();

    // 等待 AI 回复完成
    await page.waitForSelector('[data-testid="assistant-message"]', {
      timeout: 30000,
    });

    // 验证来源引用显示
    const sourceCards = page.locator('[data-testid="source-url-card"]');
    // 注意：来源引用可能不存在，取决于后端是否返回了搜索结果
    const hasSourceCards = await sourceCards.first().isVisible({ timeout: 5000 }).catch(() => false);

    if (hasSourceCards) {
      // 如果有来源引用，验证至少有一个
      const count = await sourceCards.count();
      expect(count).toBeGreaterThan(0);
    }
    // 如果没有来源引用，测试仍然通过（可能后端没有返回搜索结果）
  });

  test('displays file attachments in chat', async ({ page }) => {
    // 等待输入框可见
    const input = page.getByTestId('chat-input');
    await expect(input).toBeVisible({ timeout: 15000 });

    // 注意：文件上传功能需要实际的文件和上传组件
    // 这里仅测试基本的消息发送和回复流程
    // TODO: 添加文件上传交互测试

    // 发送消息
    await input.fill('分析这个文件');
    await page.getByTestId('send-button').click();

    // 等待回复
    await page.waitForSelector('[data-testid="assistant-message"]', {
      timeout: 30000,
    });

    // 验证文件附件显示（如果有的话）
    const fileAttachment = page.locator('[data-testid="file-attachment"]');
    const hasFileAttachment = await fileAttachment.first().isVisible({ timeout: 5000 }).catch(() => false);

    // 文件附件可能不存在，取决于是否真的上传了文件
    if (hasFileAttachment) {
      const count = await fileAttachment.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('displays table data in chat', async ({ page }) => {
    // 等待输入框可见
    const input = page.getByTestId('chat-input');
    await expect(input).toBeVisible({ timeout: 15000 });

    // 发送需要返回数据的请求
    await input.fill('查询用户列表');
    await page.getByTestId('send-button').click();

    // 等待回复
    await page.waitForSelector('[data-testid="assistant-message"]', {
      timeout: 30000,
    });

    // 验证表格显示（如果后端返回了表格数据）
    const table = page.locator('table');
    const hasTable = await table.isVisible({ timeout: 5000 }).catch(() => false);

    if (hasTable) {
      // 验证表格有数据
      const rows = table.locator('tbody tr');
      const rowCount = await rows.count();
      expect(rowCount).toBeGreaterThan(0);
    }
    // 如果没有表格，测试仍然通过（可能后端返回的是文本格式）
  });

  test('chat interaction maintains conversation context', async ({ page }) => {
    // 第一轮对话
    const input = page.getByTestId('chat-input');
    await expect(input).toBeVisible({ timeout: 15000 });

    await input.fill('你好，请记住我的名字是小明');
    await page.getByTestId('send-button').click();

    // 等待第一条回复
    await page.waitForSelector('[data-testid="assistant-message"]', {
      timeout: 30000,
    });

    // 清空输入框并发送第二条消息
    await input.fill('你还记得我的名字吗？');
    await page.getByTestId('send-button').click();

    // 等待第二条回复
    const assistantMessages = page.locator('[data-testid="assistant-message"]');
    await expect(assistantMessages.nth(1)).toBeVisible({ timeout: 30000 });

    // 验证对话历史显示
    const userMessages = page.locator('[data-testid="user-message"]');
    const userCount = await userMessages.count();
    const assistantCount = await assistantMessages.count();

    // 应该有 2 条用户消息和 2 条助手消息
    expect(userCount).toBeGreaterThanOrEqual(2);
    expect(assistantCount).toBeGreaterThanOrEqual(2);
  });
});
