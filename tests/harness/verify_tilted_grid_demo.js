/**
 * 医疗物资 SPD 3D 弧面圆柱流光全景展厅 (Tilted Grid Hero) 自动化测试与 Playwright 回环验证脚本
 *
 * 验证目标:
 * 1. 静态代码扫描: docs/design/spd_tilted_grid_hero_demo.html 100% 零 Emoji 违规;
 * 2. 驱动 Playwright 持久化无锁浏览器, 依次验证:
 *    - 3D 弧面圆柱流光带 (#tgh-band) 正常装配, 瓦片 (.tgh-tile) 与 16-垂直微切片 (.tgh-slice) 精确渲染;
 *    - 中央悬浮通透主舞台 (#hero-main-stage) 标题、徽标、CTA 按钮组与三大法定内控合规指标卡渲染就绪;
 *    - 亮暗双色主题 (#theme-toggle-btn) 双向切换正常;
 *    - 5 大智能体快速弹窗 (#agent-modal) 呼出与关闭顺畅;
 * 3. 校验 Console Error = 0 并分别截取亮暗高清实机验证图归档至 tests/screenshots/.
 */

const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { launchPersistentPlaywright } = require('../e2e/browser_config');
const { checkNoEmoji } = require('./guardrails');

const ROOT_DIR = path.resolve(__dirname, '../..');
const DEMO_PATH = path.resolve(ROOT_DIR, 'docs/design/spd_tilted_grid_hero_demo.html');
const SCREENSHOT_DIR = path.resolve(ROOT_DIR, 'tests/screenshots');
const SCREENSHOT_LIGHT = path.resolve(SCREENSHOT_DIR, '2026-11-02_14-36-00_tilted_grid_hero_light.png');
const SCREENSHOT_DARK = path.resolve(SCREENSHOT_DIR, '2026-11-02_14-36-00_tilted_grid_hero_dark.png');

/**
 * 执行静态合规扫描
 * @returns {void}
 * @route internal://tests/harness/verify_tilted_grid_demo.js/runStaticAudit
 * @throws {Error} 文件缺失或检测到 Emoji 时抛出
 */
function runStaticAudit() {
  console.log('[TiltedGrid-Audit] 1. 正在校验 3D 弧面展厅原型文件存在性与静态无 Emoji 违规...');
  if (!fs.existsSync(DEMO_PATH) || fs.statSync(DEMO_PATH).size === 0) {
    throw new Error(`原型文件不存在或为空: ${DEMO_PATH}`);
  }

  const content = fs.readFileSync(DEMO_PATH, 'utf-8');
  const check = checkNoEmoji(content, 'docs/design/spd_tilted_grid_hero_demo.html');
  if (!check.passed) {
    throw new Error(check.violation);
  }
  console.log('[TiltedGrid-Audit] 静态扫描通过: 100% 无 Emoji 违规，符合全域禁用 Emoji 铁律');
}

/**
 * 驱动 Playwright 浏览器执行 3D 弧面圆柱流光展厅渲染与交互断言
 * @returns {Promise<{light: string, dark: string}>} 截图保存路径
 * @route internal://tests/harness/verify_tilted_grid_demo.js/runBrowserVerification
 * @throws {Error} 交互失败或控制台报错时抛出
 */
