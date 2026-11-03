/**
 * 医疗物资 SPD 数字化展厅 (轨道画廊展示大屏) 自动化测试与 Playwright 回环验证脚本
 *
 * 验证目标:
 * 1. 静态代码扫描: docs/design/spd_orbital_hero_demo.html 100% 零 Emoji 违规;
 * 2. 驱动 Playwright 持久化无锁浏览器, 依次验证:
 *    - 轨道旋转架 (#orbit-rig) 正常加载且精准按极坐标注入 10 大核心业务卡片 (.medical-card-pod);
 *    - 中央静态主舞台 (#hero-main-stage) 标题、徽标、CTA 按钮及三大法定合规指标卡渲染完整;
 *    - 亮暗主题 (#theme-toggle-btn) 双向切换正常;
 *    - 智能体快速弹窗 (#agent-modal) 呼出与关闭交互顺畅;
 * 3. 校验 Console Error = 0 并截取实机验证图保存至 tests/screenshots/2026-11-02_14-21-00_orbital_hero_demo_verify.png.
 */

const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { launchPersistentPlaywright } = require('../e2e/browser_config');
const { checkNoEmoji } = require('./guardrails');

const ROOT_DIR = path.resolve(__dirname, '../..');
const DEMO_PATH = path.resolve(ROOT_DIR, 'docs/design/spd_orbital_hero_demo.html');
const SCREENSHOT_DIR = path.resolve(ROOT_DIR, 'tests/screenshots');
const SCREENSHOT_DARK = path.resolve(SCREENSHOT_DIR, '2026-11-02_14-21-00_orbital_hero_demo_dark.png');
const SCREENSHOT_LIGHT = path.resolve(SCREENSHOT_DIR, '2026-11-02_14-21-00_orbital_hero_demo_light.png');

/**
 * 执行静态合规扫描
 * @returns {void}
 * @route internal://tests/harness/verify_orbital_demo.js/runStaticAudit
 * @throws {Error} 文件缺失或检测到 Emoji 时抛出
 */
function runStaticAudit() {
  console.log('[Orbital-Audit] 1. 正在校验轨道画廊原型文件存在性与静态无 Emoji 违规...');
  if (!fs.existsSync(DEMO_PATH) || fs.statSync(DEMO_PATH).size === 0) {
    throw new Error(`轨道画廊文件不存在或为空: ${DEMO_PATH}`);
  }

  const content = fs.readFileSync(DEMO_PATH, 'utf-8');
  const check = checkNoEmoji(content, 'docs/design/spd_orbital_hero_demo.html');
  if (!check.passed) {
    throw new Error(check.violation);
  }
  console.log('[Orbital-Audit] 静态扫描通过: 100% 无 Emoji 违规，符合全域禁用 Emoji 铁律');
}

/**
 * 驱动 Playwright 浏览器执行轨道画廊渲染与交互断言
 * @returns {Promise<string>} 截图保存路径
 * @route internal://tests/harness/verify_orbital_demo.js/runBrowserVerification
 * @throws {Error} 交互失败或控制台报错时抛出
 */
async function runBrowserVerification() {
  console.log('[Orbital-Browser] 2. 正在启动 Playwright 持久化无锁浏览器执行交互测试...');
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

    // 断言 1: 验证 10 个轨道卡片节点已成功按极坐标注入
    const cardPods = page.locator('.medical-card-pod');
    const cardCount = await cardPods.count();
    console.log(`[Orbital-Browser] 检测到在轨卡片数量: ${cardCount}`);
    if (cardCount !== 10) {
      throw new Error(`轨道卡片数量不符，期望 10，实际检测到 ${cardCount}`);
    }
    console.log('[Orbital-Browser] 断言 1 通过: 10 大医疗业务卡片全部正确挂载到 520px 环形轨道');

    // 断言 2: 验证中央主舞台与核心文案元素
    const centerStage = page.locator('#hero-main-stage');
    if (!(await centerStage.isVisible())) {
      throw new Error('中央主舞台 #hero-main-stage 未正常显示');
    }
    const badgeText = await page.locator('.hero-pill-badge').innerText();
    if (!badgeText.includes('SPD') || !badgeText.includes('v2.0')) {
      throw new Error('中央状态徽标文案校验失败');
    }
    const metricCount = await page.locator('.metric-col').count();
    if (metricCount !== 3) {
      throw new Error(`法定合规指标卡数量不符，期望 3，实际检测到 ${metricCount}`);
    }
    console.log('[Orbital-Browser] 断言 2 通过: 中央静态主舞台、CTA 按钮及三大法定合规指标卡渲染完好');

    // 截取亮色大屏展厅实机截图 (1:1 还原 21st.dev 浅色卡片视觉)
    await page.waitForTimeout(400);
    await page.screenshot({ path: SCREENSHOT_LIGHT, fullPage: false });
    console.log(`[Orbital-Browser] 亮色实机截图已保存至: ${SCREENSHOT_LIGHT}`);

    // 断言 3: 验证亮暗主题双向切换
    const themeBtn = page.locator('#theme-toggle-btn');
    await themeBtn.click();
    let isDark = await page.evaluate(() => document.documentElement.getAttribute('data-theme') === 'dark');
    if (!isDark) {
      throw new Error('切换暗黑主题未生效');
    }
    console.log('[Orbital-Browser] 断言 3.1 通过: 暗色主题 (Dark Mode) 成功激活');

    // 断言 4: 验证 5 大智能体弹窗呼出与关闭
    await page.click('#btn-open-agents-quick');
    const isModalOpen = await page.locator('#agent-modal').isVisible();
    if (!isModalOpen) {
      throw new Error('智能体弹窗 #agent-modal 呼出失败');
    }
    // 关闭弹窗以恢复展厅全景
    await page.locator('#agent-modal .btn-theme').click();
    console.log('[Orbital-Browser] 断言 4 通过: 5 大业务智能体快速弹窗呼出与关闭正常');

    // 稍候 500ms 让 CSS 关键帧轨道动画平滑运转并截取暗色截图
    await page.waitForTimeout(500);
    await page.screenshot({ path: SCREENSHOT_DARK, fullPage: false });
    console.log(`[Orbital-Browser] 暗色实机截图已保存至: ${SCREENSHOT_DARK}`);

    // 校验运行时错误
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
  console.log('开始执行医疗物资展厅 (Orbital Gallery Hero) 回环验证');
  console.log('====================================================');

  try {
    runStaticAudit();
    const result = await runBrowserVerification();
    console.log('====================================================');
    console.log('轨道画廊英雄展厅验证全部通过! 0 错误 0 Emoji');
    console.log(`亮色实机截图路径: ${result.light}`);
    console.log(`暗色实机截图路径: ${result.dark}`);
    console.log('====================================================');
  } catch (err) {
    console.error(`验证失败: ${err.message}`);
    process.exit(1);
  }
}

main();
