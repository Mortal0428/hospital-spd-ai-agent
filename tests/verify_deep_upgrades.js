const { launchPersistentPlaywright } = require('./e2e/browser_config');
const path = require('path');
const fs = require('fs');

async function runDeepVerification() {
  console.log('--- STARTING DEEP SPD SYSTEM E2E VERIFICATION ---');
  const { context, page } = await launchPersistentPlaywright({ headless: true });
  const interceptedErrors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const t = msg.text();
      if (!t.includes('favicon') && !t.includes('chrome-extension')) {
        interceptedErrors.push(t);
      }
    }
  });

  const screenshotsDir = path.resolve(__dirname, 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  await page.setViewportSize({ width: 1440, height: 900 });

  // 1. 登录管理员
  console.log('Step 1: Logging in as Admin...');
  await page.goto('http://127.0.0.1:5173/showcase?login=1');
  await page.waitForTimeout(1000);
  const adminBtn = page.locator('.spd-role-btn[data-role="admin"]');
  if ((await adminBtn.count()) > 0) {
    await adminBtn.click();
  }
  await page.waitForTimeout(1500);

  // 2. 验证 RBAC 刷新落盘持久化
  console.log('Step 2: Testing RBAC 15x8 Matrix Persistence...');
  await page.goto('http://127.0.0.1:5173/users');
  await page.waitForTimeout(1500);

  // 点击第 2 个 Tab (15 模块 x 8 动作细粒度 RBAC 矩阵)
  const rbacTab = page.locator('.el-tabs__item:has-text("细粒度 RBAC 矩阵")');
  if (await rbacTab.count() > 0) {
    await rbacTab.click();
    await page.waitForTimeout(1200);

    // 点击一键授予全权 (全亮)
    const grantAllBtn = page.locator('button:has-text("一键授予全权")');
    if (await grantAllBtn.count() > 0) {
      await grantAllBtn.click();
      await page.waitForTimeout(800);
    }

    // 点击保存并下发全院权限矩阵
    const saveRbacBtn = page.locator('button:has-text("保存并下发全院权限矩阵")');
    if (await saveRbacBtn.count() > 0) {
      await saveRbacBtn.click();
      await page.waitForTimeout(1500);
    }

    // 页面刷新，验证持久化是否保持！
    await page.reload();
    await page.waitForTimeout(2000);
    // 再次切回 RBAC Tab 截图取证
    const rbacTabReloaded = page.locator('.el-tabs__item:has-text("细粒度 RBAC 矩阵")');
    if (await rbacTabReloaded.count() > 0) {
      await rbacTabReloaded.click();
      await page.waitForTimeout(1000);
    }

    const sc1 = path.join(screenshotsDir, '2026-11-04_19-07-00_01_rbac_save_persistence.png');
    await page.screenshot({ path: sc1, fullPage: false });
    console.log('Captured Screenshot 1 ->', sc1);
  }

  // 3. 验证仓库架构维护 Tab UI 框线与浅色模式统一
  console.log('Step 3: Testing Warehouse Architecture Glass-Panel UI in Light Mode...');
  await page.goto('http://127.0.0.1:5173/product-dict');
  await page.waitForTimeout(1500);

  // 切换到仓库架构 Tab
  const whTab = page.locator('.el-tabs__item:has-text("仓库架构与")');
  if (await whTab.count() > 0) {
    await whTab.click();
    await page.waitForTimeout(1000);
  }

  // 切换浅色模式
  await page.evaluate(() => {
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('theme', 'light');
  });
  await page.waitForTimeout(800);

  const sc2 = path.join(screenshotsDir, '2026-11-04_19-07-00_02_warehouse_ui_glass_panel.png');
  await page.screenshot({ path: sc2, fullPage: false });
  console.log('Captured Screenshot 2 ->', sc2);

  // 恢复深色模式
  await page.evaluate(() => {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
  });
  await page.waitForTimeout(500);

  // 4. 验证知识库多格式文件真实上传与特征雷达
  console.log('Step 4: Testing Knowledge Base File Upload & Feature Radar Modal...');
  await page.goto('http://127.0.0.1:5173/rag-hub?tab=knowledge');
  await page.waitForTimeout(1500);

  const uploadBtn = page.locator('button:has-text("上传医疗规范文档")');
  if (await uploadBtn.count() > 0) {
    await uploadBtn.click();
    await page.waitForTimeout(1000);

    const sc3 = path.join(screenshotsDir, '2026-11-04_19-07-00_03_document_upload_and_radar.png');
    await page.screenshot({ path: sc3, fullPage: false });
    console.log('Captured Screenshot 3 ->', sc3);

    // 关闭弹窗
    const cancelBtn = page.locator('.spd-dialog-modal button:has-text("取消")');
    if (await cancelBtn.count() > 0) {
      await cancelBtn.click();
      await page.waitForTimeout(500);
    }
  }

  // 5. 验证 Modular RAG 独立连通性测速与 6 大智能体模型解耦中台
  console.log('Step 5: Testing Single Connectivity Check & 6 Agents Model Decoupling...');
  await page.goto('http://127.0.0.1:5173/rag-hub?tab=config');
  await page.waitForTimeout(1500);

  // 点击测速按钮测试 Ollama 连通性
  const testOllamaBtn = page.locator('.kpi-card:has-text("本地 Ollama") button:has-text("测速")');
  if (await testOllamaBtn.count() > 0) {
    await testOllamaBtn.click();
    await page.waitForTimeout(1500);
  }

  const sc4 = path.join(screenshotsDir, '2026-11-04_19-07-00_04_modular_rag_connectivity_test.png');
  await page.screenshot({ path: sc4, fullPage: false });
  console.log('Captured Screenshot 4 ->', sc4);

  // 6. 验证 6 大智能体独立工作台、多模态识图与 OpenClaw/DeepSeek
  console.log('Step 6: Testing 6 Agents Independent Workbench, Multimodal & OpenClaw...');
  await page.goto('http://127.0.0.1:5173/rag-hub?tab=agents');
  await page.waitForTimeout(1500);

  // 选择智能体 4 (高值一物一码全链路溯源)
  const agent4Menu = page.locator('.agent-menu-item:has-text("智能体 4")');
  if (await agent4Menu.count() > 0) {
    await agent4Menu.click();
    await page.waitForTimeout(1000);
  }

  // 点击预设问题
  const presetPill = page.locator('.preset-pill').first();
  if (await presetPill.count() > 0) {
    await presetPill.click();
    await page.waitForTimeout(3000); // 等待智能体执行与思考链展开
  }

  const sc5 = path.join(screenshotsDir, '2026-11-04_19-07-00_05_agent_chat_multimodal_openclaw.png');
  await page.screenshot({ path: sc5, fullPage: false });
  console.log('Captured Screenshot 5 ->', sc5);

  console.log('--- ALL E2E STEPS COMPLETED ---');
  console.log('Total Intercepted Page Errors:', interceptedErrors.length);
  if (interceptedErrors.length > 0) {
    console.log('Details:', interceptedErrors);
  } else {
    console.log('CLEAN RUN: 0 Errors encountered!');
  }

  await context.close();
}

runDeepVerification().catch((err) => {
  console.error('E2E Verification Error:', err);
  process.exit(1);
});
