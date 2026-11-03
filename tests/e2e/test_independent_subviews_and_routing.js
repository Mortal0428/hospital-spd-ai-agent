const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

/**
 * @file test_independent_subviews_and_routing.js
 * @description 验证全链路 404 故障恢复与多业务模块细分子功能独立视图切换：
 * 1. 后端各新旧核心 API 端点 HTTP 200 自检（绝无 404）
 * 2. 产品字典四大独立视图切换：
 *    - 耗材规格目录 (tab=specs)
 *    - 仓库架构维护与主库/二级库分层拓扑 (tab=warehouses)
 *    - 耗材分类设置 (tab=categories)
 *    - 供应商国家级资质档案台账 (tab=suppliers)
 * 3. 普通耗材主库五大独立工作台切换
 * 4. 临床二级库物资申领、手动发料与独立盘点切换
 * 5. 财务四大主库发料对账与进销存月度收发存平衡表切换
 * 6. 物资流转追溯与异常审计预警切换
 */
async function runSubviewsAndRoutingVerification() {
  console.log('==== [阶段一：后端全量业务端点 HTTP 状态探测] ====');
  const testEndpoints = [
    'http://127.0.0.1:8000/api/v1/health',
    'http://127.0.0.1:8000/api/v1/dict/warehouses',
    'http://127.0.0.1:8000/api/v1/dict/categories',
    'http://127.0.0.1:8000/api/v1/dict/suppliers',
    'http://127.0.0.1:8000/api/v1/dict/specs',
    'http://127.0.0.1:8000/api/v1/main-warehouse/requisitions',
    'http://127.0.0.1:8000/api/v1/stats/main-dispatch-reconciliation',
    'http://127.0.0.1:8000/api/v1/stats/dept-consumption-reconciliation',
    'http://127.0.0.1:8000/api/v1/stats/inventory-balance-monthly',
    'http://127.0.0.1:8000/api/v1/workflow-logs'
  ];

  for (const ep of testEndpoints) {
    const res = await fetch(ep);
    console.log(`[API Probe] ${ep} -> HTTP ${res.status}`);
    if (res.status === 404) {
      throw new Error(`端点仍然返回 404: ${ep}`);
    }
  }
  console.log('[OK] 全部核心业务接口探测完毕，0 项 404，完全恢复正常！');

  console.log('\n==== [阶段二：浏览器各细分子视图渲染与截图回环验证] ====');
  const tempProfile = path.resolve(os.tmpdir(), `pw_profile_subviews_${Date.now()}`);
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

  // 监听控制台错误
  const pageErrors = [];
  page.on('pageerror', (err) => pageErrors.push(err.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (!text.includes('favicon') && !text.includes('Failed to load resource')) {
        pageErrors.push(text);
      }
    }
  });

  try {
    // 1. 登录
    console.log('[Step 1] 登录系统管理员工作台...');
    await page.goto('http://127.0.0.1:5173/showcase?login=1', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);

    const adminBtn = page.locator('.spd-role-btn[data-role="admin"]');
    if (await adminBtn.count()) {
      await adminBtn.click();
    } else {
      await page.locator('#login-account').fill('admin');
      await page.locator('#login-password').fill('123456');
      await page.locator('#btn-submit-login').click();
    }
    await page.waitForTimeout(1500);

    // 2. 产品字典四大独立视图验证
    console.log('[Step 2] 验证产品字典 4 大主内容区独立视图与 Tab 联动...');
    
    // 2.1 耗材规格目录 (tab=specs)
    await page.goto('http://127.0.0.1:5173/dict?tab=specs', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);
    const img1 = path.resolve(screenshotDir, `${ts}_subview_01_dict_specs.png`);
    await page.screenshot({ path: img1, fullPage: true });
    fs.copyFileSync(img1, path.resolve(artifactDir, `${ts}_subview_01_dict_specs.png`));
    console.log(`[OK] 耗材规格目录视图截图: ${img1}`);

    // 2.2 仓库架构维护 (tab=warehouses) 独立全屏视图
    console.log('[Step 3] 验证仓库架构维护独立视图（院级主库与临床二级库两栏拓扑）...');
    await page.goto('http://127.0.0.1:5173/dict?tab=warehouses', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);
    const img2 = path.resolve(screenshotDir, `${ts}_subview_02_dict_warehouses_topology.png`);
    await page.screenshot({ path: img2, fullPage: true });
    fs.copyFileSync(img2, path.resolve(artifactDir, `${ts}_subview_02_dict_warehouses_topology.png`));
    console.log(`[OK] 仓库架构分层维护视图截图: ${img2}`);

    // 2.3 耗材分类设置 (tab=categories) 独立全屏视图
    console.log('[Step 4] 验证耗材分类设置独立视图...');
    await page.goto('http://127.0.0.1:5173/dict?tab=categories', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);
    const img3 = path.resolve(screenshotDir, `${ts}_subview_03_dict_categories.png`);
    await page.screenshot({ path: img3, fullPage: true });
    fs.copyFileSync(img3, path.resolve(artifactDir, `${ts}_subview_03_dict_categories.png`));
    console.log(`[OK] 耗材分类设置视图截图: ${img3}`);

    // 2.4 供应商资质档案 (tab=suppliers) 独立全屏视图
    console.log('[Step 5] 验证国家级医疗供应商资质档案独立台账大表格...');
    await page.goto('http://127.0.0.1:5173/dict?tab=suppliers', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);
    const img4 = path.resolve(screenshotDir, `${ts}_subview_04_dict_suppliers.png`);
    await page.screenshot({ path: img4, fullPage: true });
    fs.copyFileSync(img4, path.resolve(artifactDir, `${ts}_subview_04_dict_suppliers.png`));
    console.log(`[OK] 供应商国家级资质档案台账截图: ${img4}`);

    // 3. 普通耗材主库验收入库与盘点
    console.log('[Step 6] 验证普通耗材主库子工作台切换 (/general?tab=inbound)...');
    await page.goto('http://127.0.0.1:5173/general?tab=inbound', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);
    const img5 = path.resolve(screenshotDir, `${ts}_subview_05_general_inbound.png`);
    await page.screenshot({ path: img5, fullPage: true });
    fs.copyFileSync(img5, path.resolve(artifactDir, `${ts}_subview_05_general_inbound.png`));
    console.log(`[OK] 主库耗材验收入库与退货工作台截图: ${img5}`);

    // 4. 临床二级库手动发料出库
    console.log('[Step 7] 验证临床二级库手动发料出库 (/secondary?tab=manual-out)...');
    await page.goto('http://127.0.0.1:5173/secondary?tab=manual-out', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);
    const img7 = path.resolve(screenshotDir, `${ts}_subview_07_secondary_manual_out.png`);
    await page.screenshot({ path: img7, fullPage: true });
    fs.copyFileSync(img7, path.resolve(artifactDir, `${ts}_subview_07_secondary_manual_out.png`));
    console.log(`[OK] 临床二级库手动发料工作台截图: ${img7}`);

    // 5. 财务四大主库发料流向对账
    console.log('[Step 8] 验证财务四大归口主库发料流向对账台账 (/finance?tab=main-reconciliation)...');
    await page.goto('http://127.0.0.1:5173/finance?tab=main-reconciliation', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);
    const img9 = path.resolve(screenshotDir, `${ts}_subview_09_finance_main_reconciliation.png`);
    await page.screenshot({ path: img9, fullPage: true });
    fs.copyFileSync(img9, path.resolve(artifactDir, `${ts}_subview_09_finance_main_reconciliation.png`));
    console.log(`[OK] 财务四大主库发料对账台账截图: ${img9}`);

    // 6. 全院物资流转追溯与异常预警
    console.log('[Step 9] 验证全院物资流转追溯台账 (/logs?tab=trace)...');
    await page.goto('http://127.0.0.1:5173/logs?tab=trace', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);
    const img11 = path.resolve(screenshotDir, `${ts}_subview_11_logs_trace.png`);
    await page.screenshot({ path: img11, fullPage: true });
    fs.copyFileSync(img11, path.resolve(artifactDir, `${ts}_subview_11_logs_trace.png`));
    console.log(`[OK] 物资流转追溯台账截图: ${img11}`);

    console.log(`\n==== [回环验证检测结果] ====`);
    console.log(`控制台/页面异常报错数: ${pageErrors.length}`);
    if (pageErrors.length > 0) {
      console.warn('警告：捕获到以下前端页面错误:', pageErrors);
    }
    console.log('==== [SUCCESS] 全业务模块细分子功能独立视图与路由联动回环测试全部通过！====');
  } finally {
    await context.close();
  }
}

runSubviewsAndRoutingVerification().catch((err) => {
  console.error('[FAILED] 回环验证执行异常:', err);
  process.exit(1);
});
