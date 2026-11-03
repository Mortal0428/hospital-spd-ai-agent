const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

/**
 * 实机捕获最新 5173 数字化展厅主门户及模态登录弹窗联动截图
 */
async function captureShowcasePortal() {
  const { context, page } = await launchPersistentPlaywright({ headless: true });
  try {
    const screenshotDir = path.resolve(__dirname, '../screenshots');
    const artifactDir = path.resolve('C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2');
    if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;

    // 1. 清理本地会话，以未登录身份直接访问根路径
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    console.log('正在访问 http://127.0.0.1:5173/ ...');
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1500);

    // 截图 1: 展厅大屏全景
    const showcaseImg = path.resolve(screenshotDir, `${ts}_01_showcase_portal_live.png`);
    await page.screenshot({ path: showcaseImg, fullPage: true });
    fs.copyFileSync(showcaseImg, path.resolve(artifactDir, `${ts}_01_showcase_portal_live.png`));
    console.log(`[OK] 展厅全景已成功截图: ${showcaseImg}`);

    // 2. 点击【医慧通行】或【进入三级角色工作台 ENTRY】唤起模态弹窗
    console.log('正在点击【医慧通行】唤起模态弹窗...');
    const loginPill = page.locator('#btn-open-login, button:has-text("医慧通行")');
    if (await loginPill.count() > 0) {
      await loginPill.first().click();
    } else {
      await page.click('#btn-enter-workbench, a:has-text("进入三级角色工作台")');
    }
    await page.waitForTimeout(800);

    // 截图 2: 展厅之上的毛玻璃模态登录中枢
    const modalImg = path.resolve(screenshotDir, `${ts}_02_showcase_modal_active_live.png`);
    await page.screenshot({ path: modalImg, fullPage: true });
    fs.copyFileSync(modalImg, path.resolve(artifactDir, `${ts}_02_showcase_modal_active_live.png`));
    console.log(`[OK] 展厅模态弹窗已成功截图: ${modalImg}`);

    return { showcaseImg, modalImg };
  } finally {
    await context.close();
  }
}

captureShowcasePortal()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error('展厅截屏执行失败:', err);
    process.exit(1);
  });
