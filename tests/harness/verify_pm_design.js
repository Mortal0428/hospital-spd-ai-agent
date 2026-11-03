const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { launchPersistentPlaywright } = require('../e2e/browser_config');
const { checkNoEmoji } = require('./guardrails');

/**
 * 静态扫描 docs/design/ 下的三份可视化 HTML 产物，确保无违规 Emoji 且文件非空
 * @param {string} rootDir 项目根目录绝对路径
 * @returns {Array<string>} 通过静态校验的 HTML 文件绝对路径列表
 * @route internal://tests/harness/verify_pm_design.js/validateDesignFilesStatic
 * @throws {Error} 当文件缺失或检测到 Emoji 时抛出异常
 */
function validateDesignFilesStatic(rootDir) {
  const relFiles = [
    'docs/design/spd_business_and_agent_flowcharts.html',
    'docs/design/spd_interactive_prototype.html',
    'docs/design/spd_prd_document.html'
  ];

  const fullPaths = [];
  for (const rel of relFiles) {
    const full = path.resolve(rootDir, rel);
    if (!fs.existsSync(full) || fs.statSync(full).size === 0) {
      throw new Error(`[PM-Verify-Fail] 设计产物缺失或为空: ${rel}`);
    }
    const text = fs.readFileSync(full, 'utf-8');
    const emojiCheck = checkNoEmoji(text, rel);
    if (!emojiCheck.passed) {
      throw new Error(emojiCheck.violation);
    }
    fullPaths.push(full);
  }
  return fullPaths;
}

/**
 * 驱动 Playwright 真实浏览器回环验证业务与 5 大智能体流程图、可点击交互原型及可视化 PRD
 * @returns {Promise<{flowchartShot: string, prototypeShot: string}>} 返回两张实机验证截图保存路径
 * @route internal://tests/harness/verify_pm_design.js/runPmDesignVerification
 * @throws {Error} 当页面存在 Console Error、DOM 缺失或交互断言失败时抛出异常
 */
async function runPmDesignVerification() {
  const rootDir = path.resolve(__dirname, '../..');
  const [flowPath, protoPath, prdPath] = validateDesignFilesStatic(rootDir);

  const screenshotDir = path.resolve(rootDir, 'tests/screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  let contextHandle = null;
  const runtimeErrors = [];

  try {
    const { context, page } = await launchPersistentPlaywright({ headless: true });
    contextHandle = context;

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        runtimeErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      runtimeErrors.push(err.message);
    });

    // 1. 验证全院业务流转与 5 大智能体节点流程图
    await page.goto(pathToFileURL(flowPath).href, { waitUntil: 'domcontentloaded' });
    const requiredCanvases = [
      '#canvas-biz-overview',
      '#canvas-agent-01',
      '#canvas-agent-02',
      '#canvas-agent-03',
      '#canvas-agent-04',
      '#canvas-agent-05'
    ];
    for (const selector of requiredCanvases) {
      const visible = await page.locator(selector).isVisible();
      if (!visible) {
        throw new Error(`流程图画布节点未正常显示: ${selector}`);
      }
    }

    const flowchartShot = path.resolve(
      screenshotDir,
      '2026-11-02_11-52-00_flowcharts_verify.png'
    );
    await page.screenshot({ path: flowchartShot, fullPage: true });

    // 2. 验证高保真可点击交互原型（角色切换、7大模块切换、四联单据打印预览与主题切换）
    await page.goto(pathToFileURL(protoPath).href, { waitUntil: 'domcontentloaded' });

    await page.selectOption('#role-select', 'consumable_mgr');
    const tabsToVerify = [
      'tab-dict',
      'tab-main-wh',
      'tab-high-value',
      'tab-secondary',
      'tab-logs',
      'tab-stats',
      'tab-agents'
    ];
    for (const tabId of tabsToVerify) {
      await page.click(`.nav-item[data-tab="${tabId}"]`);
      const isTabVisible = await page.locator(`#${tabId}`).isVisible();
      if (!isTabVisible) {
        throw new Error(`交互原型模块切换失败: ${tabId}`);
      }
    }

    // 切换回产品字典视图并打开四联签字单据打印预览进行截图验证
    await page.click('.nav-item[data-tab="tab-dict"]');
    await page.click('#btn-open-voucher');
    const modalVisible = await page.locator('#voucher-modal.open').isVisible();
    if (!modalVisible) {
      throw new Error('四联签字栏单据打印预览弹窗未能正常打开');
    }
    await page.click('#voucher-modal .btn:first-child');

    const prototypeShot = path.resolve(
      screenshotDir,
      '2026-11-02_11-52-00_prototype_verify.png'
    );
    await page.screenshot({ path: prototypeShot, fullPage: true });

    // 3. 验证可视化 PRD 文档
    await page.goto(pathToFileURL(prdPath).href, { waitUntil: 'domcontentloaded' });
    const prdVisible = await page.locator('#prdContent').isVisible();
    if (!prdVisible) {
      throw new Error('可视化 PRD 文档 #prdContent 未能正常渲染');
    }

    if (runtimeErrors.length > 0) {
      throw new Error(`检测到页面运行期异常: ${runtimeErrors.join('; ')}`);
    }

    console.log(`[PM-Design-Verify] 流程图实机截图已落盘: ${flowchartShot}`);
    console.log(`[PM-Design-Verify] 交互原型实机截图已落盘: ${prototypeShot}`);
    return { flowchartShot, prototypeShot };
  } finally {
    if (contextHandle) {
      await contextHandle.close();
    }
  }
}

if (require.main === module) {
  runPmDesignVerification().catch((err) => {
    console.error('[PM-Design-Verify] 验证失败:', err.message);
    process.exit(1);
  });
}

module.exports = {
  validateDesignFilesStatic,
  runPmDesignVerification
};
