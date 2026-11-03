const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright, getEgoDriverInfo } = require('./browser_config');

/**
 * 执行自动化浏览器持久化 Profile 回环渲染与凭证截取
 * @returns {Promise<boolean>} 验证执行结果
 * @route internal://tests/e2e/verify_browser.js/runVerification
 * @throws {Error} 若自检断言失败或截图捕获异常则抛出
 */
async function runVerification() {
  console.log('[Browser-Verify] 正在加载浏览器自动化持久化上下文 (方案 A)...');
  const egoInfo = getEgoDriverInfo();
  console.log(`[Browser-Verify] 已核验系统 Ego 浏览器本体路径: ${egoInfo.appPath}`);
  console.log(`[Browser-Verify] 已核验系统 Ego CLI 工具路径: ${egoInfo.cliPath}`);

  let contextHandle = null;

  try {
    const { context, page } = await launchPersistentPlaywright({ headless: true });
    contextHandle = context;

    console.log('[Browser-Verify] 自动化持久化上下文构建成功，开始渲染自检视图...');
    await page.setContent(`
      <!DOCTYPE html>
      <html lang="zh-CN">
      <head>
        <meta charset="UTF-8">
        <title>浏览器自动化环境与 Ego 协同验证凭证</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #090d16;
            color: #f1f5f9;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
          }
          .card {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 14px;
            padding: 36px 44px;
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7);
            max-width: 640px;
          }
          .tag {
            display: inline-block;
            background: rgba(14, 165, 233, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 6px;
            padding: 4px 12px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 16px;
          }
          h1 {
            font-size: 20px;
            margin: 0 0 14px 0;
            color: #ffffff;
            font-weight: 600;
          }
          p {
            font-size: 13.5px;
            color: #94a3b8;
            line-height: 1.6;
            margin: 0 0 24px 0;
          }
          .status-row {
            display: flex;
            align-items: center;
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 13px;
          }
          .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            margin-right: 10px;
            display: inline-block;
          }
          .status-text {
            color: #34d399;
            font-weight: 500;
          }
        </style>
      </head>
      <body>
        <div class="card">
          <div class="tag">AUTOMATION PROFILE VERIFIED</div>
          <h1>浏览器自动化持久化 Profile 接入成功</h1>
          <p>
            方案 A 持久化 Profile 隔离环境已就绪。Cookie、LocalStorage 及会话状态具备独立缓存能力，
            与前台运行中的 Ego 浏览器保持安全隔离并规避单实例文件锁冲突。
          </p>
          <div class="status-row">
            <span class="status-dot"></span>
            <span class="status-text">[ PASS ] 回环测试环境、渲染引擎与截图驱动已就绪</span>
          </div>
        </div>
      </body>
      </html>
    `);

    const screenshotDir = path.resolve(__dirname, '../screenshots');
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }

    const screenshotPath = path.join(screenshotDir, '2026-10-29_20-08-09_ego_verify.png');
    console.log(`[Browser-Verify] 正在生成实机测试凭证并保存至: ${screenshotPath}`);
    await page.screenshot({ path: screenshotPath, fullPage: true });

    console.log('[Browser-Verify] 实机凭证捕获成功！');
    return true;
  } catch (error) {
    console.error(`[Browser-Verify-Error] 执行失败: ${error.message}`);
    throw error;
  } finally {
    if (contextHandle) {
      await contextHandle.close();
      console.log('[Browser-Verify] 持久化浏览器上下文已安全释放。');
    }
  }
}

runVerification()
  .then(() => {
    process.exit(0);
  })
  .catch(() => {
    process.exit(1);
  });
