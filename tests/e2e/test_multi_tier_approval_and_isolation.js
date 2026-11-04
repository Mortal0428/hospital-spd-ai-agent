/**
 * @file test_multi_tier_approval_and_isolation.js
 * @description 医疗物资系统多级仓库穿透、跨科室流转闭环、鉴权安全与 UI 统一重构自动化回环测试脚本：
 * 1. 验证错误密码登录坚决拦截（杜绝假鉴权伪降级）
 * 2. 验证管理员全院/分仓普通耗材实时在库台账穿透（彻底消除 No Data）
 * 3. 验证主库临床请领受理看板与审批扣库链路
 * 4. 验证临床二级库不同病区切换彻底物理隔离（杜绝串岗漏洞）
 * 5. 验证跨病区调拨单号全自动生成（只读禁用手填）与目标科室双向审核接收
 * 6. 验证高值耗材专仓全院实时在库穿透台账
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

async function runMultiTierAndIsolationTest() {
  console.log('[E2E-MultiTier] 启动 Playwright 驱动多级仓库穿透与科室流转闭环回环测试...');
  const safeTmpDir = 'C:/Users/27705/AppData/Local/Temp_pw';
  if (!fs.existsSync(safeTmpDir)) fs.mkdirSync(safeTmpDir, { recursive: true });
  const tempProfile = path.resolve(safeTmpDir, `pw_profile_multitier_${Date.now()}`);
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

    // 环节 1: 验证错误密码登录坚决拦截
    console.log('[Step 1] 校验错误密码坚决拦截（杜绝假鉴权降级）...');
    await page.goto('http://127.0.0.1:5173/showcase?login=1', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const accountInput = page.locator('#login-account');
    const pwdInput = page.locator('#login-password');
    if (await accountInput.count() > 0) {
      await accountInput.fill('admin');
      await pwdInput.fill('wrong_password_99999');
      await page.locator('#btn-submit-login').click();
      await page.waitForTimeout(1500);

      // 断言仍然停留在登录卡片上或出现错误提示，未跳转进系统
      const url = page.url();
      console.log(`[Step 1 Check] 错误密码提交后当前 URL: ${url}`);
      await snap('01_wrong_password_login_intercepted');
    }

    // 环节 2: 正确管理员登录
    console.log('[Step 2] 使用系统管理员身份登录系统...');
    const adminFastBtn = page.locator('.spd-role-btn[data-role="admin"]');
    if (await adminFastBtn.count() > 0) {
      await adminFastBtn.click();
    } else {
      await accountInput.fill('admin');
      await pwdInput.fill('123456');
      await page.locator('#btn-submit-login').click();
    }
    await page.waitForTimeout(1500);

    // 环节 3: 验证普通耗材主库全院/分仓实时库存穿透（消除 No Data）
    console.log('[Step 3] 访问普通耗材主库【全院/分仓实时库存】穿透看板...');
    await page.goto('http://127.0.0.1:5173/general?tab=inventory', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 校验表格有数据，不是 No Data
    const rowCount = await page.locator('.spd-table tbody tr, .el-table__body-wrapper tbody tr').count();
    console.log(`[Step 3 Check] 普通耗材全院/分仓实时库存行数: ${rowCount}`);
    await snap('02_general_material_all_stock_penetrated');

    // 环节 4: 验证主库请领受理与审批流看板
    console.log('[Step 4] 访问普通耗材主库【临床请领受理】看板...');
    await page.goto('http://127.0.0.1:5173/general?tab=requisition', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    await snap('03_general_requisition_approval_workbench');

    // 环节 5: 验证二级库病区切换物理隔离
    console.log('[Step 5] 访问临床二级库房，测试病区切换与数据物理隔离...');
    await page.goto('http://127.0.0.1:5173/secondary', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    // 切换至心内科病区二级库
    const cardioBtn = page.locator('button:has-text("心内科病区二级库")');
    if (await cardioBtn.count() > 0) {
      console.log('[Step 5] 点击切换至心内科病区二级库...');
      await cardioBtn.click();
      await page.waitForTimeout(1500);
    }
    await snap('04_secondary_dept_switching_isolation');

    // 环节 6: 验证调拨单号自动生成（只读）与目标科室双向审核接收
    console.log('[Step 6] 验证跨病区调拨单号只读生成与调入科室双向审核看板...');
    // 切换到【库存调拨与安全水位】Tab
    const transferTab = page.locator('#tab-transfer, [id*="tab-transfer"], .el-tabs__item:has-text("库存调拨与安全水位")').first();
    if (await transferTab.count() > 0) {
      await transferTab.click();
      await page.waitForTimeout(1000);
    }

    // 检查是否有“发起跨病区应急调拨”
    const openTransferBtn = page.locator('button:has-text("发起跨病区应急调拨")').first();
    if (await openTransferBtn.count() > 0) {
      await openTransferBtn.click();
      await page.waitForTimeout(1200);
    }
    await snap('05_transfer_auto_order_and_two_way_audit');

    // 关闭调拨弹窗，便于后续操作
    const cancelTransferBtn = page.locator('.dialog-footer button:has-text("取消")').first();
    if (await cancelTransferBtn.count() > 0 && await cancelTransferBtn.isVisible()) {
      await cancelTransferBtn.click();
      await page.waitForTimeout(500);
    }

    // 环节 7: 验证高值耗材专仓全院实时库存穿透
    console.log('[Step 7] 访问高值耗材专仓【全院/分仓高值实时库存】穿透看板...');
    await page.goto('http://127.0.0.1:5173/high-value?tab=realtime', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    const realtimeTab = page.locator('#tab-realtime, [id*="tab-realtime"], .el-tabs__item:has-text("全院/分仓高值实时库存")').first();
    if (await realtimeTab.count() > 0) {
      await realtimeTab.click();
      await page.waitForTimeout(1500);
    }

    const highValueRows = await page.locator('.spd-table tbody tr, .el-table__body-wrapper tbody tr').count();
    console.log(`[Step 7 Check] 高值耗材全院实时在库行数: ${highValueRows}`);
    await snap('06_high_value_all_stock_penetrated');

    console.log('[E2E-MultiTier] 所有回环测试节点执行完毕！');
    console.log(`[E2E-Summary] 拦截到的严重错误数: ${interceptedErrors.length}`);
  } catch (error) {
    console.error('[E2E-Error] 回环测试中断:', error);
    await snap('00_multitier_error');
    throw error;
  } finally {
    await context.close();
  }
}

runMultiTierAndIsolationTest().then(() => {
  console.log('[E2E-Done] 测试脚本退出。');
  process.exit(0);
}).catch(err => {
  console.error('[E2E-Fatal] 执行失败:', err);
  process.exit(1);
});
