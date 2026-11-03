const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

/**
 * 实机捕获 M4 重构后的全新高质感毛玻璃业务视图截图
 */
async function captureM4Views() {
  const { context, page } = await launchPersistentPlaywright({ headless: true });
  try {
    const screenshotDir = path.resolve(__dirname, '../screenshots');
    const artifactDir = path.resolve('C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2');
    if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;

    // 1. 先以管理员身份登录，查看重构后的【产品字典双维分类管理视图】
    await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle' });
    await page.waitForTimeout(600);
    console.log('以管理员身份登录查看产品字典...');
    await page.click('button[data-role="consumable"]'); // 耗材科主管王建国 (负责产品字典)
    await page.waitForURL('**/dict', { timeout: 10000 });
    await page.waitForTimeout(1500);

    const dictImg = path.resolve(screenshotDir, `${ts}_01_product_dict_glassmorphism.png`);
    await page.screenshot({ path: dictImg, fullPage: true });
    fs.copyFileSync(dictImg, path.resolve(artifactDir, `${ts}_01_product_dict_glassmorphism.png`));
    console.log(`[OK] 重构后产品字典截图已生成: ${dictImg}`);

    // 2. 切换为护士身份，查看重构后的【二级库管理视图】
    console.log('切换为临床二级库护士视角...');
    await page.selectOption('.role-selector select', 'secondary_user');
    await page.waitForTimeout(1500);

    const secImg = path.resolve(screenshotDir, `${ts}_02_secondary_warehouse_glassmorphism.png`);
    await page.screenshot({ path: secImg, fullPage: true });
    fs.copyFileSync(secImg, path.resolve(artifactDir, `${ts}_02_secondary_warehouse_glassmorphism.png`));
    console.log(`[OK] 重构后二级库管理截图已生成: ${secImg}`);

    return { dictImg, secImg };
  } finally {
    await context.close();
  }
}

captureM4Views()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error('截屏失败:', err);
    process.exit(1);
  });
