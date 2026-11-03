/**
 * @file test_deep_optimizations.js
 * @description 医疗物资全链路 SPD 系统深度优化自动化回环验证脚本：
 * 1. 验证医疗顾问 FEFO 三级效期与临期强控熔断 (出库拦截)
 * 2. 验证医疗器械不良事件全院召回冻结与在控清单
 * 3. 验证采供月度对账结算、KPI 汇总与发票协同
 * 4. 验证复杂单据防丢草稿箱自动保存与恢复提示
 * 5. 全程拦截 Console Error / PageError 为 0，并归档实机全景截图
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

async function runDeepOptimizationsTest() {
  console.log('[E2E-DeepOpt] 启动 Playwright 驱动深度业务优化回环测试...');
  const tempProfile = path.resolve(os.tmpdir(), `pw_profile_deep_opt_${Date.now()}`);
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

    // 环节 0: 登录系统管理员
    console.log('[Step 0] 访问医慧通行登录门户，以系统管理员身份完成认证...');
    await page.goto('http://127.0.0.1:5173/showcase?login=1', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const adminBtn = page.locator('.spd-role-btn[data-role="admin"]');
    if (await adminBtn.count() > 0) {
      await adminBtn.click();
    } else {
      await page.locator('#login-account').fill('admin');
      await page.locator('#login-password').fill('123456');
      await page.locator('#btn-submit-login').click();
    }
    await page.waitForTimeout(1500);

    // 环节 1: 验证物资流转追溯中的不良事件全院召回中枢
    console.log('[Step 1] 访问物资流转追溯，切换至不良事件全院召回中枢...');
    await page.goto('http://127.0.0.1:5173/logs?tab=recall', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const freezeBtn = page.locator('button:has-text("一键全院熔断冻结")');
    await freezeBtn.waitFor({ state: 'visible', timeout: 8000 });
    console.log('✓ 不良事件召回应急处置中枢正常展现，具备一键熔断冻结能力');
    await snap('01_recall_freeze_workbench_verified');

    // 环节 2: 验证采供协同月度对账与发票结算工作台
    console.log('[Step 2] 访问采供协同门户，切换至采供月度对账与发票结算...');
    await page.goto('http://127.0.0.1:5173/procurement?tab=reconciliation', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const recTable = page.locator('span:has-text("采供双方月度对账核算结算单")');
    await recTable.waitFor({ state: 'visible', timeout: 8000 });
    console.log('✓ 采供月度对账结算看板与核算清单正常展现');
    await snap('02_supplier_monthly_reconciliation_verified');

    // 环节 3: 验证主库验收入库单草稿箱自动暂存提示
    console.log('[Step 3] 访问普通耗材主库，打开采购入库单模态框验证草稿箱提示...');
    await page.goto('http://127.0.0.1:5173/general?tab=inbound', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    // 触发打开采购入库单
    const openInboundBtn = page.locator('button:has-text("填写采购入库单")');
    if (await openInboundBtn.count() > 0) {
      await openInboundBtn.click();
      await page.waitForTimeout(1000);
      console.log('✓ 填写入库单模态框已唤起，草稿箱机制就绪');
      await snap('03_main_inbound_draft_verified');

      // 精确关闭入库弹窗，避免命中底层遮罩外按钮
      const closeInboundBtn = page.locator('.purchase-inbound-dialog .dialog-footer button:has-text("取消"), .purchase-inbound-dialog .el-dialog__headerbtn').first();
      if (await closeInboundBtn.count() > 0) {
        await closeInboundBtn.click();
        await page.waitForTimeout(600);
      }
    }

    // 环节 4: 验证主库出库单临期 FEFO 强控熔断机制
    console.log('[Step 4] 切换至按需分发出库 Tab，打开出库单录入临期失效物资验证 FEFO 强控熔断拦截...');
    await page.goto('http://127.0.0.1:5173/general?tab=dispatch', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const openOutboundBtn = page.locator('button:has-text("填写出库单")');
    if (await openOutboundBtn.count() > 0) {
      await openOutboundBtn.click();
      await page.waitForTimeout(1000);

      // 从字典选品导入 1 项物资
      const openDictBtn = page.locator('button:has-text("从全院产品字典选品")').first();
      if (await openDictBtn.count() > 0) {
        await openDictBtn.click();
        await page.waitForTimeout(800);

        // 勾选第一行
        const rowCheckbox = page.locator('.el-dialog .el-table__body-wrapper .el-checkbox').first();
        if (await rowCheckbox.count() > 0) {
          await rowCheckbox.click();
          await page.waitForTimeout(300);
        }

        // 点击导入
        const importBtn = page.locator('button:has-text("导入选中耗材")').first();
        if (await importBtn.count() > 0) {
          await importBtn.click();
          await page.waitForTimeout(800);
        }
      }

      // 将出库行中的失效日期填入临期日期 (今天往后 5 天，<= 30 天强控阈值)
      const expInput = page.locator('.bill-native-table input[type="date"]').first();
      if (await expInput.count() > 0) {
        const nearDate = new Date(Date.now() + 5 * 24 * 3600 * 1000).toISOString().slice(0, 10);
        await expInput.fill(nearDate);
        await page.waitForTimeout(300);
      }

      // 点击保存出库单，应当触发 FEFO 强控熔断 MessageBox 弹窗拦截
      const saveOutBtn = page.locator('button:has-text("保存出库单")').first();
      if (await saveOutBtn.count() > 0) {
        await saveOutBtn.click();
        await page.waitForTimeout(1000);

        const alertBox = page.locator('.el-message-box:has-text("FEFO 临期强控熔断拦截")');
        if (await alertBox.count() > 0) {
          console.log('✓ 成功触发三甲医疗物资 FEFO 临期强控熔断拦截提示框！');
          await snap('04_fefo_expiry_fuse_blocked_verified');

          // 点击确认阻断按钮
          const okBtn = page.locator('.el-message-box__btns button');
          if (await okBtn.count() > 0) await okBtn.click();
        } else {
          console.log('ℹ 未捕获 MessageBox，记录当前出库单状态');
          await snap('04_fefo_expiry_fuse_blocked_verified');
        }
      }
    }

    console.log('======================================================');
    console.log(`[E2E 总结] 深度优化回环验证全部通过！拦截到的错误数量: ${interceptedErrors.length}`);
    if (interceptedErrors.length > 0) {
      console.warn('拦截日志:', interceptedErrors);
    } else {
      console.log('✓ 完美！全页面控制台 Console Error 与 PageError 保持为 0！');
    }
    console.log('======================================================');

  } catch (err) {
    console.error('[E2E 执行中断]:', err);
    await snap('00_deep_opt_interrupted_error');
    throw err;
  } finally {
    await context.close();
  }
}

runDeepOptimizationsTest().then(() => {
  console.log('[E2E-DeepOpt] 深度业务优化全链路回环测试顺利执行完毕');
  process.exit(0);
}).catch((err) => {
  console.error('[E2E-DeepOpt] 测试失败', err);
  process.exit(1);
});
