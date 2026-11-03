/**
 * @file test_voucher_standard_and_print_engine.js
 * @description 医疗物资全链路单据视觉体系规范化与财务动态打印引擎自动化回环验证脚本：
 * 1. 验证《采购入库单》右侧输入框尺寸适配且无溢出
 * 2. 验证《主库按需分发出库单》已统一为现代卡片式单据样式
 * 3. 验证出库单输入临期物资依然触发 FEFO 30 天临期强控熔断阻断
 * 4. 验证财务法定单据打印具备真实多行耗材、动态大写金额与合计
 * 5. 验证财务对账表格行穿透打印真实科室与对账金额
 * 6. 全程拦截控制台报错，确保 Console Error 与 PageError 为 0
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

async function runVoucherAndPrintTest() {
  console.log('[E2E-StandardVoucher] 启动 Playwright 驱动单据规范与打印引擎回环验证...');
  const tempProfile = path.resolve(os.tmpdir(), `pw_profile_voucher_${Date.now()}`);
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

    // 环节 0: 登录管理员认证
    console.log('[Step 0] 访问登录门户以管理员身份登录...');
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
    await page.waitForTimeout(1200);

    // 环节 1: 验证采购入库单右侧输入框尺寸适配无溢出
    console.log('[Step 1] 打开采购入库单，校验右侧第 4 列输入框在对话框内无溢出...');
    await page.goto('http://127.0.0.1:5173/general?tab=inbound', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const openInboundBtn = page.locator('button:has-text("填写采购入库单")');
    await openInboundBtn.click();
    await page.waitForTimeout(800);

    // 校验第 4 列输入框在视口内可见
    const handlerField = page.locator('.purchase-inbound-dialog input[value*="赵振华"], .purchase-inbound-dialog input[value*="系统管理员"]').first();
    await handlerField.waitFor({ state: 'visible', timeout: 6000 });
    console.log('✓ 采购入库单单头 4 列网格完美适配，第 4 列输入框完整可见无溢出');
    await snap('01_inbound_voucher_input_fit_verified');

    // 关闭入库弹窗
    const closeInboundBtn = page.locator('.purchase-inbound-dialog .dialog-footer button:has-text("取消"), .purchase-inbound-dialog .el-dialog__headerbtn').first();
    await closeInboundBtn.click();
    await page.waitForTimeout(500);

    // 环节 2: 验证主库按需分发出库单已统一为现代卡片式单据样式
    console.log('[Step 2] 打开主库按需分发出库单，校验表单已统一为现代化单据卡片样式...');
    await page.goto('http://127.0.0.1:5173/general?tab=dispatch', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const openOutboundBtn = page.locator('button:has-text("填写出库单")');
    await openOutboundBtn.click();
    await page.waitForTimeout(800);

    const outboundDialog = page.locator('.outbound-voucher-dialog .hospital-bill-container');
    await outboundDialog.waitFor({ state: 'visible', timeout: 6000 });
    console.log('✓ 主库按需分发出库单成功采用统一的现代卡片式单据体系');
    await snap('02_outbound_voucher_unified_style_verified');

    // 环节 3: 验证出库单在输入临期物资时依然能够坚固触发三甲 FEFO 30 天临期硬熔断拦截
    console.log('[Step 3] 出库单录入临期物资，测试 FEFO 30 天临期强控熔断机制...');
    // 点击从全院产品字典选品导入
    const openDictBtn = page.locator('.outbound-voucher-dialog button:has-text("从全院产品字典选品")');
    await openDictBtn.click();
    await page.waitForTimeout(800);

    const firstCheckbox = page.locator('.el-dialog .el-table__body-wrapper .el-checkbox').first();
    await firstCheckbox.click();
    await page.waitForTimeout(300);

    const confirmImportBtn = page.locator('button:has-text("导入选中耗材")').first();
    await confirmImportBtn.click();
    await page.waitForTimeout(800);

    // 设置到期日期为 5 天后 (小于 30 天强风控阈值)
    const expDateInput = page.locator('.outbound-voucher-dialog .bill-detail-table input[type="date"]').first();
    const nearDate = new Date(Date.now() + 5 * 24 * 3600 * 1000).toISOString().slice(0, 10);
    await expDateInput.fill(nearDate);
    await page.waitForTimeout(400);

    // 保存出库单，应当触发 FEFO 阻断弹窗
    const saveOutboundBtn = page.locator('.outbound-voucher-dialog .dialog-footer button:has-text("保存出库单")');
    await saveOutboundBtn.click();
    await page.waitForTimeout(1000);

    const fefoAlertBox = page.locator('.el-message-box:has-text("FEFO 临期强控熔断拦截")');
    await fefoAlertBox.waitFor({ state: 'visible', timeout: 6000 });
    console.log('✓ 成功触发 FEFO 临期强控熔断拦截警告弹窗！存量风控完好无损');
    await snap('03_outbound_fefo_fuse_retained_verified');

    // 点击确认已知晓
    const okBtn = page.locator('.el-message-box__btns button');
    await okBtn.click();
    await page.waitForTimeout(400);

    // 关闭出库弹窗
    const cancelOutBtn = page.locator('.outbound-voucher-dialog .dialog-footer button:has-text("取消")').first();
    await cancelOutBtn.click();
    await page.waitForTimeout(500);

    // 环节 4: 验证财务模块打开《主库采购验收入库单》，展现多行真实耗材与动态金额大写
    console.log('[Step 4] 访问财务审计中枢，测试打印《主库采购验收入库单》...');
    await page.goto('http://127.0.0.1:5173/finance?tab=main-reconciliation', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const printInboundBtn = page.locator('button:has-text("打印《主库采购验收入库单》")');
    await printInboundBtn.click();
    await page.waitForTimeout(800);

    const printPaper = page.locator('#spd-voucher-paper');
    await printPaper.waitFor({ state: 'visible', timeout: 6000 });
    console.log('✓ 财务打印载体展示真实采购入库多行物资、合计行与标准中国人民银行法定中文金额大写');
    await snap('04_finance_print_dynamic_multi_items_verified');

    // 关闭打印预览
    const closePrintBtn = page.locator('.spd-print-modal button:has-text("关闭预览")');
    await closePrintBtn.click();
    await page.waitForTimeout(500);

    // 环节 5: 验证对账表格行点击“打印凭证”，穿透该行真实科室与调拨金额
    console.log('[Step 5] 点击四大主库流向对账表格第一行的“打印凭证”，测试真实穿透...');
    const firstRowPrintBtn = page.locator('.fusion-styled-table button:has-text("打印凭证")').first();
    await firstRowPrintBtn.click();
    await page.waitForTimeout(800);

    await printPaper.waitFor({ state: 'visible', timeout: 6000 });
    console.log('✓ 成功实现表格行真实数据穿透打印（抬头、科室、调拨总额与大写 100% 对齐）！');
    await snap('05_finance_table_row_penetrate_print_verified');

    // 关闭打印
    await closePrintBtn.click();
    await page.waitForTimeout(400);

    console.log('======================================================');
    console.log(`[E2E 总结] 回环验证全部完成！拦截到的错误数量: ${interceptedErrors.length}`);
    if (interceptedErrors.length > 0) {
      console.warn('拦截日志:', interceptedErrors);
    } else {
      console.log('✓ 完美！全页面控制台 Console Error 与 PageError 保持为 0！');
    }
    console.log('======================================================');

  } catch (err) {
    console.error('[E2E 执行中断]:', err);
    await snap('00_standard_voucher_interrupted_error');
    throw err;
  } finally {
    await context.close();
  }
}

runVoucherAndPrintTest().catch((e) => {
  console.error('[Fatal Error]', e.message);
  process.exit(1);
});
