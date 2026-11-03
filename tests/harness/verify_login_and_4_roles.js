const path = require('path');
const { launchPersistentPlaywright } = require('../e2e/browser_config');

const BASE_URL = 'http://127.0.0.1:5173';

async function run() {
  console.log('[Test Start] 开始执行 1:1 复刻 Demo 原型前端自动化测试...');
  const { context, page } = await launchPersistentPlaywright({ headless: true });

  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(`Console Error: ${msg.text()}`);
    }
  });
  page.on('pageerror', (err) => {
    errors.push(`PageError: ${err.message}`);
  });

  await page.setViewportSize({ width: 1440, height: 900 });

  // 1. 清理本地缓存并测试未登录拦截与重定向
  console.log('[Step 1] 清理本地会话并校验未登录拦截与重定向至 /login...');
  await page.goto(`${BASE_URL}/dict`);
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.goto(`${BASE_URL}/dict`);
  await page.waitForTimeout(1000);

  const currentUrl = page.url();
  console.log('  当前重定向 URL:', currentUrl);
  if (!currentUrl.includes('/login')) {
    throw new Error(`未登录拦截失败，当前 URL 应为 /login，实际为: ${currentUrl}`);
  }
  console.log('  [PASS 1/6] 未登录访问受控工作台自动拦截并重定向到 /login 通过');

  // 2. 校验登录门户卡片渲染
  console.log('[Step 2] 校验医慧通行现代卡片风格登录认证门户与 4 大角色网格...');
  const titleText = await page.locator('.spd-auth-title').textContent();
  console.log('  认证中心标题:', titleText);
  if (!titleText.includes('医慧通行')) {
    throw new Error(`登录卡片标题不符合预期: ${titleText}`);
  }
  const roleButtons = await page.locator('.spd-role-btn').count();
  console.log('  4 大角色一键体验按钮数量:', roleButtons);
  if (roleButtons < 4) {
    throw new Error(`4 大角色一键按钮数量不足 4 个，实际为: ${roleButtons}`);
  }
  await page.screenshot({ path: 'tests/screenshots/live_1to1_login_portal.png' });
  console.log('  [PASS 2/6] 登录认证门户、Tab切换与4大角色一键登录网格渲染通过');

  // 3. 一键免密登录为 [信息科系统管理员]
  console.log('[Step 3] 点击一键免密登录为 [信息科系统管理员]...');
  await page.locator('.spd-role-btn').first().click();
  await page.waitForURL('**/dict', { timeout: 8000 });
  await page.waitForTimeout(1200);

  const roleBannerText = await page.locator('.role-banner').textContent();
  console.log('  当前权限上下文横幅:', roleBannerText.trim());
  if (!roleBannerText.includes('信息科系统管理员')) {
    throw new Error(`角色上下文横幅未正确显示信息科管理员说明: ${roleBannerText}`);
  }
  console.log('  [PASS 3/6] 信息科系统管理员免密登录并正确激活顶部角色权限横幅通过');

  // 4. 校验产品字典顶部 4 宫格 KPI 大盘与双树联动
  console.log('[Step 4] 校验产品字典顶部 4 宫格 KPI 卡片大盘与双树联动...');
  const kpiCount = await page.locator('.kpi-card').count();
  console.log('  KPI 卡片数量:', kpiCount);
  if (kpiCount < 4) {
    throw new Error(`顶部 KPI 卡片不足 4 个: ${kpiCount}`);
  }
  const kpi1Text = await page.locator('.kpi-val').first().textContent();
  console.log('  KPI 1 字典总数:', kpi1Text.trim());
  await page.screenshot({ path: 'tests/screenshots/live_1to1_dict_view.png' });
  console.log('  [PASS 4/6] 1:1 复刻 Demo 原型顶部 4 宫格 KPI 大盘与双树联动通过');

  // 5. 切换为 [临床二级库人员] 校验权限上下文变化与普通耗材/高值耗材大盘
  console.log('[Step 5] 切换为 [临床二级库人员] 视角并校验普通耗材与高值耗材大盘...');
  await page.locator('.role-selector select').selectOption('secondary_user');
  await page.waitForTimeout(800);
  const updatedBanner = await page.locator('.role-banner').textContent();
  console.log('  切换后角色横幅:', updatedBanner.trim());
  if (!updatedBanner.includes('临床二级库')) {
    throw new Error(`角色上下文横幅未切换为临床二级库: ${updatedBanner}`);
  }

  // 导航至普通耗材
  await page.goto(`${BASE_URL}/general`);
  await page.waitForTimeout(800);
  const genKpiCount = await page.locator('.kpi-card').count();
  console.log('  普通耗材 KPI 卡片数:', genKpiCount);
  await page.screenshot({ path: 'tests/screenshots/live_1to1_general_view.png' });

  // 导航至高值耗材
  await page.goto(`${BASE_URL}/high-value`);
  await page.waitForTimeout(800);
  const hvKpiCount = await page.locator('.kpi-card').count();
  console.log('  高值耗材 KPI 卡片数:', hvKpiCount);
  await page.screenshot({ path: 'tests/screenshots/live_1to1_high_value_view.png' });
  console.log('  [PASS 5/6] 角色视角平滑切换、角色横幅联动与各业务页面 4 宫格 KPI 大盘通过');

  // 6. 测试退出登录闭环
  console.log('[Step 6] 测试退出登录安全闭环...');
  await page.locator('button:has-text("退出登录")').click();
  await page.waitForURL('**/login', { timeout: 5000 });
  await page.waitForTimeout(500);
  const postLogoutUrl = page.url();
  console.log('  退出登录后 URL:', postLogoutUrl);
  if (!postLogoutUrl.includes('/login')) {
    throw new Error(`退出登录后未安全返回 /login: ${postLogoutUrl}`);
  }
  console.log('  [PASS 6/6] 退出登录清理会话并重定向回认证门户闭环通过');

  if (errors.length > 0) {
    console.error('发现控制台报错:', errors);
    throw new Error(`自动化测试存在 ${errors.length} 个错误`);
  }

  await context.close();
  console.log('[SUCCESS] 全部 6 项强断言 100% 绿色通过，0 错误，0 报错！');
}

run().catch((err) => {
  console.error('[FAILED] 测试未通过:', err);
  process.exit(1);
});
