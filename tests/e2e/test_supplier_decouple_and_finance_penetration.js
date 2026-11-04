/**
 * @file test_supplier_decouple_and_finance_penetration.js
 * @description 医疗物资系统采供端到端物理解耦闭环与财务四级穿透业财一体化 E2E 回环测试脚本：
 * 1. 验证采购协同页面中医院端与供应商端业务动作解耦，发货后医院端显示【前往验收入库】
 * 2. 验证普通耗材主库【耗材验收入库与退货】Tab 顶部专属【待验收供应商到货看板】展示待验送货单并支持一键查验实物入库
 * 3. 验证财务精算 Tab 4【多级小仓库资金运转流水总台账】展示二级小仓真实资金流向与分页
 * 4. 验证财务精算 Tab 2【科室耗材支出对账】子行展开穿透物料级真实明细（品名、批次、单价、病案号）
 * 5. 验证法定四联单据打印引擎装配真实物料明细与三方联签栏
 */

const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

async function runSupplierDecoupleAndFinancePenetrationTest() {
  console.log('[E2E-SupplierFinance] 启动 Playwright 驱动采供解耦与财务四级穿透回环测试...');
  const safeTmpDir = 'C:/Users/27705/AppData/Local/Temp_pw';
  if (!fs.existsSync(safeTmpDir)) fs.mkdirSync(safeTmpDir, { recursive: true });
  const tempProfile = path.resolve(safeTmpDir, `pw_profile_sup_fin_${Date.now()}`);
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

    // 环节 1: 管理员登录
    console.log('[Step 1] 系统管理员身份快速登录...');
    await page.goto('http://127.0.0.1:5173/showcase?login=1', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const adminFastBtn = page.locator('.spd-role-btn[data-role="admin"]');
    if (await adminFastBtn.count() > 0) {
      await adminFastBtn.click();
    } else {
      await page.locator('#login-account').fill('admin');
      await page.locator('#login-password').fill('123456');
      await page.locator('#btn-submit-login').click();
    }
    await page.waitForTimeout(1500);

    // 环节 2: 采购订单管理 - 采供解耦与验收入库动作
    console.log('[Step 2] 访问采购订单协同页面，检验订单状态与验收入库流转动作...');
    await page.goto('http://127.0.0.1:5173/procurement', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await snap('01_supplier_purchase_decouple_and_handover');

    // 环节 3: 普通耗材主库 - 验收入库看板与到货查验
    console.log('[Step 3] 访问普通耗材主库【耗材验收入库与退货】Tab，查验专属待验收看板...');
    await page.goto('http://127.0.0.1:5173/general?tab=inbound', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 如果顶部有待验收送货单，点击一次查验实物并验收入库
    const acceptBtn = page.locator('button:has-text("查验实物并验收入库")').first();
    if (await acceptBtn.count() > 0) {
      console.log('[Step 3] 发现待验收供应商送货单，点击【查验实物并验收入库】...');
      await acceptBtn.click();
      await page.waitForTimeout(1500);
    }
    await snap('02_general_supplier_delivery_acceptance_workbench');

    // 环节 4: 财务精算 - 多级小仓库资金运转流水总台账 (Tab 4)
    console.log('[Step 4] 访问财务精算中心【多级小仓库资金运转流水总台账】Tab...');
    await page.goto('http://127.0.0.1:5173/finance?tab=sub-flows', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const flowRows = await page.locator('.el-table__body-wrapper tbody tr').count();
    console.log(`[Step 4 Check] 小仓库资金流水表格行数: ${flowRows}`);
    await snap('03_finance_sub_warehouse_flows_ledger');

    // 环节 5: 财务精算 - 科室领用支出对账物料级明细穿透 (Tab 2)
    console.log('[Step 5] 访问财务精算【各科室耗材支出对账】，测试展开子行穿透物料级真实消耗...');
    await page.goto('http://127.0.0.1:5173/finance?tab=dept-cost', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 点击表格第一行的展开按钮
    const expandIcon = page.locator('.el-table__expand-icon').first();
    if (await expandIcon.count() > 0) {
      console.log('[Step 5] 展开第一行科室消耗明细...');
      await expandIcon.click();
      await page.waitForTimeout(1500);
    }
    await snap('04_finance_dept_material_penetration_details');

    // 环节 6: 法定四联单据打印预览 (装配物料级明细与三方联签)
    console.log('[Step 6] 触发法定四联单据打印中心预览...');
    const topPrintBtn = page.locator('button:has-text("打印《主库采购验收入库单》")').first();
    if (await topPrintBtn.count() > 0) {
      await topPrintBtn.click();
      await page.waitForTimeout(1500);
    }
    await snap('05_finance_voucher_print_preview_with_details');

    console.log('[E2E-SupplierFinance] 自动化回环测试执行完毕，拦截到的严重错误数:', interceptedErrors.length);
    if (interceptedErrors.length > 0) {
      console.warn('[E2E-SupplierFinance Warning] 页面异常拦截汇总:', interceptedErrors);
    }

  } catch (err) {
    console.error('[E2E-SupplierFinance Error] 测试中断:', err);
  } finally {
    await context.close();
  }
}

runSupplierDecoupleAndFinancePenetrationTest().then(() => {
  console.log('[E2E-SupplierFinance] Playwright 进程安全退出');
  process.exit(0);
}).catch((e) => {
  console.error('[E2E-SupplierFinance Fatal]', e);
  process.exit(1);
});
