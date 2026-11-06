/**
 * @file verify_feishu_dynamic_screenshot.js
 * @description 使用原生 Edge 内核持久化 Playwright 截取飞书长连接守护服务与 8 大智能体控制台实机截图
 * 遵循全域零 Emoji 规范与 100% 中文四要素注释。
 * 
 * @param 无
 * @returns {Promise<void>}
 * @route internal://tests/e2e/verify_feishu_dynamic_screenshot.js
 * @throws 异常安全捕获
 */

const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

async function captureFeishuConsoleScreenshot() {
  const screenshotDir = path.resolve(__dirname, '../screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }
  const targetScreenshot = path.resolve(screenshotDir, '2026-11-05_23-50-00_feishu_dynamic_intent_and_at.png');

  console.log('正在拉起系统 Edge 内核 Playwright 浏览器...');
  const { context, page } = await launchPersistentPlaywright({
    headless: true,
    channel: 'msedge'
  });

  try {
    console.log('导航访问前端控制台: http://127.0.0.1:5173 ...');
    await page.goto('http://127.0.0.1:5173/#/rag-agent-hub', { timeout: 30000 });
    await page.waitForTimeout(3000);

    // 检查是否在登录页
    const loginBtn = await page.$("button:has-text('登录')");
    if (loginBtn) {
      console.log('注入管理员登录凭据...');
      await page.fill("input[type='text']", 'sys_admin');
      await page.fill("input[type='password']", 'admin123');
      await loginBtn.click();
      await page.waitForTimeout(3000);
      await page.goto('http://127.0.0.1:5173/#/rag-agent-hub', { timeout: 30000 });
      await page.waitForTimeout(3000);
    }

    // 切换到 Tab 2: Modular RAG 算子与智能体中台配置
    console.log('切换至 Modular RAG 算子与智能体中台配置 Tab...');
    const tabs = await page.$$('.el-tabs__item');
    for (const tab of tabs) {
      const text = await tab.innerText();
      if (text.includes('中台配置') || text.includes('算子')) {
        await tab.click();
        await page.waitForTimeout(1500);
        break;
      }
    }

    // 平滑向下滚动到飞书长连接看板与卡片推送区域
    await page.evaluate(() => {
      window.scrollTo({ top: 820, behavior: 'instant' });
    });
    await page.waitForTimeout(2000);

    // 截屏保存
    await page.screenshot({ path: targetScreenshot, fullPage: false });
    console.log(`[SUCCESS] 实机高清截图已成功归档至: ${targetScreenshot}`);
  } catch (err) {
    console.error(`截图发生异常: ${err.message}`);
  } finally {
    await context.close();
  }
}

captureFeishuConsoleScreenshot();
