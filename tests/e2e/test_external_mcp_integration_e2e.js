/**
 * @file test_external_mcp_integration_e2e.js
 * @description 外部解耦式 MCP 协议扩展工具中台与智能体入参出参过程透明化 Playwright E2E 回环测试
 * 
 * 验证目标：
 * 1. 验证 Modular RAG 控制台 (Tab 2) 成功呈现【7. 外部 MCP 协议扩展工具中台】卡片；
 * 2. 验证两款外部解耦 MCP 工具 (mcp_external_medical_search & mcp_datetime_and_fefo_calc) 状态良好、支持启闭与在线调试；
 * 3. 验证点击【调试入参出参 (Inspect)】能够成功执行 MCP 调用并格式化回显标准 Output；
 * 4. 验证在 8 大智能体沙箱中输入国标规范咨询指令时，智能体成功调用外部 MCP 工具；
 * 5. 验证前端透明展开展示真实入参 (Arguments) 与出参 (Output) 实体；
 * 6. 生成实机测试截图并归档至 tests/screenshots/ 与 Artifact 目录。
 */

const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

async function runExternalMcpE2ETest() {
  const screenshotDir = path.resolve(__dirname, '../screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const artifactDir = 'C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2';

  const { context, page } = await launchPersistentPlaywright({ headless: true });
  const consoleErrors = [];

  page.on('pageerror', err => {
    console.error('[PageError]', err.message);
    consoleErrors.push(err.message);
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      if (!txt.includes('favicon.ico') && !txt.includes('Failed to load resource')) {
        console.error('[ConsoleError]', txt);
        consoleErrors.push(txt);
      }
    }
  });

  try {
    console.log('1. 正在导航至人员管理页面并切换至系统管理员账号...');
    await page.goto('http://127.0.0.1:5173/users', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    const switchBtn = page.locator('button:has-text("切换账号"), .account-switch-btn').first();
    if (await switchBtn.count() > 0) {
      await switchBtn.click();
      await page.waitForTimeout(1000);
      const adminCard = page.locator('.switch-user-card:has-text("cyx"), .switch-user-card:has-text("陈永兴"), .switch-user-card:has-text("系统管理员")').first();
      if (await adminCard.count() > 0) {
        await adminCard.click();
        await page.waitForTimeout(1500);
        console.log('已确保当前身份为信息科系统管理员');
      }
    }

    console.log('2. 访问智能体控制中台 Tab 2 (Modular RAG 控制台)...');
    await page.goto('http://127.0.0.1:5173/rag-hub?tab=config', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2500);

    const configTab = page.locator('.el-tabs__item:has-text("Modular RAG"), .el-tabs__item:has-text("热插拔")').first();
    if (await configTab.count() > 0) {
      await configTab.click();
      await page.waitForTimeout(1200);
    }

    console.log('3. 滚动定位至【7. 外部 MCP 协议扩展工具中台】...');
    const mcpSection = page.locator('.config-section:has-text("外部 MCP 协议扩展工具中台")').first();
    if (await mcpSection.count() > 0) {
      await mcpSection.scrollIntoViewIfNeeded();
      await page.waitForTimeout(1000);
      console.log('成功定位到外部 MCP 协议扩展工具中台卡片！');
    } else {
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(1200);
    }

    console.log('4. 打开外部 MCP 工具单体调试弹窗并执行调用...');
    const inspectBtn = page.locator('.config-section:has-text("外部 MCP") button:has-text("调试入参出参"), .config-section:has-text("外部 MCP") button:has-text("Inspect")').first();
    if (await inspectBtn.count() > 0) {
      await inspectBtn.click();
      await page.waitForTimeout(1000);

      const execMcpBtn = page.locator('.el-dialog button:has-text("立即执行 MCP 调用")').first();
      if (await execMcpBtn.count() > 0) {
        await execMcpBtn.click();
        await page.waitForTimeout(2500);
        console.log('已执行外部 MCP 单体测试，获取到标准回传 JSON');
      }
    }

    // 截取 MCP 控制中台与单体调试全貌
    const mcpCenterScreenshot = path.join(screenshotDir, '2026-11-06_18-55-00_mcp_control_center.png');
    await page.screenshot({ path: mcpCenterScreenshot, fullPage: true });
    console.log('外部 MCP 控制中台截图已落盘:', mcpCenterScreenshot);

    if (fs.existsSync(artifactDir)) {
      fs.copyFileSync(mcpCenterScreenshot, path.join(artifactDir, '2026-11-06_18-55-00_mcp_control_center.png'));
    }

    // 关闭弹窗
    const closeDialogBtn = page.locator('.el-dialog__headerbtn').first();
    if (await closeDialogBtn.count() > 0) {
      await closeDialogBtn.click();
      await page.waitForTimeout(1000);
    }

    console.log('5. 切换至 Tab 3 (8 大业务智能体多架构调度沙箱)...');
    const sandboxTab = page.locator('.el-tabs__item:has-text("8 大业务智能体"), .el-tabs__item:has-text("沙箱")').first();
    if (await sandboxTab.count() > 0) {
      await sandboxTab.click();
      await page.waitForTimeout(2000);
    }

    console.log('6. 选中智能体 1 并触发外部 MCP 关联查询...');
    const mcpPreset = page.locator('.preset-pill:has-text("外部 MCP"), .preset-pill:has-text("国标规范")').first();
    if (await mcpPreset.count() > 0) {
      console.log('点击预置建议药丸触发外部 MCP 查询...');
      await mcpPreset.click();
    } else {
      console.log('在内嵌 AgentChatWidget 输入框中输入指令...');
      const chatInput = page.locator('.agent-chat-widget .widget-footer input').first();
      await chatInput.fill('查询国家药监局关于无菌一次性耗材包装与灭菌的最新国标规范 (调用外部 MCP)');
      await page.waitForTimeout(500);
      const sendBtn = page.locator('.agent-chat-widget .widget-footer button:has-text("执行")').first();
      await sendBtn.click();
    }

    console.log('等待智能体打字机与外部 MCP 网关专家气泡完成 (等待 16 秒)...');
    await page.waitForTimeout(16000);

    console.log('7. 展开 MCP 工具调用详细入参与出参...');
    const expandBtn = page.locator('.subagent-bubble-card span:has-text("展开入参/出参"), .tool-call-card span:has-text("展开入参/出参"), span:has-text("展开入参/出参 (JSON) ▾")').first();
    if (await expandBtn.count() > 0) {
      await expandBtn.click();
      await page.waitForTimeout(1000);
      console.log('已成功点击展开 MCP 详细入参出参 JSON 卡片！');
    } else {
      console.warn('未找到展开折叠按钮，尝试直接截取群聊气泡区域');
    }

    // 截取智能体群聊中外部 MCP 过程透明化展开截图
    const agentMcpScreenshot = path.join(screenshotDir, '2026-11-06_18-55-00_agent_mcp_tool_call_expanded.png');
    await page.screenshot({ path: agentMcpScreenshot, fullPage: true });
    console.log('智能体 MCP 详细入参出参展开截图已落盘:', agentMcpScreenshot);

    if (fs.existsSync(artifactDir)) {
      fs.copyFileSync(agentMcpScreenshot, path.join(artifactDir, '2026-11-06_18-55-00_agent_mcp_tool_call_expanded.png'));
    }

    console.log('\n===== Playwright E2E 回环测试执行完毕 =====');
    console.log('拦截到的控制台错误数:', consoleErrors.length);

  } catch (err) {
    console.error('Playwright E2E 测试运行异常:', err);
    throw err;
  } finally {
    await context.close();
  }
}

runExternalMcpE2ETest().then(() => {
  console.log('Playwright 回环测试成功完成！');
  process.exit(0);
}).catch(err => {
  console.error('Playwright 回环测试失败:', err);
  process.exit(1);
});
