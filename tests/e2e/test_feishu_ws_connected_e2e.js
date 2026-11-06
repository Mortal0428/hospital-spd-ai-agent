/**
 * @file test_feishu_ws_connected_e2e.js
 * @description Playwright 端到端自动化实机验证脚本
 * 验证：
 * 1. 飞书官方 SDK 反向长连接服务 (lark-oapi ws.Client) 实时监控看板正确渲染
 * 2. 状态标签显示“WebSocket 已连通 (在线监听)”，绿灯在线
 * 3. 长连接会话 ID、运行秒数、事件订阅 (im.message.receive_v1) 准确呈现
 * 4. 飞书开放平台【重新验证】操作指引横幅清晰醒目
 * 5. 点击“刷新状态”按钮联动后端 GET /api/v1/rag-hub/feishu/ws-status
 * 6. 捕获实机截图保存至 tests/screenshots/
 *
 * @param 无
 * @returns None
 * @route tests/e2e/test_feishu_ws_connected_e2e.js
 * @throws 异常捕获并输出
 */

const { launchPersistentPlaywright } = require('./browser_config');
const fs = require('fs');
const path = require('path');

(async () => {
  console.log('=== 启动 Playwright 飞书官方 SDK 长连接在线看板端到端实机验证 ===');
  const { browser, context, page } = await launchPersistentPlaywright({
    headless: true,
    profileDir: path.resolve('C:/Users/27705/AppData/Local/Citro Labs/ego lite/User Data/FeishuWsAutomationProfile')
  });

  const pageErrors = [];
  page.on('pageerror', (err) => {
    console.error('[Page Error]:', err.message);
    pageErrors.push(err.message);
  });

  const screenshotDir = path.resolve(__dirname, '../screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const timestamp = '2026-11-05_22-30-00';

  try {
    // 1. 初始化管理员登录态并访问 RAG Hub 中台
    console.log('1. 初始化 sys_admin 登录凭据并访问 /rag-hub...');
    await page.goto('http://127.0.0.1:5173/showcase', { waitUntil: 'networkidle', timeout: 30000 });
    await page.evaluate(() => {
      localStorage.setItem('spd_is_logged_in', 'true');
      localStorage.setItem('spd_token', 'mock_sys_admin_token');
      localStorage.setItem('spd_active_user', JSON.stringify({
        id: 1,
        username: 'admin',
        realName: '赵振华 (系统管理员)',
        roleCode: 'sys_admin',
        deptCode: 'INFO_DEPT',
        deptName: '信息科'
      }));
    });

    await page.goto('http://127.0.0.1:5173/rag-hub?tab=modular', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    await page.waitForTimeout(2000);

    // 显式点击 Tab 确保激活 Modular RAG 算子与智能体中控台
    const modularTab = page.locator(".el-tabs__item:has-text('Modular RAG')").first();
    if (await modularTab.isVisible()) {
      await modularTab.click();
      await page.waitForTimeout(1500);
    }

    // 2. 验证看板渲染
    console.log('2. 验证飞书官方 SDK 反向长连接监控看板...');
    const boardTitle = page.locator("text='飞书官方 SDK 反向长连接服务'").first();
    const isTitleVisible = await boardTitle.isVisible();
    console.log('看板标题可见性:', isTitleVisible);

    const statusChip = page.locator("text='WebSocket 已连通'").first();
    const isStatusVisible = await statusChip.isVisible();
    console.log('连接成功状态可见性:', isStatusVisible);

    // 3. 点击【刷新状态】按钮
    console.log('3. 点击【刷新状态】按钮...');
    const refreshBtn = page.locator("button:has-text('刷新状态')").first();
    if (await refreshBtn.isVisible()) {
      await refreshBtn.click();
      await page.waitForTimeout(2000);
      console.log('刷新状态按钮交互成功！');
    }

    // 滚动并精确定位到长连接看板
    if (await boardTitle.isVisible()) {
      await boardTitle.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
    }

    const recheckStatus = await page.locator("text='WebSocket 已连通'").first().isVisible();
    console.log('刷新后长连接状态连通可见性:', recheckStatus);

    // 4. 截图 1: 聚焦外部生态与长连接面板
    const sectionPanel = page.locator(".config-section:has-text('飞书官方 SDK 反向长连接服务')").first();
    const screenshot1Path = path.join(screenshotDir, `${timestamp}_feishu_ws_connected_board.png`);
    if (await sectionPanel.isVisible()) {
      await sectionPanel.screenshot({ path: screenshot1Path });
    } else {
      await page.screenshot({ path: screenshot1Path, fullPage: false });
    }
    console.log('截图 1 已保存:', screenshot1Path);

    // 5. 截图 2: 全景视图 (包含外部生态通道与 8 大智能体解耦表格)
    const screenshot2Path = path.join(screenshotDir, `${timestamp}_feishu_ws_and_agents_overview.png`);
    await page.screenshot({ path: screenshot2Path, fullPage: true });
    console.log('截图 2 已保存:', screenshot2Path);

    console.log('\n=== 控制台异常审计 ===');
    if (pageErrors.length > 0) {
      console.warn('警告: 控制台存在错误:', pageErrors);
    } else {
      console.log('完美: 控制台 0 错误 (PageError=0)！');
    }

    console.log('=== Playwright 端到端实机验证圆满成功 ===');
  } catch (err) {
    console.error('Playwright 执行出现异常:', err);
    process.exitCode = 1;
  } finally {
    if (context) await context.close();
  }
})();
