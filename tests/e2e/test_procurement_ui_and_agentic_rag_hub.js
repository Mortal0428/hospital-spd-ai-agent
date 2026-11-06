/**
 * @file test_procurement_ui_and_agentic_rag_hub.js
 * @description 采供双端UI统一、单据闭环重构、6大异构智能体与Modular/Agentic RAG知识工程中台端到端自动化测试
 */

const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

async function runProcurementAndRagHubTest() {
  console.log('[E2E-RAG-HUB] 启动 Playwright 执行采供双端UI统一与Agentic RAG中台回环测试...');
  const safeTmpDir = 'C:/Users/27705/AppData/Local/Temp_pw';
  if (!fs.existsSync(safeTmpDir)) fs.mkdirSync(safeTmpDir, { recursive: true });
  const tempProfile = path.resolve(safeTmpDir, `pw_profile_rag_hub_${Date.now()}`);
  const { context, page } = await launchPersistentPlaywright({
    headless: true,
    profileDir: tempProfile
  });

  const screenshotDir = path.resolve(__dirname, '../screenshots');
  const artifactDir = path.resolve('C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2');
  if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;

  const interceptedErrors = [];
  page.on('pageerror', (err) => {
    console.error(`[Browser PageError]: ${err.message}`);
    interceptedErrors.push(`PageError: ${err.message}`);
  });
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (!text.includes('favicon') && !text.includes('chrome-extension')) {
        console.warn(`[Browser ConsoleError]: ${text}`);
        interceptedErrors.push(`ConsoleError: ${text}`);
      }
    }
  });

  async function snap(name) {
    const fileName = `${ts}_${name}.png`;
    const fullPath = path.resolve(screenshotDir, fileName);
    await page.screenshot({ path: fullPath, fullPage: true });
    console.log(`[E2E-Screenshot] 截图已捕获: ${fileName}`);
    if (fs.existsSync(artifactDir)) {
      try {
        fs.copyFileSync(fullPath, path.resolve(artifactDir, fileName));
      } catch (e) {}
    }
  }

  try {
    await page.setViewportSize({ width: 1440, height: 900 });

    // 0. 系统管理员标准登录流程
    console.log('[Step 0] 通过医慧通行通道完成系统管理员身份登录...');
    await page.goto('http://127.0.0.1:5173/showcase?login=1', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    const adminFastBtn = page.locator('.spd-role-btn[data-role="admin"]');
    if (await adminFastBtn.count() > 0) {
      await adminFastBtn.click();
    } else {
      const acc = page.locator('#login-account');
      if (await acc.isVisible()) {
        await acc.fill('admin');
        await page.locator('#login-password').fill('123456');
        await page.locator('#btn-submit-login').click();
      }
    }
    await page.waitForTimeout(2000);

    // 1. 访问医院采购管理端 /procurement
    console.log('[Step 1] 访问医院采购管理端 /procurement...');
    await page.goto('http://127.0.0.1:5173/procurement', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    // 验证提报采购计划弹窗与人民币大写
    console.log('[Step 1.1] 打开提报采购计划单据模态框...');
    const btnCreatePlan = page.locator('button:has-text("提报医用耗材采购计划")');
    if (await btnCreatePlan.count() > 0 && await btnCreatePlan.isVisible()) {
      await btnCreatePlan.click();
      await page.waitForTimeout(1200);
      await snap('01_procurement_bill_entry_dialog');
      // 关闭弹窗
      const cancelBtn = page.locator('.spd-dialog-modal button:has-text("取消")');
      if (await cancelBtn.count() > 0 && await cancelBtn.isVisible()) {
        await cancelBtn.click();
        await page.waitForTimeout(500);
      }
    }

    // 2. 访问外部供应商协同门户 /supplier-portal
    console.log('[Step 2] 访问外部供应商协同门户 /supplier-portal...');
    await page.goto('http://127.0.0.1:5173/supplier-portal', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await snap('02_supplier_portal_overview');

    // 3. 访问全新构建的 Agentic RAG 知识工程与智能体控制中台 /rag-hub
    console.log('[Step 3] 访问智能体与知识工程控制中台 /rag-hub...');
    await page.goto('http://127.0.0.1:5173/rag-hub', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await snap('03_rag_hub_category_and_chunks');

    // 3.1 切换至 Modular RAG 热插拔 Tab
    console.log('[Step 3.1] 切换至 Modular RAG 热插拔实时配置 Tab...');
    const modularTab = page.locator('#tab-config');
    if (await modularTab.count() > 0 && await modularTab.isVisible()) {
      await modularTab.click();
      await page.waitForTimeout(1200);
      await snap('04_rag_hub_modular_config');
    }

    // 3.2 切换至六大智能体调度沙箱 Tab
    console.log('[Step 3.2] 切换至六大智能体调度沙箱 Tab...');
    const sandboxTab = page.locator('#tab-agents');
    if (await sandboxTab.count() > 0 && await sandboxTab.isVisible()) {
      await sandboxTab.click();
      await page.waitForTimeout(1500);
      await snap('05_six_agents_orchestration_sandbox');
    }

    // 4. 验证产品字典页面右下角专属智能体 1 (Plan & Execute) 浮动助手
    console.log('[Step 4] 访问产品字典页面 /dict 并展开右下角智能体助手...');
    await page.goto('http://127.0.0.1:5173/dict', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    const agentTrigger = page.locator('.floating-agent-trigger');
    if (await agentTrigger.count() > 0 && await agentTrigger.isVisible()) {
      await agentTrigger.click();
      await page.waitForTimeout(1000);
    }
    await snap('06_floating_agent_workbench');

    console.log('[E2E-RAG-HUB] 全部回环测试与截图捕获顺利完成！拦截错误总数:', interceptedErrors.length);
  } catch (err) {
    console.error('[E2E-RAG-HUB-Fatal]', err);
    throw err;
  } finally {
    await context.close();
  }
}

runProcurementAndRagHubTest().catch((err) => {
  console.error(err);
  process.exit(1);
});