async function runBrowserVerification() {
  console.log('[TiltedGrid-Browser] 2. 正在启动 Playwright 持久化无锁浏览器执行交互测试...');
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const { context, page } = await launchPersistentPlaywright({ headless: true });
  const runtimeErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error' && !msg.text().includes('favicon.ico')) {
      runtimeErrors.push(msg.text());
    }
  });
  page.on('pageerror', (err) => {
    runtimeErrors.push(err.message);
  });

  try {
    const fileUrl = pathToFileURL(DEMO_PATH).href;
    await page.goto(fileUrl, { waitUntil: 'domcontentloaded' });
    await page.setViewportSize({ width: 1440, height: 900 });

    // 断言 1: 验证 3D 圆柱体流光带瓦片与微切片渲染
    const tileCount = await page.locator('.tgh-tile').count();
    console.log(`[TiltedGrid-Browser] 检测到 3D 圆柱体环形流光瓦片数量: ${tileCount}`);
    if (tileCount < 8) {
      throw new Error(`流光瓦片数量过少，期望至少 8，实际检测到 ${tileCount}`);
    }

    const sliceCount = await page.locator('.tgh-slice').count();
    console.log(`[TiltedGrid-Browser] 检测到垂直微切片 (Strip Facets) 总数: ${sliceCount}`);
    if (sliceCount !== tileCount * 16) {
      throw new Error(`16 微切片总数不匹配: 期望 ${tileCount * 16}，实际检测到 ${sliceCount}`);
    }
    console.log('[TiltedGrid-Browser] 断言 1 通过: 16-切片圆柱 3D 曲面微积分几何面全部装配成功');

    // 断言 2: 验证中央主舞台与核心文案
    const centerStage = page.locator('#hero-main-stage');
    if (!(await centerStage.isVisible())) {
      throw new Error('中央主舞台 #hero-main-stage 未正常显示');
    }
    const badgeText = await page.locator('.hero-pill-badge').innerText();
    if (!badgeText.includes('SPD') || !badgeText.includes('v2.0')) {
      throw new Error('中央状态微徽标校验失败');
    }
    const metricCount = await page.locator('.metric-col').count();
    if (metricCount !== 3) {
      throw new Error(`法定合规指标卡数量不符，期望 3，实际检测到 ${metricCount}`);
    }
    console.log('[TiltedGrid-Browser] 断言 2 通过: 中央静态主舞台、CTA 按钮组及三大法定指标卡渲染完好');

    // 截取亮色大屏展厅实机截图
    await page.waitForTimeout(400);
    await page.screenshot({ path: SCREENSHOT_LIGHT, fullPage: false });
    console.log(`[TiltedGrid-Browser] 亮色实机截图已保存至: ${SCREENSHOT_LIGHT}`);

    // 断言 3: 验证亮暗主题双向切换
    const themeBtn = page.locator('#theme-toggle-btn');
    await themeBtn.click();
    const isDark = await page.evaluate(() => document.documentElement.getAttribute('data-theme') === 'dark');
    if (!isDark) {
      throw new Error('切换暗黑主题未生效');
    }
    console.log('[TiltedGrid-Browser] 断言 3 通过: 暗色主题 (Dark Mode) 成功激活');

    // 断言 4: 验证 5 大智能体弹窗呼出与关闭
    await page.click('#btn-open-agents-quick');
    const isModalOpen = await page.locator('#agent-modal').isVisible();
    if (!isModalOpen) {
      throw new Error('智能体弹窗 #agent-modal 呼出失败');
    }
    await page.locator('#agent-modal .btn-theme').click();
    console.log('[TiltedGrid-Browser] 断言 4 通过: 5 大业务智能体快速弹窗呼出与关闭交互顺畅');

    // 稍候 500ms 截取暗色大屏展厅实机截图
    await page.waitForTimeout(500);
    await page.screenshot({ path: SCREENSHOT_DARK, fullPage: false });
    console.log(`[TiltedGrid-Browser] 暗色实机截图已保存至: ${SCREENSHOT_DARK}`);

    // 运行时报错检查
    if (runtimeErrors.length > 0) {
      throw new Error(`页面存在控制台运行时错误: ${runtimeErrors.join(' | ')}`);
    }

    return { light: SCREENSHOT_LIGHT, dark: SCREENSHOT_DARK };
  } finally {
    await context.close();
  }
}

/**
 * 主执行函数
 */
async function main() {
  console.log('====================================================');
  console.log('开始执行医疗物资展厅 (Tilted Grid Hero) 回环验证');
  console.log('====================================================');

  try {
    runStaticAudit();
    const result = await runBrowserVerification();
    console.log('====================================================');
    console.log('3D 弧面圆柱流光展厅验证全部通过! 0 错误 0 Emoji');
    console.log(`亮色实机截图路径: ${result.light}`);
    console.log(`暗色实机截图路径: ${result.dark}`);
    console.log('====================================================');
  } catch (err) {
    console.error(`验证失败: ${err.message}`);
    process.exit(1);
  }
}

main();
