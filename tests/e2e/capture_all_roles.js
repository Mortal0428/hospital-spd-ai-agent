const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

/**
 * 完整校验并实机截取多角色权限隔离工作台视图
 */
async function captureAllRoles() {
  const { context, page } = await launchPersistentPlaywright({ headless: true });
  try {
    const screenshotDir = path.resolve(__dirname, '../screenshots');
    const artifactDir = path.resolve('C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2');
    if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;

    // 1. 清理会话，访问登录中枢
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle' });
    await page.waitForTimeout(600);

    // 截图 1: 登录中枢模态卡片
    const loginImg = path.resolve(screenshotDir, `${ts}_01_auth_modal.png`);
    await page.screenshot({ path: loginImg, fullPage: true });
    fs.copyFileSync(loginImg, path.resolve(artifactDir, `${ts}_01_auth_modal.png`));
    console.log(`[OK] 登录模态窗已截图: ${loginImg}`);

    // 2. 点击【临床二级库】免密登录
    console.log('点击临床二级库演示通道...');
    await page.click('button[data-role="nurse"]');
    await page.waitForURL('**/secondary', { timeout: 10000 });
    await page.waitForTimeout(1000);

    // 截图 2: 护士视角工作台 (重点检验侧边栏权限隔离)
    const nurseImg = path.resolve(screenshotDir, `${ts}_02_nurse_workbench_isolated.png`);
    await page.screenshot({ path: nurseImg, fullPage: true });
    fs.copyFileSync(nurseImg, path.resolve(artifactDir, `${ts}_02_nurse_workbench_isolated.png`));
    console.log(`[OK] 护士工作台已截图: ${nurseImg}`);

    // 3. 切换为系统管理员 (全权视角)
    console.log('切换为系统管理员全权视角...');
    await page.selectOption('.role-selector select', 'sys_admin');
    await page.waitForTimeout(1200);

    const adminImg = path.resolve(screenshotDir, `${ts}_03_admin_workbench_full.png`);
    await page.screenshot({ path: adminImg, fullPage: true });
    fs.copyFileSync(adminImg, path.resolve(artifactDir, `${ts}_03_admin_workbench_full.png`));
    console.log(`[OK] 管理员全权工作台已截图: ${adminImg}`);

    return { loginImg, nurseImg, adminImg };
  } finally {
    await context.close();
  }
}

captureAllRoles()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error('实机截屏执行异常:', err);
    process.exit(1);
  });
