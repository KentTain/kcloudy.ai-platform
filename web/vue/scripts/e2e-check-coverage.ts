#!/usr/bin/env node
/**
 * E2E 测试覆盖缺失检测脚本
 *
 * 功能：
 * 1. 登录获取 Token
 * 2. 从 /me 接口获取菜单数据
 * 3. 扫描 tests 目录下所有 .spec.ts 文件并提取测试名称
 * 4. 对比菜单与测试覆盖情况
 * 5. 生成 Markdown 格式的缺失报告
 *
 * 使用方法：
 *   pnpm test:coverage:check
 *   或
 *   tsx scripts/e2e-check-coverage.ts
 *
 * 环境变量：
 *   E2E_API_BASE - API 基础路径（默认: http://127.0.0.1:8000）
 */

import { writeFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { glob } from 'glob';

// ============================================================================
// 配置常量
// ============================================================================

const API_BASE = process.env.E2E_API_BASE || 'http://127.0.0.1:8000';
const ADMIN_LOGIN_URL = `${API_BASE}/api/tenant/admin/v1/auth/login`;
const ADMIN_ME_URL = `${API_BASE}/api/tenant/admin/v1/admin/me`;
const DEFAULT_USERNAME = 'admin';
const DEFAULT_PASSWORD = 'admin123';

// 测试文件扫描模式
const TEST_FILE_PATTERNS = [
  'tests/tenant/e2e/*.spec.ts',
  'tests/iam/e2e/*.spec.ts',
  'tests/ai/e2e/*.spec.ts',
  'tests/demo/e2e/*.spec.ts',
];

// ============================================================================
// 类型定义
// ============================================================================

interface MenuItem {
  id: string;
  name: string;
  path: string;
  is_visible: boolean;
  children?: MenuItem[];
}

interface TestInfo {
  name: string;
  file: string;
  describe?: string;
}

interface CoverageReport {
  generatedAt: string;
  menus: MenuCoverage[];
  statistics: {
    totalMenus: number;
    coveredMenus: number;
    uncoveredMenus: number;
    coverageRate: string;
  };
}

interface MenuCoverage {
  name: string;
  path: string;
  testFile: string | null;
  status: 'covered' | 'partial' | 'uncovered';
}

// ============================================================================
// API 辅助函数
// ============================================================================

/**
 * 管理员登录获取 Token
 */
async function adminLogin(
  username = DEFAULT_USERNAME,
  password = DEFAULT_PASSWORD
): Promise<string> {
  console.log(`正在登录管理员账号: ${username}`);

  const response = await fetch(ADMIN_LOGIN_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`管理员登录失败 (HTTP ${response.status}): ${errorText}`);
  }

  const data = await response.json();
  const token = data?.data?.token;

  if (!token) {
    throw new Error(`登录响应中未找到 token 字段: ${JSON.stringify(data)}`);
  }

  console.log('登录成功，已获取 Token');
  return token;
}

/**
 * 获取管理员菜单数据
 */
async function getAdminMenus(token: string): Promise<MenuItem[]> {
  console.log('正在获取管理员菜单数据...');

  const response = await fetch(ADMIN_ME_URL, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`获取管理员信息失败 (HTTP ${response.status}): ${errorText}`);
  }

  const data = await response.json();
  const menus = data?.data?.menus || [];

  console.log(`获取到 ${menus.length} 个菜单项`);
  return menus;
}

// ============================================================================
// 测试文件扫描
// ============================================================================

/**
 * 扫描测试文件并提取测试名称
 */
async function scanTestFiles(baseDir: string): Promise<Map<string, TestInfo[]>> {
  console.log('正在扫描测试文件...');

  const testMap = new Map<string, TestInfo[]>();

  for (const pattern of TEST_FILE_PATTERNS) {
    const files = await glob(pattern, { cwd: baseDir });

    for (const file of files) {
      const filePath = resolve(baseDir, file);
      const tests = extractTestsFromFile(filePath);

      if (tests.length > 0) {
        testMap.set(file, tests);
        console.log(`  - ${file}: 发现 ${tests.length} 个测试`);
      }
    }
  }

  return testMap;
}

