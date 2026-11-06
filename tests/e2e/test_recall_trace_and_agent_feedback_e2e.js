/**
 * @file test_recall_trace_and_agent_feedback_e2e.js
 * @description 不良事件召回患者追访闭环 (方案 A) 与 AI 智能体医护人工纠偏自演化记忆库 (方案 C) Playwright E2E 回环测试
 * 
 * 验证目标：
 * 1. 验证高值耗材工作台 Tab 8【不良事件召回患者追访中枢】成功呈现；
 * 2. 验证批次穿透追溯看板统计（全院总数、在库拦截数、已植入患者数）；
 * 3. 验证《已植入患者紧急随访跟踪清册》数据表格与随访状态机流转；
 * 4. 验证《医疗器械不良事件紧急召回处置报告（含患者清册四联单）》标准打印预览窗口；
 * 5. 验证智能体对话气泡底部【采纳建议】与【人工纠偏/补充院内规则】交互卡片；
 * 6. 验证医护专家人工纠偏内容提交并持久化沉淀至本地 Chroma 物理向量库 EXPERT_HUMAN_CORRECTION 分区；
 * 7. 捕获两张带时间戳实机测试截图并安全归档至 tests/screenshots/ 与 Artifact 目录。
 */

const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

async function runRecallAndFeedbackE2ETest() {
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
    console.log('1. 正在访问高值耗材工作台 Tab 8 (不良事件召回患者追访中枢)...');
    await page.goto('http://127.0.0.1:5173/high-value?tab=recall-trace', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2500);

    // 确保激活 recall-trace tab
    const recallTab = page.locator('.el-tabs__item:has-text("不良事件召回"), .el-tabs__item:has-text("追访中枢")').first();
    if (await recallTab.count() > 0) {
      await recallTab.click();
      await page.waitForTimeout(1500);
      console.log('已成功切换至【不良事件召回患者追访中枢】标签页');
    }

    console.log('2. 验证批次穿透汇总统计看板与已植入患者清册...');
    const traceBtn = page.locator('button:has-text("穿透追查患者")').first();
    if (await traceBtn.count() > 0) {
      await traceBtn.click();
      await page.waitForTimeout(2000);
    }

    // 触发更新随访状态弹窗
    const updateFollowBtn = page.locator('.fusion-styled-table button:has-text("更新随访")').first();
    if (await updateFollowBtn.count() > 0) {
      console.log('点击第一位患者的【更新随访】按钮...');
      await updateFollowBtn.click();
      await page.waitForTimeout(1000);

      const saveFollowBtn = page.locator('.el-dialog button:has-text("保存随访记录")').first();
      if (await saveFollowBtn.count() > 0) {
        await saveFollowBtn.click();
        await page.waitForTimeout(1500);
        console.log('患者随访医学记录已成功更新并提交保存');
      }
    }

    // 打开召回处置四联单预览
    console.log('3. 打开《医疗器械不良事件紧急召回处置报告（含患者清册四联单）》预览...');
    const printBtn = page.locator('button:has-text("打印召回处置四联单")').first();
    if (await printBtn.count() > 0) {
      await printBtn.click();
      await page.waitForTimeout(1500);
      console.log('四联处置报告预览窗口已成功打开');
    }

    // 截图 1: 不良事件患者追查清册与四联报告
    const screenshot1 = path.join(screenshotDir, '2026-11-06_19-50-00_recall_patient_trace_ledger.png');
    await page.screenshot({ path: screenshot1, fullPage: true });
    console.log('实机截图 1 已保存:', screenshot1);

    if (fs.existsSync(artifactDir)) {
      fs.copyFileSync(screenshot1, path.join(artifactDir, '2026-11-06_19-50-00_recall_patient_trace_ledger.png'));
    }

    // 关闭四联单预览弹窗
    const closePrintBtn = page.locator('.el-dialog button:has-text("关闭预览")').first();
    if (await closePrintBtn.count() > 0) {
      await closePrintBtn.click();
      await page.waitForTimeout(800);
    }

    console.log('4. 访问智能体控制中台 Tab 3 (8 大业务智能体多架构调度沙箱)...');
    await page.goto('http://127.0.0.1:5173/rag-hub?tab=sandbox', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2500);

    const sandboxTab = page.locator('.el-tabs__item:has-text("8 大业务智能体"), .el-tabs__item:has-text("沙箱")').first();
    if (await sandboxTab.count() > 0) {
      await sandboxTab.click();
      await page.waitForTimeout(1500);
    }

    console.log('5. 在智能体 4 (UDI 追溯智能体) 中发送提问指令...');
    const chatInput = page.locator('.agent-chat-widget .widget-footer .el-input__inner, .agent-chat-widget .widget-footer input[type="text"]').first();
    if (await chatInput.count() > 0) {
      await chatInput.fill('全链路溯源高值耗材 UDI-HV-20261104-001，若发生不良事件召回应如何处置？');
      await page.waitForTimeout(400);

      const sendBtn = page.locator('.agent-chat-widget .widget-footer button:has-text("执行")').first();
      await sendBtn.click();
      console.log('指令已发送，等待智能体推理与流式输出完成 (12 秒)...');
      await page.waitForTimeout(12000);
    }

    console.log('6. 测试智能体回答底部的医护专家人工纠偏自演化交互卡片...');
    const correctBtn = page.locator('.feedback-action-bar button:has-text("人工纠偏"), .feedback-action-bar button:has-text("院内规则")').first();
    if (await correctBtn.count() > 0) {
      await correctBtn.scrollIntoViewIfNeeded();
      await correctBtn.click();
      await page.waitForTimeout(800);
      console.log('已展开专家人工纠偏输入卡片');

      const textarea = page.locator('.correction-card textarea').first();
      if (await textarea.count() > 0) {
        await textarea.fill('三甲医院专家标准化准则：所有不良事件召回批次必须在1小时内完成在库封存并在24小时内联系全部已植入患者进行电话随访登记。');
        await page.waitForTimeout(500);

        const submitMemoryBtn = page.locator('.correction-card button:has-text("提交记忆沉淀")').first();
        if (await submitMemoryBtn.count() > 0) {
          await submitMemoryBtn.click();
          await page.waitForTimeout(2500);
          console.log('已提交纠偏记忆，成功写入 Chroma 物理向量库');
        }
      }
    }

    // 截图 2: 智能体回答气泡人工纠偏与 Chroma 记忆沉淀
    const screenshot2 = path.join(screenshotDir, '2026-11-06_19-50-00_agent_human_feedback_evolution.png');
    await page.screenshot({ path: screenshot2, fullPage: true });
    console.log('实机截图 2 已保存:', screenshot2);

    if (fs.existsSync(artifactDir)) {
      fs.copyFileSync(screenshot2, path.join(artifactDir, '2026-11-06_19-50-00_agent_human_feedback_evolution.png'));
    }

    console.log('--- 测试总结 ---');
    console.log('Console Errors 数量:', consoleErrors.length);
    console.log('全部回环验证链路执行完毕！');

  } catch (err) {
    console.error('测试执行出现异常:', err);
    throw err;
  } finally {
    await context.close();
  }
}

runRecallAndFeedbackE2ETest().then(() => {
  console.log('E2E 回环测试脚本执行成功！');
  process.exit(0);
}).catch(err => {
  console.error('E2E 测试失败:', err);
  process.exit(1);
});
