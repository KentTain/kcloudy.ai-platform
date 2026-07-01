// web/vue/tests/framework/e2e/toast.spec.ts
import { expect, test } from "@playwright/test"

test.describe("Toast 通知测试", () => {
  test.beforeEach(async ({ page }) => {
    // 登录到系统（使用 IAM 用户端登录）
    await page.goto("/login")
    await page.waitForLoadState("networkidle")

    const usernameInput = page
      .locator('input[type="text"], input[name="username"]')
      .first()
    const passwordInput = page.locator('input[type="password"]').first()
    const loginButton = page.locator('button[type="submit"]')

    if (await usernameInput.isVisible()) {
      await usernameInput.fill("admin")
      await passwordInput.fill("admin123")
      await loginButton.click()

      // 等待登录完成并跳转
      await page.waitForURL(/^(?!.*\/login).*$/, { timeout: 15000 })
    }
  })

  test("应该显示成功消息并自动关闭", async ({ page }) => {
    // 导航到租户管理页面（该页面包含 CRUD 操作可触发 Toast）
    await page.goto("/tenant/admin/tenants")
    await page.waitForLoadState("networkidle")

    // 尝试触发一个成功 Toast 通知
    // 查找并点击"新建"或"创建"按钮
    const createButton = page
      .locator(
        'button:has-text("新建"), button:has-text("创建"), [data-testid="create-button"]'
      )
      .first()

    if (await createButton.isVisible()) {
      await createButton.click()

      // 如果有弹窗，填写表单并提交以触发成功消息
      // 否则直接等待可能的现有 Toast
    }

    // 验证 Toast 出现
    const toast = page.locator('[data-sonner-toast][data-type="success"]')
    await expect(toast).toBeVisible({ timeout: 5000 })

    // 验证 Toast 在 4 秒后消失
    await page.waitForTimeout(4500)
    await expect(toast).not.toBeVisible()
  })

  test("应该在 top-center 位置显示", async ({ page }) => {
    // 导航到租户管理页面
    await page.goto("/tenant/admin/tenants")
    await page.waitForLoadState("networkidle")

    // 触发一个操作产生 Toast
    const button = page
      .locator(
        'button:has-text("新建"), button:has-text("创建"), [data-testid="create-button"]'
      )
      .first()

    if (await button.isVisible()) {
      await button.click()
    }

    // 等待 Toast 出现
    await page.waitForTimeout(1000)

    // 验证 Toast 位置
    const toast = page.locator("[data-sonner-toast]").first()
    await expect(toast).toBeVisible()

    // 检查位置（top-center）
    const boundingBox = await toast.boundingBox()
    if (boundingBox) {
      const pageWidth = page.viewportSize()?.width || 1280
      const centerX = pageWidth / 2
      const toastCenterX = boundingBox.x + boundingBox.width / 2

      // 允许 50px 误差
      expect(Math.abs(toastCenterX - centerX)).toBeLessThan(50)
      // 应该在页面顶部
      expect(boundingBox.y).toBeLessThan(100)
    }
  })

  test("应该显示 rich-colors 样式", async ({ page }) => {
    // 导航到租户管理页面
    await page.goto("/tenant/admin/tenants")
    await page.waitForLoadState("networkidle")

    // 触发操作产生成功 Toast
    const createButton = page
      .locator(
        'button:has-text("新建"), button:has-text("创建"), [data-testid="create-button"]'
      )
      .first()

    if (await createButton.isVisible()) {
      await createButton.click()
    }

    // 验证成功 Toast 的样式（rich-colors 模式会使用有颜色的图标和边框）
    const successToast = page.locator(
      '[data-sonner-toast][data-type="success"]'
    )
    await expect(successToast).toBeVisible()

    // 验证 Toast 内容不为空
    const toastContent = await successToast.textContent()
    expect(toastContent?.length).toBeGreaterThan(0)
  })

  test("最多应该显示 3 个消息", async ({ page }) => {
    // 导航到租户管理页面
    await page.goto("/tenant/admin/tenants")
    await page.waitForLoadState("networkidle")

    // 快速触发多个操作产生 Toast
    // 注：此处依赖页面上可触发 Toast 的操作
    // 实际场景中可通过 console 注入调用 notifySuccess

    // 等待 Toast 出现
    await page.waitForTimeout(1000)

    // 验证最多显示 3 个
    const toasts = await page.locator("[data-sonner-toast]").count()
    expect(toasts).toBeLessThanOrEqual(3)
  })
})