/**
 * 从测试文件中提取测试名称
 */
function extractTestsFromFile(filePath: string): TestInfo[] {
  const content = readFileSync(filePath, 'utf-8');
  const tests: TestInfo[] = [];

  // 匹配 test.describe('xxx', ...) 块
  const describeRegex = /test\.describe\s*\(\s*['"`]([^'"`]+)['"`]/g;

  // 匹配 test('xxx', ...) 或 test.only('xxx', ...)
  const testRegex = /test(?:\.(?:only|skip|fixme))?\s*\(\s*['"`]([^'"`]+)['"`]/g;

  // 先提取 describe 块
  const describes: string[] = [];
  let describeMatch;
  while ((describeMatch = describeRegex.exec(content)) !== null) {
    describes.push(describeMatch[1]);
  }

  // 重置正则的 lastIndex
  testRegex.lastIndex = 0;

  // 提取测试名称
  let testMatch;
  while ((testMatch = testRegex.exec(content)) !== null) {
    tests.push({
      name: testMatch[1],
      file: filePath.split(/[\\/]/).pop() || filePath,
      describe: describes.length > 0 ? describes[describes.length - 1] : undefined,
    });
  }

  return tests;
}

// ============================================================================
// 覆盖分析
// ============================================================================

/**
 * 展平菜单树结构
 */
function flattenMenus(menus: MenuItem[], result: MenuItem[] = []): MenuItem[] {
  for (const menu of menus) {
    if (menu.is_visible) {
      result.push(menu);
    }
    if (menu.children && menu.children.length > 0) {
      flattenMenus(menu.children, result);
    }
  }
  return result;
}

/**
 * 匹配测试文件与菜单路径
 */
function matchTestFile(
  menuPath: string,
  testMap: Map<string, TestInfo[]>
): string | null {
  // 从路径提取模块名（如 /admin/tenants -> admin）
  const pathParts = menuPath.split('/').filter(Boolean);
  const moduleName = pathParts[0] || '';

  // 检查是否有对应模块的测试文件
  for (const [file, tests] of testMap) {
    // 检查文件路径是否匹配模块
    if (file.includes(`/${moduleName}/`) || file.includes(`\\${moduleName}\\`)) {
      // 检查测试名称是否与菜单路径相关
      const menuName = pathParts[pathParts.length - 1] || '';
      const hasRelatedTest = tests.some(
        (test) =>
          test.name.toLowerCase().includes(menuName.toLowerCase()) ||
          (test.describe && test.describe.toLowerCase().includes(menuName.toLowerCase()))
      );

      if (hasRelatedTest) {
        return file.split(/[\\/]/).pop() || file;
      }
    }
  }

  return null;
}

/**
 * 分析菜单覆盖情况
 */
function analyzeCoverage(
  menus: MenuItem[],
  testMap: Map<string, TestInfo[]>
): CoverageReport {
  console.log('正在分析测试覆盖情况...');

  const flatMenus = flattenMenus(menus);
  const menuCoverages: MenuCoverage[] = [];

  for (const menu of flatMenus) {
    const testFile = matchTestFile(menu.path, testMap);

    menuCoverages.push({
      name: menu.name,
      path: menu.path,
      testFile,
      status: testFile ? 'covered' : 'uncovered',
    });
  }

  const coveredCount = menuCoverages.filter((m) => m.status === 'covered').length;
  const totalCount = menuCoverages.length;

  return {
    generatedAt: new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
    menus: menuCoverages,
    statistics: {
      totalMenus: totalCount,
      coveredMenus: coveredCount,
      uncoveredMenus: totalCount - coveredCount,
      coverageRate: totalCount > 0 ? `${((coveredCount / totalCount) * 100).toFixed(1)}%` : '0%',
    },
  };
}

// ============================================================================
// 报告生成
// ============================================================================

/**
 * 生成 Markdown 格式的缺失报告
 */
function generateMarkdownReport(report: CoverageReport): string {
  const lines: string[] = [];

  // 标题
  lines.push('# E2E 测试覆盖缺失报告');
  lines.push('');
  lines.push(`**生成时间**: ${report.generatedAt}`);
  lines.push('');

  // 菜单列表表格
  lines.push('## 菜单列表');
  lines.push('');
  lines.push('| 菜单名称 | 路径 | 测试文件 | 覆盖状态 |');
  lines.push('|---------|------|---------|---------|');

  for (const menu of report.menus) {
    const statusIcon = menu.status === 'covered' ? '✅' : '❌';
    const testFile = menu.testFile || '-';
    lines.push(`| ${menu.name} | ${menu.path} | ${testFile} | ${statusIcon} |`);
  }

  lines.push('');

  // 缺失测试清单
  const uncoveredMenus = report.menus.filter((m) => m.status === 'uncovered');

  if (uncoveredMenus.length > 0) {
    lines.push('## 缺失测试清单');
    lines.push('');

    for (const menu of uncoveredMenus) {
      lines.push(`### ${menu.path}`);
      lines.push(`- 无对应测试文件`);
      lines.push('');
    }
  }

  // 统计信息
  lines.push('## 统计');
  lines.push('');
  lines.push(`- 总菜单数: ${report.statistics.totalMenus}`);
  lines.push(`- 已覆盖: ${report.statistics.coveredMenus}`);
  lines.push(`- 未覆盖: ${report.statistics.uncoveredMenus}`);
  lines.push(`- 覆盖率: ${report.statistics.coverageRate}`);
  lines.push('');

  return lines.join('\n');
}

/**
 * 保存报告到文件
 */
function saveReport(content: string, baseDir: string): string {
  const docsDir = resolve(baseDir, 'docs/tests');

  // 确保目录存在
  if (!existsSync(docsDir)) {
    mkdirSync(docsDir, { recursive: true });
  }

  // 生成文件名（包含日期）
  const date = new Date();
  const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD
  const fileName = `test-lose-item-${dateStr}.md`;
  const filePath = resolve(docsDir, fileName);

  writeFileSync(filePath, content, 'utf-8');

  return filePath;
}

// ============================================================================
// 主函数
// ============================================================================

async function main() {
  console.log('='.repeat(60));
  console.log('E2E 测试覆盖缺失检测');
  console.log('='.repeat(60));
  console.log(`API 基础路径: ${API_BASE}`);
  console.log('');

  try {
    // 1. 登录获取 Token
    const token = await adminLogin();

    // 2. 获取菜单数据
    const menus = await getAdminMenus(token);

    if (menus.length === 0) {
      console.log('警告: 未获取到任何菜单数据');
      return;
    }

    // 3. 扫描测试文件
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = dirname(__filename);
    const baseDir = resolve(__dirname, '..');

    const testMap = await scanTestFiles(baseDir);

    if (testMap.size === 0) {
      console.log('警告: 未找到任何测试文件');
    }

    // 4. 分析覆盖情况
    const report = analyzeCoverage(menus, testMap);

    // 5. 生成报告
    const markdown = generateMarkdownReport(report);
    const reportPath = saveReport(markdown, baseDir);

    console.log('');
    console.log('='.repeat(60));
    console.log('报告已生成:');
    console.log(reportPath);
    console.log('');
    console.log('统计信息:');
    console.log(`  - 总菜单数: ${report.statistics.totalMenus}`);
    console.log(`  - 已覆盖: ${report.statistics.coveredMenus}`);
    console.log(`  - 未覆盖: ${report.statistics.uncoveredMenus}`);
    console.log(`  - 覆盖率: ${report.statistics.coverageRate}`);
    console.log('='.repeat(60));
  } catch (error) {
    console.error('执行失败:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

main();
