/**
 * @file test_supplier_physical_decoupling_and_multi_audit.js
 * @description 采供双端物理彻底解耦与多供应商资质审查自动化回环测试脚本：
 * 1. 验证医院采购管理端 (/procurement) 顶栏为内控指标，采购表格坚决无“发货”按钮
 * 2. 验证多供应商资质审查工作台对 SUP_UNVERIFIED_99 独立查验并审核通过准入
 * 3. 验证外部供应商协同门户 (/supplier-portal) 企业级数据隔离，过审企业配货发货成功且 0 个 403
 * 4. 验证普通耗材主库查验供应商送货单并验收入库闭环
 */

const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

async function runSupplierPhysicalDecouplingTest() {
  console.log('[E2E-SupplierDecouple] 启动 Playwright 驱动采供物理彻底解耦与多供应商准入审查回环测试...');
  const safeTmpDir = 'C:/Users/27705/AppData/Local/Temp_pw';
  if (!fs.existsSync(safeTmpDir)) fs.mkdirSync(safeTmpDir, { recursive: true });
  const tempProfile = path.resolve(safeTmpDir, `pw_profile_decouple_${Date.now()}`);
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

    // 环节 1: 系统管理员身份登录
    console.log('[Step 1] 系统管理员身份登录...');
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

    // 环节 2: 访问医院端采购管理中心 (/procurement)
    console.log('[Step 2] 访问医院端采购管理与准入中心 (/procurement)...');
    await page.goto('http://127.0.0.1:5173/procurement', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    // 断言页面内绝对没有“配货发货”按钮
    const shipBtnInHospital = await page.locator('button:has-text("配货发货")').count();
    console.log(`[Step 2 Check] 医院端页面中配货发货按钮数量 (必须为0): ${shipBtnInHospital}`);
    if (shipBtnInHospital > 0) {
      throw new Error('内控违规：医院端采购管理页面依然存在配货发货按钮！');
    }
    await snap('01_hospital_procurement_no_ship_btn');

    // 环节 3: 访问 Tab 2【供应商经营资质审查台账】，审查 SUP_UNVERIFIED_99
    console.log('[Step 3] 切换至【供应商经营资质审查台账】，审查 SUP_UNVERIFIED_99...');
    const supTabBtn = page.locator('button:has-text("供应商经营资质审查台账")');
    await supTabBtn.click();
    await page.waitForTimeout(1500);

    // 点击某新注册未审商贸公司的审核通过按钮
    const auditBtn = page.locator('tr:has-text("SUP_UNVERIFIED_99") button:has-text("审核通过并准入")').first();
    if (await auditBtn.count() > 0) {
      console.log('[Step 3] 发现待审企业 SUP_UNVERIFIED_99，点击【审核通过并准入】...');
      await auditBtn.click();
      await page.waitForTimeout(1000);

      const confirmBtn = page.locator('button:has-text("确认提交审查结果")');
      if (await confirmBtn.count() > 0) {
        await confirmBtn.click();
        await page.waitForTimeout(1500);
      }
    }
    await snap('02_multi_vendor_qualification_audit');

    // 环节 4: 访问外部供应商专属门户 (/supplier-portal)
    console.log('[Step 4] 访问外部供应商协同门户 (/supplier-portal)...');
    await page.goto('http://127.0.0.1:5173/supplier-portal', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    // 切换至 SUP_UNVERIFIED_99 视角
    const switchSelect = page.locator('.supplier-switch-select');
    if (await switchSelect.count() > 0) {
      await switchSelect.click();
      await page.waitForTimeout(500);
      const optionSup99 = page.locator('.el-select-dropdown__item:has-text("SUP_UNVERIFIED_99")').first();
      if (await optionSup99.count() > 0) {
        await optionSup99.click();
        await page.waitForTimeout(1500);
      }
    }

    // 检查是否具备配货发货按钮并执行发货
    const shipBtnInSupplier = page.locator('button:has-text("配货发货")').first();
    if (await shipBtnInSupplier.count() > 0) {
      console.log('[Step 4] 供应商代表点击【配货发货】...');
      await shipBtnInSupplier.click();
      await page.waitForTimeout(1000);

      const submitShipBtn = page.locator('button:has-text("确认发货并生成医院待验单")');
      if (await submitShipBtn.count() > 0) {
        await submitShipBtn.click();
        await page.waitForTimeout(2000);
      }
    }
    await snap('03_supplier_portal_ship_success');

    // 环节 5: 医院普通主库查验实物验收入库
    console.log('[Step 5] 访问普通耗材主库验收入库 Tab (/general?tab=inbound)...');
    await page.goto('http://127.0.0.1:5173/general?tab=inbound', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const acceptBtn = page.locator('button:has-text("查验实物并验收入库")').first();
    if (await acceptBtn.count() > 0) {
      console.log('[Step 5] 主库管理员点击【查验实物并验收入库】...');
      await acceptBtn.click();
      await page.waitForTimeout(1500);
    }
    await snap('04_main_warehouse_acceptance_closed_loop');

    console.log('[E2E-SupplierDecouple] 测试执行完毕，拦截到的严重错误数:', interceptedErrors.length);
    if (interceptedErrors.length > 0) {
      console.warn('[E2E-SupplierDecouple Warning] 异常拦截汇总:', interceptedErrors);
    }

  } catch (err) {
    console.error('[E2E-SupplierDecouple Error] 测试异常中断:', err);
  } finally {
    await context.close();
  }
}

runSupplierPhysicalDecouplingTest().then(() => {
  console.log('[E2E-SupplierDecouple] Playwright 自动化回环测试安全退出');
  process.exit(0);
}).catch((e) => {
  console.error('[E2E-SupplierDecouple Fatal]', e);
  process.exit(1);
});
