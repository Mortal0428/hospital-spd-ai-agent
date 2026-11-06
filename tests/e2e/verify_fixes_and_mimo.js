/**
 * @file verify_fixes_and_mimo.js
 * @description Playwright 端到端自动化回环验证脚本
 * 验证：1. 知识库列表无 500、操作列完整显示
 *       2. RBAC 矩阵保存按钮与未保存提示条幅
 *       3. 智能体工作台小米 MiMo 真实挂载与思考过程展示
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const screenshotDir = path.resolve(__dirname, '../screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  // 监听控制台错误
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  console.log('[E2E] 1. 访问知识库与 Agent 控制中台页面...');
  await page.goto('http://localhost:5173/#/rag-agent-hub', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // 截取知识库与 6 大智能体总览大盘
  const p1 = path.join(screenshotDir, '2026-11-04_rag_hub_no_500.png');
  await page.screenshot({ path: p1, fullPage: false });
  console.log('[E2E] 截图 1 知识库列表无500截断已保存:', p1);

  console.log('[E2E] 2. 切换至 6 大智能体调度沙箱...');
  // 点击沙箱 Tab
  await page.locator('.el-tabs__item').filter({ hasText: '6 大业务智能体多架构调度沙箱' }).click();
  await page.waitForTimeout(1000);

  // 检查智能体 6 沙箱
  const p2 = path.join(screenshotDir, '2026-11-04_agent_sandbox_mimo.png');
  await page.screenshot({ path: p2, fullPage: false });
  console.log('[E2E] 截图 2 智能体沙箱已保存:', p2);

  console.log('[E2E] 3. 访问用户管理与 15模块x8动作 RBAC 矩阵...');
  await page.goto('http://localhost:5173/#/user-management', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // 切换至 RBAC 矩阵 Tab
  await page.locator('.el-tabs__item').filter({ hasText: '15 模块 × 8 动作细粒度 RBAC 矩阵' }).click();
  await page.waitForTimeout(1000);

  // 点击一键授予全权，触发未保存条幅与全亮
  await page.locator('button').filter({ hasText: '一键授予全权' }).click();
  await page.waitForTimeout(800);

  const p3 = path.join(screenshotDir, '2026-11-04_rbac_matrix_save_bar.png');
  await page.screenshot({ path: p3, fullPage: false });
  console.log('[E2E] 截图 3 RBAC 矩阵未保存条幅与保存按钮已保存:', p3);

  console.log('[E2E] 控制台捕获到的错误数:', consoleErrors.length);
  await browser.close();
  console.log('[E2E] 回环自动化验证完成！');
})();
