import { defineConfig, devices } from '@playwright/test';
import os from 'os';

/**
 * Playwright E2E 测试配置
 *
 * 使用方式：
 * - pnpm test:e2e              # 运行所有 E2E 测试
 * - pnpm test:e2e tests/ai/    # 运行 AI 模块 E2E 测试
 * - pnpm test:e2e tests/iam/   # 运行 IAM 模块 E2E 测试（如有）
 * - pnpm test:e2e:ui           # UI 模式运行
 *
 * 环境变量：
 * - PLAYWRIGHT_BROWSERS_PATH   浏览器安装路径，如 /ms-playwright/
 * - E2E_BASE_URL               前端服务地址，默认 http://localhost:5173
 * - E2E_WORKERS                并发数，内存不足时设为 1
 */
export default defineConfig({
  testDir: './tests',
  testMatch: '**/e2e/*.spec.ts',
  outputDir: './tests/test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  // 本地也允许 1 次重试，容忍内存不足导致的偶发崩溃
  // 内存不足时设置 E2E_WORKERS=1 避免崩溃
  workers: process.env.E2E_WORKERS
    ? parseInt(process.env.E2E_WORKERS, 10)
    : process.env.CI
      ? 1
      : Math.min(4, Math.floor(os.cpus().length / 2)),
  reporter: [['html', { outputFolder: './tests/playwright-report' }]],
  timeout: 60000,
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
    // 禁用录制以节省内存
    // 性能优化配置
    headless: true,
    ignoreHTTPSErrors: true,
    // 减少等待时间
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // 浏览器启动参数优化
        launchOptions: {
          args: [
            '--disable-gpu',
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--no-sandbox',
            '--disable-extensions',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-component-update',
            '--no-first-run',
            '--disable-sync',
            '--disable-background-networking',
            '--js-flags=--max-old-space-size=512',
            '--memory-pressure-off',
            '--max_old_space_size=512',
          ],
        },
      },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
