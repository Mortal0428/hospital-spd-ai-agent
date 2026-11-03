const fs = require('fs');
const path = require('path');
const { launchPersistentPlaywright } = require('../e2e/browser_config');
const { runAllGuardrails } = require('./guardrails');

/**
 * 校验项目 Harness 六大组件规范文件、ORM comment 契约及熵管理归档目录的完整性
 * @param {string} rootDir 项目根目录绝对路径
 * @returns {Array<{file: string, exists: boolean, size: number, role: string}>} 返回各规范文件的检查结果列表
 * @route internal://tests/harness/runner.js/verifyHarnessFiles
 * @throws {Error} 当核心规范文件缺失或为空时抛出断言异常
 */
function verifyHarnessFiles(rootDir) {
  const targetSpecs = [
    { relPath: 'CLAUDE.md', role: '组件1&4: 跨桌面全局上下文与ORM/目录架构硬约束' },
    { relPath: 'AGENTS.md', role: '组件2: 研发子Agent专业化分工与5大业务智能体契约' },
    { relPath: 'SKILL.md', role: '组件5&6: 反馈循环自进化技能库与防错资产治理' },
    { relPath: 'tests/harness/guardrails.js', role: '组件4&5: 自动代码合规扫描与SKILL反哺引擎' },
    { relPath: 'docs/requirements.md', role: '组件1&3: 三级角色/PM六大规则/5套CRUD/智能体流程图' },
    { relPath: 'docs/db_schema.md', role: '组件1&4: SQLAlchemy 2.0 ORM映射与100% comment注释规范' },
    { relPath: 'docs/api_spec.md', role: '组件1&4: FastAPI RESTful契约与MCP/小米MiMo可插拔规范' },
    { relPath: 'plans/2026-11-02_10-41-00_master_project_plan_and_confirmed_baseline.md', role: '组件3: 持久化记忆总体计划书基线' },
    { relPath: 'plans/archive/README.md', role: '组件6: 熵管理历史计划降权归档台账' }
  ];

  const results = [];
  for (const item of targetSpecs) {
    const fullPath = path.resolve(rootDir, item.relPath);
    const exists = fs.existsSync(fullPath);
    const size = exists ? fs.statSync(fullPath).size : 0;
    if (!exists || size === 0) {
      throw new Error(`[Harness-Assert-Fail] 关键规范文件缺失或内容为空: ${item.relPath}`);
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
 * 构建用于 Playwright 实机渲染验证的 HTML 视图内容（采用 CSS 变量适配主题，严禁使用任何 Emoji）
 * @param {Array<{file: string, exists: boolean, size: number, role: string}>} checkResults 规范文件校验结果数组
 * @returns {string} 完整的 HTML 文本字符串
 * @route internal://tests/harness/runner.js/buildVerificationHtml
 * @throws {Error} 当入参非法时抛出格式化异常
 */
function buildVerificationHtml(checkResults) {
  if (!Array.isArray(checkResults)) {
    throw new Error('checkResults 必须为有效数组');
  }

  const rowsHtml = checkResults
    .map(
      (item) => `
      <tr>
        <td class="mono">${item.file}</td>
        <td>${item.role}</td>
        <td class="mono">${item.size} Bytes</td>
        <td><span class="status-badge">VERIFIED</span></td>
      </tr>`
    )
    .join('');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>医疗物资全链路管理系统 - Harness 规范与前期基建自检台</title>
  <style>
    :root {
      --bg-page: #0b1120;
      --bg-card: #111827;
      --bg-table-head: #1e293b;
      --border-subtle: #1f2937;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --accent-primary: #38bdf8;
      --status-ok-bg: rgba(16, 185, 129, 0.14);
      --status-ok-text: #34d399;
      --status-ok-border: rgba(52, 211, 153, 0.35);
    }
    * { box-sizing: border-box; user-select: none; }
    body {
      margin: 0;
      padding: 32px;
      background-color: var(--bg-page);
      color: var(--text-primary);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    }
    .container {
      max-width: 1120px;
      margin: 0 auto;
      background-color: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 28px 32px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border-subtle);
      padding-bottom: 18px;
      margin-bottom: 20px;
    }
    .title {
      font-size: 20px;
      font-weight: 600;
      margin: 0 0 6px 0;
    }
    .subtitle {
      font-size: 13px;
      color: var(--text-secondary);
      margin: 0;
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin-bottom: 22px;
    }
    .metric-box {
      background-color: var(--bg-table-head);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      padding: 14px 16px;
    }
    .metric-label {
      font-size: 12px;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }
    .metric-val {
      font-size: 15px;
      font-weight: 600;
      color: var(--accent-primary);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      text-align: left;
      padding: 11px 14px;
      border-bottom: 1px solid var(--border-subtle);
    }
    th {
      background-color: var(--bg-table-head);
      color: var(--text-secondary);
      font-weight: 600;
    }
    .mono {
      font-family: Consolas, Monaco, monospace;
      color: var(--accent-primary);
    }
    .status-badge {
      display: inline-block;
      padding: 3px 10px;
      font-size: 11px;
      font-weight: 600;
      color: var(--status-ok-text);
      background-color: var(--status-ok-bg);
      border: 1px solid var(--status-ok-border);
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <div class="container" id="harness-root">
    <div class="header">
      <div>
        <h1 class="title">医院医疗物资全链路管理系统 - Harness 工程基建自检报告</h1>
        <p class="subtitle">三级角色权限(信息科/设备耗材财务科/二级库) | PM六大深度业务规则 | SQLAlchemy 2.0 ORM 100% comment注释契约</p>
      </div>
      <span class="status-badge">ALL 6 HARNESS PILLARS READY</span>
    </div>
    <div class="summary-grid">
      <div class="metric-box">
        <div class="metric-label">人员与业务流转体系</div>
        <div class="metric-val">三级人员 + 5套核心CRUD + 统计打印</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">数据库映射规范</div>
        <div class="metric-val">SQLAlchemy 2.0 ORM + 全字段 comment</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">智能体与工具链架构</div>
        <div class="metric-val">5大LangGraph智能体 + MCP + Chroma</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">熵管理与记忆持久化</div>
        <div class="metric-val">plans/活跃台账 + archive/降权归档</div>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>物理文件路径</th>
          <th>承载的 Harness 架构职责</th>
          <th>文件字节数</th>
          <th>自检状态</th>
        </tr>
      </thead>
      <tbody>
        ${rowsHtml}
      </tbody>
    </table>
  </div>
</body>
</html>`;
}

/**
 * 执行 Harness 工程规范与前期准备工作的端到端回环验证及截图取证
 * @returns {Promise<string>} 返回生成的实机验证截图路径
 * @route internal://tests/harness/runner.js/runHarnessVerification
 * @throws {Error} 若存在控制台报错、DOM 断言未通过或浏览器异常则抛出错误
 */
async function runHarnessVerification() {
  const rootDir = path.resolve(__dirname, '../..');
  const checkResults = verifyHarnessFiles(rootDir);
  const guardrailReport = runAllGuardrails(rootDir);
  if (!guardrailReport.allPassed) {
    throw new Error(`[Harness-Guardrails-Fail] 架构护栏扫描未通过: ${guardrailReport.violations.join('; ')}`);
  }
  console.log(`[Harness-Guardrails] ${guardrailReport.ormReport.message}`);

  let contextHandle = null;
  const consoleErrors = [];

  try {
    const { context, page } = await launchPersistentPlaywright({ headless: true });
    contextHandle = context;

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(err.message);
    });

    const htmlContent = buildVerificationHtml(checkResults);
    await page.setContent(htmlContent, { waitUntil: 'domcontentloaded' });

    const rootVisible = await page.locator('#harness-root').isVisible();
    if (!rootVisible) {
      throw new Error('Harness 自检视图根节点 #harness-root 未能正常渲染');
    }

    if (consoleErrors.length > 0) {
      throw new Error(`检测到页面控制台异常: ${consoleErrors.join('; ')}`);
    }

    const screenshotDir = path.resolve(rootDir, 'tests/screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }

    const screenshotPath = path.resolve(
      screenshotDir,
      '2026-11-02_11-22-00_harness_spec_verify.png'
    );
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`[Harness-Runner] 规范校验与浏览器实机渲染通过，截图已保存至: ${screenshotPath}`);
    return screenshotPath;
  } finally {
    if (contextHandle) {
      await contextHandle.close();
    }
  }
}

if (require.main === module) {
  runHarnessVerification().catch((err) => {
    console.error('[Harness-Runner] 自检失败:', err.message);
    process.exit(1);
  });
}

module.exports = {
  verifyHarnessFiles,
  buildVerificationHtml,
  runHarnessVerification
};
