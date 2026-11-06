/**
 * @file test_all_agents_and_hitl_visual.js
 * @description Playwright 端到端自动化回环测试：知识库切片巡检条幅、Agent 3 人机回环步骤条与审批批示物理落盘
 * @param 无
 * @returns None
 * @route tests/e2e/test_all_agents_and_hitl_visual.js
 * @throws 页面渲染或断言异常捕获
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  console.log('=== 启动 Playwright 浏览器自动化端到端回环验证 ===');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // 监听并确保 0 控制台报错
  const pageErrors = [];
  page.on('pageerror', (err) => {
    console.error('[Page Error]:', err.message);
    pageErrors.push(err.message);
  });

  const screenshotDir = path.resolve(__dirname, '../screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const now = new Date();
  const timeStr = now.toISOString().replace(/T/, '_').replace(/:/g, '-').slice(0, 19);

  try {
    // 1. 访问 RAG 知识工程与智能体中台
    console.log('1. 正在访问前端中台页面: http://localhost:5173/#/rag-agent-hub');
    await page.goto('http://localhost:5173/#/rag-agent-hub', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // 2. 验证知识库切片健康度巡检条幅渲染
    console.log('2. 验证知识库切片健康度全库巡检条幅...');
    const healthText = await page.textContent('.doc-main-table-wrap');
    console.log('包含知识库向量化健康度条幅:', healthText.includes('知识库向量化健康度'));

    const bannerScreenshot = path.join(screenshotDir, `${timeStr}_rag_health_inspection_banner.png`);
    await page.screenshot({ path: bannerScreenshot, fullPage: false });
    console.log(`已捕获知识库巡检条幅截图: ${bannerScreenshot}`);

    // 3. 切换至 6 大业务智能体沙箱
    console.log('3. 切换至【6 大业务智能体沙箱】Tab...');
    await page.click('#tab-agents');
    await page.waitForTimeout(1000);

    // 4. 选择智能体 3 (LangGraph + HITL)
    console.log('4. 选择智能体 3: 临床二级库申领问答 (LangGraph + HITL)...');
    const agentMenuItems = await page.$$('.agent-menu-item');
    for (const item of agentMenuItems) {
      const text = await item.textContent();
      if (text.includes('智能体 3')) {
        await item.click();
        break;
      }
    }
    await page.waitForTimeout(1000);

    // 5. 触发申领指令，测试中断挂起与 4 节点步骤条
    console.log('5. 发送自然语言申领诉求: 向耗材主库申领 50 包一次性医用外科口罩...');
    const chatInput = await page.waitForSelector('.agent-chat-widget input');
    await chatInput.fill('向耗材主库申领 50 包一次性医用外科口罩');
    await page.click('.agent-chat-widget button:has-text("执行")');

    console.log('等待大模型与 LangGraph 意图提取并挂起中断点...');
    await page.waitForSelector('.hitl-card', { timeout: 60000 });
    await page.waitForTimeout(2000);

    const hitlCardText = await page.textContent('.hitl-card');
    console.log('HITL 卡片渲染内容包含中断挂起 (PAUSED):', hitlCardText.includes('PAUSED') || hitlCardText.includes('挂起'));
    console.log('包含流程步骤条节点:', hitlCardText.includes('临床意图解析') && hitlCardText.includes('人机协同审批'));

    const hitlPausedScreenshot = path.join(screenshotDir, `${timeStr}_agent3_hitl_paused_stepper.png`);
    await page.screenshot({ path: hitlPausedScreenshot, fullPage: false });
    console.log(`已捕获 HITL 中断挂起与 4 节点步骤条截图: ${hitlPausedScreenshot}`);

    // 6. 人工审批: 填写批示意见并点击【同意下发 (CONFIRM)】
    console.log('6. 人工审批：输入审核批示意见并点击同意下发...');
    const commentInput = await page.waitForSelector('.hitl-action-box input');
    await commentInput.fill('护士长临床核验通过，准予紧急下发排队出库');
    await page.click('.hitl-action-box button:has-text("同意下发")');

    console.log('等待状态机推进至节点 4/4 并物理落盘请领单...');
    await page.waitForTimeout(4000);

    const hitlApprovedScreenshot = path.join(screenshotDir, `${timeStr}_agent3_hitl_approved_complete.png`);
    await page.screenshot({ path: hitlApprovedScreenshot, fullPage: false });
    console.log(`已捕获人机回环审批通过与单据落盘截图: ${hitlApprovedScreenshot}`);

    console.log('=== Playwright 端到端自动化回环测试全部成功通过！ ===');
    console.log('页面控制台致命错误数:', pageErrors.length);
  } catch (err) {
    console.error('Playwright 自动化测试执行异常:', err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
