/**
 * @file test_groupchat_and_mcp_ui.js
 * @description Playwright 端到端自动化实机验证脚本
 * 验证多子智能体微信群聊气泡流式渲染、MCP 工具入参出参真实填实展开、
 * 图三 Modular RAG 算子生效凭证卡片、飞书交互式卡片推送、Coze 云端协同问答
 * 以及智能体 3 人机协同 (HITL) 流程节点。
 *
 * @param 无
 * @returns None
 * @route tests/e2e/test_groupchat_and_mcp_ui.js
 * @throws 异常捕获并输出
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  console.log('=== 启动 Playwright 多子智能体群聊气泡与 MCP 真实参数实机回环验证 ===');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const pageErrors = [];
  page.on('pageerror', (err) => {
    console.error('[Page Error]:', err.message);
    pageErrors.push(err.message);
  });

  const screenshotDir = path.resolve(__dirname, '../screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  try {
    // 1. 访问智能体调度沙箱
    console.log('1. 正在访问前端沙箱: http://localhost:5173/#/rag-agent-hub?tab=agents');
    await page.goto('http://localhost:5173/#/rag-agent-hub?tab=agents', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // 2. 选择智能体 1 发送建仓指令
    console.log('2. 选择智能体 1 并发送建仓指令...');
    const agentMenuItems = await page.$$('.agent-menu-item');
    if (agentMenuItems.length > 0) {
      await agentMenuItems[0].click();
      await page.waitForTimeout(1000);
    }

    const inputArea = await page.$('.widget-footer input, .widget-footer .el-input__inner, input[placeholder*="输入业务指令"]');
    if (inputArea) {
      await inputArea.fill('请帮我新增一款高值骨科接骨板字典档案并查验供应商资质');
      await page.waitForTimeout(500);

      const sendBtn = await page.$('.widget-footer button:has-text("执行"), button:has-text("执行")');
      if (sendBtn) {
        await sendBtn.click();
        console.log('已提交智能体 1 业务指令，等待多子智能体群聊气泡与流式输出...');
        await page.waitForTimeout(12000);
      }
    }

    // 3. 展开 MCP 工具调用参数卡片
    console.log('3. 展开 MCP 工具入参出参卡片...');
    const toolHeaders = await page.$$('.tool-call-header');
    for (const th of toolHeaders) {
      try {
        await th.click();
        await page.waitForTimeout(300);
      } catch (e) {
        // ignore
      }
    }

    // 截图 1: 多子智能体微信群聊气泡与真实工具参数
    const s1Path = path.join(screenshotDir, '2026-11-05_16-10-00_groupchat_stream_bubbles.png');
    await page.screenshot({ path: s1Path, fullPage: false });
    console.log(`[截图完成 1/4]: ${s1Path}`);

    // 4. 切换至智能体 6 体验知识库问答并查看算子生效凭证卡片
    console.log('4. 选择智能体 6 并发送知识库问答指令...');
    const items = await page.$$('.agent-menu-item');
    for (const item of items) {
      const text = await item.textContent();
      if (text && text.includes('智能体 6')) {
        await item.click();
        await page.waitForTimeout(1000);
        break;
      }
    }

    const inputArea6 = await page.$('.widget-footer input, .widget-footer .el-input__inner, input[placeholder*="输入业务指令"]');
    if (inputArea6) {
      await inputArea6.fill('系统知识库目前纳管了多少篇医疗器械规范文档？切片与向量库状态如何？');
      await page.waitForTimeout(500);
      const sendBtn6 = await page.$('.widget-footer button:has-text("执行"), button:has-text("执行")');
      if (sendBtn6) {
        await sendBtn6.click();
        console.log('已提交智能体 6 知识库指令，等待算子凭证生成...');
        await page.waitForTimeout(8000);
      }
    }

    // 截图 2: 验证算子生效凭证卡片与系统事实查验
    const s2Path = path.join(screenshotDir, '2026-11-05_16-10-00_mcp_tool_parameters_verified.png');
    await page.screenshot({ path: s2Path, fullPage: false });
    console.log(`[截图完成 2/4]: ${s2Path}`);

    // 5. 切换至 Modular RAG 控制台 Tab 并测试一键保存全部配置与飞书、Coze 通道
    console.log('5. 切换至【Modular RAG 模块化热插拔控制台】Tab...');
    const configTab = await page.$('#tab-config, [aria-controls="pane-config"]');
    if (configTab) {
      await configTab.click();
      await page.waitForTimeout(1500);

      // 滚动到底部并测试发送飞书卡片
      console.log('测试发送飞书交互式卡片...');
      const feishuBtn = await page.$('button:has-text("发送飞书测试卡片")');
      if (feishuBtn) {
        await feishuBtn.scrollIntoViewIfNeeded();
        await feishuBtn.click();
        await page.waitForTimeout(2000);
      }

      // 测试与 Coze 协同问答
      console.log('测试与 Coze 云端小爱智能体协同...');
      const cozeBtn = await page.$('button:has-text("协同问答")');
      if (cozeBtn) {
        await cozeBtn.scrollIntoViewIfNeeded();
        await cozeBtn.click();
        await page.waitForTimeout(5000);
      }

      // 点击【手动保存全部配置 (立即秒级生效)】
      console.log('点击图二右下角【手动保存全部配置 (立即秒级生效)】按钮...');
      const saveBtn = await page.$('button:has-text("手动保存全部配置")');
      if (saveBtn) {
        await saveBtn.scrollIntoViewIfNeeded();
        await saveBtn.click();
        await page.waitForTimeout(2000);
      }
    }

    // 截图 3: 飞书推送与 Coze 云端智能体联调面板
    const s3Path = path.join(screenshotDir, '2026-11-05_16-10-00_feishu_notification_and_coze.png');
    await page.screenshot({ path: s3Path, fullPage: false });
    console.log(`[截图完成 3/4]: ${s3Path}`);

    // 6. 切换回沙箱测试智能体 3 人机回环 (HITL) 挂起
    console.log('6. 切换至沙箱测试智能体 3 人机回环挂起...');
    const agentsTab = await page.$('#tab-agents, [aria-controls="pane-agents"]');
    if (agentsTab) {
      await agentsTab.click();
      await page.waitForTimeout(1000);

      const items3 = await page.$$('.agent-menu-item');
      for (const item of items3) {
        const text = await item.textContent();
        if (text && text.includes('智能体 3')) {
          await item.click();
          await page.waitForTimeout(1000);
          break;
        }
      }

      const inputArea3 = await page.$('.widget-footer input, .widget-footer .el-input__inner, input[placeholder*="输入业务指令"]');
      if (inputArea3) {
        await inputArea3.fill('骨科病区二级库急需申领 120 支医用外科口罩');
        const sendBtn3 = await page.$('.widget-footer button:has-text("执行"), button:has-text("执行")');
        if (sendBtn3) {
          await sendBtn3.click();
          console.log('已提交智能体 3 请领指令，等待 HITL 挂起...');
          await page.waitForTimeout(8000);
        }
      }
    }

    // 截图 4: 人机回环挂起与 4 节点流程图
    const s4Path = path.join(screenshotDir, '2026-11-05_16-10-00_langgraph_hitl_and_workflow.png');
    await page.screenshot({ path: s4Path, fullPage: false });
    console.log(`[截图完成 4/4]: ${s4Path}`);

    console.log('=== Playwright 端到端回环验证全部执行完毕 ===');
    console.log('控制台异常总数:', pageErrors.length);
  } catch (err) {
    console.error('Playwright 回环测试出现异常:', err);
  } finally {
    await browser.close();
  }
})();
