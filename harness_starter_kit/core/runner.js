const fs = require('fs');
const path = require('path');
const config = require('../config/harness.config');
const { launchHarnessBrowser } = require('./browser');
const { runAllGuardrails } = require('./guardrails');

/**
 * 校验配置文件中指定的规范基准文件完整性
 *
 * @param {string} rootDir 工程根目录绝对路径
 * @param {Array<{relPath: string, role: string}>} specList 规范列表
 * @returns {Array<{file: string, exists: boolean, size: number, role: string}>}
 * @route internal://core/runner.js/verifySpecFiles
 * @throws {Error} 若核心规范文件缺失或为空则抛出异常
 */
function verifySpecFiles(rootDir, specList) {
  const results = [];
  for (const item of specList) {
    const fullPath = path.resolve(rootDir, item.relPath);
    const exists = fs.existsSync(fullPath);
    const size = exists ? fs.statSync(fullPath).size : 0;
    if (!exists || size === 0) {
      throw new Error(`[Harness-Assert-Fail] 核心规范文件缺失或内容为空: ${item.relPath}`);
    }
    results.push({
      file: item.relPath,
      exists,
      size,
      role: item.role
    });
  }
  return results;
}

/**
 * 生成现代无 Emoji、主题自适应的 HTML 自检全息报告视图
 *
 * @param {object} data 自检数据汇总
 * @returns {string} 完整的 HTML 字符串
 * @route internal://core/runner.js/buildReportHtml
 */
function buildReportHtml(data) {
  const specRows = data.specResults
    .map(
      (item) => `
      <tr>
        <td class="mono">${item.file}</td>
        <td><span class="badge badge-success">正常通过</span></td>
        <td class="mono">${item.size} 字节</td>
        <td>${item.role}</td>
      </tr>`
    )
    .join('');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Harness 质量护栏全息自检报告</title>
  <style>
    :root {
      --bg-base: #f8fafc;
      --card-bg: #ffffff;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --border-color: #e2e8f0;
      --primary: #2563eb;
      --success: #16a34a;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg-base: #090d16;
        --card-bg: #111827;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --border-color: #1e293b;
        --primary: #3b82f6;
        --success: #22c55e;
      }
    }
    body {
      margin: 0;
      padding: 40px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg-base);
      color: var(--text-main);
      user-select: none;
    }
    .container {
      max-width: 1000px;
      margin: 0 auto;
    }
    .header {
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border-color);
    }
    .header h1 {
      margin: 0 0 8px 0;
      font-size: 24px;
      letter-spacing: -0.5px;
    }
    .header p {
      margin: 0;
      color: var(--text-muted);
      font-size: 14px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-box {
      background: var(--bg-base);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 16px;
      text-align: center;
    }
    .stat-num {
      font-size: 28px;
      font-weight: 700;
      color: var(--primary);
    }
    .stat-label {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--border-color);
    }
    th {
      color: var(--text-muted);
      font-weight: 600;
      background: var(--bg-base);
    }
    .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
    }
    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
    }
    .badge-success {
      background: rgba(22, 163, 74, 0.1);
      color: var(--success);
      border: 1px solid rgba(22, 163, 74, 0.2);
    }
    .footer {
      text-align: center;
      color: var(--text-muted);
      font-size: 12px;
      margin-top: 32px;
    }
  </style>
</head>
<body>
  <div class="container" id="harness-root">
    <div class="header">
      <h1>Harness 质量护栏全息自检报告</h1>
      <p>执行时间: ${new Date().toLocaleString('zh-CN')} | 环境: Playwright Persistent Automation</p>
    </div>

    <div class="grid">
      <div class="stat-box">
        <div class="stat-num">${data.specResults.length}</div>
        <div class="stat-label">规范文件校验通过</div>
      </div>
      <div class="stat-box">
        <div class="stat-num">${data.guardrailsResult.totalChecked}</div>
        <div class="stat-label">静态代码合规扫描文件数</div>
      </div>
      <div class="stat-box">
        <div class="stat-num">0</div>
        <div class="stat-label">Console 错误与违规拦截</div>
      </div>
    </div>

    <div class="card">
      <h3 style="margin-top:0; margin-bottom:16px;">核心研发规范文件基准</h3>
      <table>
        <thead>
          <tr>
            <th>文件路径</th>
            <th>校验状态</th>
            <th>文件大小</th>
            <th>角色与职责契约</th>
          </tr>
        </thead>
        <tbody>
          ${specRows}
        </tbody>
      </table>
    </div>

    <div class="footer">
      本自检报告由 Harness 独立质量护栏套件自动生成 | 严格遵守零 Emoji 与零密钥泄漏铁律
    </div>
  </div>
</body>
</html>`;
}

/**
 * 运行全量 Harness 回环自检主流程
 *
 * @returns {Promise<string>} 返回保存的实机截图绝对路径
 * @route internal://core/runner.js/runHarnessSuite
 * @throws {Error} 校验失败时抛出异常
 */
async function runHarnessSuite() {
  const rootDir = config.projectRoot;
  console.log(`[Harness-Runner] 开始执行工程质量护栏自检，根目录: ${rootDir}`);

  // 1. 规范文件完整性断言
  const specResults = verifySpecFiles(rootDir, config.specFiles);
  console.log(`[Harness-Runner] 成功核验 ${specResults.length} 个核心规范契约文件。`);

  // 2. 运行 Guardrails 静态扫描
  const guardrailsResult = runAllGuardrails();
  if (!guardrailsResult.passed) {
    throw new Error(`[Harness-Runner] 静态合规扫描未通过，违规项:\n${guardrailsResult.violations.join('\n')}`);
  }
  console.log(`[Harness-Runner] 静态规则扫描完成，已合规扫描 ${guardrailsResult.totalChecked} 个代码文件，0 违规。`);

  // 3. 启动 Playwright 无锁持久化浏览器并渲染报告
  let browserContext = null;
  try {
    const { context, page } = await launchHarnessBrowser(config.browser);
    browserContext = context;

    const consoleErrors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(err.message);
    });

    const reportHtml = buildReportHtml({ specResults, guardrailsResult });
    await page.setContent(reportHtml, { waitUntil: 'domcontentloaded' });

    const rootVisible = await page.locator('#harness-root').isVisible();
    if (!rootVisible) {
      throw new Error('[Harness-Runner] 自检视图根节点 #harness-root 未能正常渲染');
    }

    if (consoleErrors.length > 0) {
      throw new Error(`[Harness-Runner] 检测到页面运行时控制台报错: ${consoleErrors.join('; ')}`);
    }

    // 4. 保存实机自检截图
    const screenshotDir = path.resolve(__dirname, '../screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }

    const screenshotPath = path.resolve(screenshotDir, 'starter_kit_verify.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`[Harness-Runner] 浏览器实机验证完成，全息报告截图已生成: ${screenshotPath}`);

    return screenshotPath;
  } finally {
    if (browserContext) {
      await browserContext.close();
    }
  }
}

// 脚本直接调用处理
if (require.main === module) {
  runHarnessSuite()
    .then(() => {
      console.log('[Harness-Runner] 质量护栏套件自检全流程 100% 成功通过！');
      process.exit(0);
    })
    .catch((err) => {
      console.error('[Harness-Runner] 自检异常熔断:', err.message);
      process.exit(1);
    });
}

module.exports = {
  verifySpecFiles,
  buildReportHtml,
  runHarnessSuite
};
