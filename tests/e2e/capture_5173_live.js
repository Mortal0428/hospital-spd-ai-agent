const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

/**
 * 实机捕获当前 5173 服务的全屏渲染截图并归档
 * @returns {Promise<string>} 截图保存路径
 * @route internal://tests/e2e/capture_5173_live.js
 * @throws 运行异常抛出
 */
async function capture5173Live() {
  const { context, page } = await launchPersistentPlaywright({ headless: true });
  try {
    console.log('正在访问 http://127.0.0.1:5173/ ...');
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);

    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;
    const screenshotDir = path.resolve(__dirname, '../screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }

    const outPath = path.resolve(screenshotDir, `${ts}_live_5173_auth_modal.png`);
    await page.screenshot({ path: outPath, fullPage: true });
    console.log(`[OK] 5173 实机全屏截图已成功生成: ${outPath}`);

    // 同时复制至 brain 目录供快速预览
    const artifactPath = path.resolve('C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2', `${ts}_live_5173_auth_modal.png`);
    fs.copyFileSync(outPath, artifactPath);
    console.log(`[OK] 已同步至 artifact: ${artifactPath}`);

    return outPath;
  } finally {
    await context.close();
  }
}

capture5173Live()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error('截图失败:', err);
    process.exit(1);
  });
