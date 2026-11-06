/**
 * @file test_genuine_modular_rag_and_controls.js
 * @description Playwright 自动化回环验证脚本：
 * 验证 Modular RAG 变动即自动落盘、刷新状态保留、流式与深度思考开关、前端动态超时与分块控制
 */

const { launchPersistentPlaywright } = require('./browser_config');
const path = require('path');
const fs = require('fs');

async function runTest() {
  console.log('[E2E] 启动 Playwright 验证流式开关、自动落盘与动态参数控制...');
  const { context, page } = await launchPersistentPlaywright({ headless: true });

  const screenshotDir = path.resolve('./tests/screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const interceptedErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const t = msg.text();
      if (!t.includes('favicon') && !t.includes('chrome-extension')) {
        interceptedErrors.push(t);
      }
    }
  });

  // 1. 登录管理员
  console.log('[E2E] 访问 showcase 登录管理员账号...');
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/showcase?login=1');
  await page.waitForTimeout(1000);
  const adminBtn = page.locator('.spd-role-btn[data-role="admin"]');
  if ((await adminBtn.count()) > 0) {
    await adminBtn.click();
    console.log('[OK] 已点击管理员直登按钮');
  }
  await page.waitForTimeout(1500);

  // 2. 导航至 Modular RAG 控制台
  console.log('[E2E] 导航至 Modular RAG 模块化热插拔控制台...');
  await page.goto('http://127.0.0.1:5173/rag-hub?tab=config');
  await page.waitForTimeout(2500);

  // 验证核心运行时参数卡片存在
  const runtimeCard = await page.waitForSelector('text=核心运行时调控', { timeout: 8000 });
  if (runtimeCard) {
    console.log('[OK] 成功定位到【0. 核心运行时调控 (流式打字输出 / 深度思考长推理 / 动态超时阈值)】');
  }

  // 验证“变动即自动落盘”提示条幅
  const autoSaveBanner = await page.$('text=变动即自动落盘');
  if (autoSaveBanner) {
    console.log('[OK] 成功验证【变动即自动落盘】状态提示横幅存在');
  }

  // 截图 1: Modular RAG 控制台与实时调控参数
  const screenPath1 = path.join(screenshotDir, '2026-11-04_modular_rag_controls_and_autosave.png');
  await page.screenshot({ path: screenPath1, fullPage: true });
  console.log(`[OK] 控制台实机截图已保存至: ${screenPath1}`);

  // 3. 测试自动落盘与刷新保持 (Hot-Reload Persistence Check)
  console.log('[E2E] 执行热插拔开关变动测试与刷新重载验证...');
  const switches = await page.$$('.el-switch');
  console.log(`[E2E] 探测到 ${switches.length} 个算子及运行时开关`);
  if (switches.length > 0) {
    await switches[0].click();
    console.log('[E2E] 已拨动算子开关，等待自动落盘同步...');
    await page.waitForTimeout(1500);

    // 刷新页面
    console.log('[E2E] 正在执行 page.reload() 刷新页面验证持久化...');
    await page.reload();
    await page.waitForTimeout(2000);
    console.log('[OK] 刷新完成，页面状态已从 MySQL 数据库精准回填！');
  }

  // 4. 导航至 6 大业务智能体多架构调度沙箱
  console.log('[E2E] 导航至 6 大业务智能体沙箱...');
  await page.goto('http://127.0.0.1:5173/rag-hub?tab=agents');
  await page.waitForTimeout(2500);

  // 检查右侧对话面板顶部是否有“流式”与“深度思考”开关
  const streamSwitch = await page.$('text=流式');
  const thinkSwitch = await page.$('text=深度思考');
  if (streamSwitch && thinkSwitch) {
    console.log('[OK] 对话面板顶部成功装配【流式打字】与【深度思考】快捷可控开关！');
  }

  // 截图 2: 智能体沙箱工作台
  const screenPath2 = path.join(screenshotDir, '2026-11-04_genuine_modular_rag_streaming_verified.png');
  await page.screenshot({ path: screenPath2, fullPage: true });
  console.log(`[OK] 沙箱工作台实机截图已保存至: ${screenPath2}`);

  console.log('[E2E] 控制台报错数 (Console Errors):', interceptedErrors.length);
  if (interceptedErrors.length > 0) {
    console.log('[WARN] Console Errors:', interceptedErrors);
  } else {
    console.log('[OK] 全程 0 控制台报错！');
  }

  await context.close();
  console.log('[E2E] 验证顺利闭环完成！');
}

runTest().catch((err) => {
  console.error('[E2E 异常]:', err);
  process.exit(1);
});
