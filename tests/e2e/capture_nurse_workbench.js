const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

/**
 * 模拟以临床二级库护士身份登录并捕获工作台侧边栏与页面权限
 * @returns {Promise<string>}
 */
async function captureNurseWorkbench() {
  const { context, page } = await launchPersistentPlaywright({ headless: true });
  try {
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);

    // 点击【临床二级库】免密登录按钮
    console.log('正在点击临床二级库演示通道...');
    const nurseBtn = page.locator('button.spd-role-btn:has-text("临床二级库")');
    if (await nurseBtn.count() > 0) {
      await nurseBtn.first().click();
    } else {
      // 备用：选择快速角色
      await page.click('button:has-text("临床二级库")');
    }

    await page.waitForTimeout(1500);

    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;
    const screenshotDir = path.resolve(__dirname, '../screenshots');
    const outPath = path.resolve(screenshotDir, `${ts}_live_nurse_workbench.png`);

    await page.screenshot({ path: outPath, fullPage: true });
    console.log(`[OK] 护士工作台截图: ${outPath}`);

    const artifactPath = path.resolve('C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2', `${ts}_live_nurse_workbench.png`);
    fs.copyFileSync(outPath, artifactPath);
    return outPath;
  } finally {
    await context.close();
  }
}

captureNurseWorkbench()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error('测试失败:', err);
    process.exit(1);
  });
