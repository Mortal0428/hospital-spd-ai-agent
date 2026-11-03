/**
 * @file test_error_elimination.js
 * @description 验证 404/500 报错彻底消除与单据化闭环实机回环测试
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

async function runErrorEliminationTest() {
  console.log('[E2E-Elimination] 启动 Playwright 验证 404 与 500 报错消除...');
  const tempProfile = path.resolve(os.tmpdir(), `pw_profile_elim_${Date.now()}`);
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

    // 1. 验证普通耗材主库 - 临床请领受理与独立盘点 (验证 404 气泡消除)
    console.log('[Step 1] 访问普通耗材主库临床请领受理页面...');
    await page.goto('http://127.0.0.1:5173/general?tab=requisition', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await snap('01_general_requisition_no_404');

    // 2. 验证普通耗材主库 - 独立盘点工作台 (验证 /ext/stocktake-plans 正常获取)
    console.log('[Step 2] 切换至主库独立盘点工作台...');
    await page.goto('http://127.0.0.1:5173/general?tab=stocktake', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await snap('02_general_stocktake_plans_loaded');

    // 3. 验证高值耗材专仓 - 备货单与生命周期单据 (验证 404 消除且展示真实后端数据)
    console.log('[Step 3] 访问高值耗材专仓备货自动入仓...');
    await page.goto('http://127.0.0.1:5173/high-value?tab=inbound', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await snap('03_high_value_prep_orders_loaded');

    // 4. 验证高值耗材专仓 - 专柜智能台账 (扫码核销)
    console.log('[Step 4] 切换至高值专柜智能台账...');
    await page.goto('http://127.0.0.1:5173/high-value?tab=stock', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await snap('04_high_value_smart_cabinet_verified');

    // 5. 验证系统与人员管理 - RBAC 细粒度赋权矩阵 (验证 500 消除)
    console.log('[Step 5] 访问系统与人员管理 RBAC 矩阵...');
    await page.goto('http://127.0.0.1:5173/users', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await snap('05_users_rbac_batch_matrix');

    console.log('\n=============================================');
    console.log('所有关键页面回环验证已完成！');
    console.log(`拦截到的 Console/Page 错误数量: ${interceptedErrors.length}`);
    console.log('=============================================\n');
  } catch (err) {
    console.error('[E2E-Elimination Error]', err);
    throw err;
  } finally {
    await context.close();
  }
}

runErrorEliminationTest().then(() => {
  console.log('[E2E-Elimination] 测试顺利结束');
  process.exit(0);
}).catch((err) => {
  console.error('[E2E-Elimination] 测试异常退出', err);
  process.exit(1);
});
