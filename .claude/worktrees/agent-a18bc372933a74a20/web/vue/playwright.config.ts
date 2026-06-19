import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 测试配置
 *
 * 使用方式：
 * - pnpm test:e2e              # 运行所有 E2E 测试
 * - pnpm test:e2e tests/ai/    # 运行 AI 模块 E2E 测试
 * - pnpm test:e2e tests/iam/   # 运行 IAM 模块 E2E 测试（如有）
 * - pnpm test:e2e:ui           # UI 模式运行
 */
export default defineConfig({
  testDir: './tests',
  testMatch: '**/e2e/*.spec.ts',
  outputDir: './tests/test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { outputFolder: './tests/playwright-report' }]],
  timeout: 60000,
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
