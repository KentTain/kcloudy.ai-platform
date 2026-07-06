// tests/ai/e2e/phase2-extension.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Phase 2 E2E', () => {
  test('user can submit feedback', async ({ page }) => {
    await page.goto('/ai')

    // 发送消息
    await page.getByTestId('chat-input').fill('测试问题')
    await page.getByTestId('send-button').click()

    // 等待回复
    await page.waitForSelector('[data-testid="assistant-message"]', {
      timeout: 30000,
    })

    // 点击👍按钮
    const thumbsUp = page.locator('[data-testid="thumbs-up"]').first()
    await thumbsUp.click()

    // 验证按钮高亮
    await expect(thumbsUp).toHaveClass(/text-green-500/)
  })

  test('user can preview PDF file', async ({ page }) => {
    await page.goto('/ai')

    // 上传 PDF 文件（需要 mock 或真实文件）
    // ...

    // 点击文件预览
    await page.locator('[data-testid="file-attachment"]').first().click()

    // 验证 PDF 查看器显示
    await expect(page.locator('[data-testid="pdf-viewer"]')).toBeVisible()
  })

  test('user can sort table data', async ({ page }) => {
    await page.goto('/ai')

    // 发送需要返回表格的问题
    await page.getByTestId('chat-input').fill('查询用户列表')
    await page.getByTestId('send-button').click()

    // 等待表格显示
    await page.waitForSelector('table', { timeout: 30000 })

    // 点击表头排序
    const header = page.locator('th').first()
    await header.click()

    // 验证排序图标显示
    await expect(page.locator('.chevron-down-icon')).toBeVisible()
  })
})
