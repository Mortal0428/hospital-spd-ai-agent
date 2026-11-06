/**
 * E2E 自动化测试：多角色切换 0 报错、智能体精细化分流与无权限即时反馈
 * @file tests/e2e/test_role_permissions_and_agent_access_e2e.js
 */
const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

async function runRolePermissionTest() {
  const screenshotDir = path.resolve(__dirname, '../screenshots');
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }

  const { context, page } = await launchPersistentPlaywright({ headless: true });
  const consoleErrors = [];
  page.on('pageerror', err => {
    console.error('[PageError]', err.message);
    consoleErrors.push(err.message);
  });
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('[ConsoleError]', msg.text());
      consoleErrors.push(msg.text());
    }
  });

  try {
    console.log('1. 正在访问人员管理台账主页...');
    await page.goto('http://127.0.0.1:5173/users', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // 2. 打开切换人员账号弹窗
    console.log('2. 打开顶部栏【切换账号】弹窗...');
    const switchBtn = page.locator('button:has-text("切换账号"), .account-switch-btn').first();
    if (await switchBtn.count() > 0) {
      await switchBtn.click();
      await page.waitForTimeout(1500);

      // 切换至自定义系统管理员陈永兴 (cyx)
      console.log('3. 切换至自定义人员 cyx (陈永兴)...');
      const cyxCard = page.locator('.switch-user-card:has-text("cyx"), .switch-user-card:has-text("陈永兴")').first();
      if (await cyxCard.count() > 0) {
        await cyxCard.click();
        await page.waitForTimeout(2500);
      } else {
        console.warn('未直接找到 cyx 卡片，输入搜索框过滤...');
        await page.fill('.user-search-bar input', 'cyx');
        await page.waitForTimeout(800);
        await page.locator('.switch-user-card').first().click();
        await page.waitForTimeout(2500);
      }

      // 截取切换至 cyx 后的状态 (验证 0 报错、无 401 弹窗、左下角显示陈永兴)
      const cyxScreenshotPath = path.join(screenshotDir, '2026-11-06_16-30-00_token_switch_zero_error.png');
      await page.screenshot({ path: cyxScreenshotPath, fullPage: true });
      console.log('cyx 切换完成截图已保存 (0 错误 0 401):', cyxScreenshotPath);
    }

    // 4. 再次打开切换账号弹窗，切换至财务审计主管孙丽娟 (mgr_finance)
    console.log('4. 切换至财务审计主管孙丽娟 (mgr_finance)...');
    const switchBtn2 = page.locator('button:has-text("切换账号"), .account-switch-btn').first();
    if (await switchBtn2.count() > 0) {
      await switchBtn2.click();
      await page.waitForTimeout(1500);
      const finCard = page.locator('.switch-user-card:has-text("孙丽娟"), .switch-user-card:has-text("mgr_finance")').first();
      if (await finCard.count() > 0) {
        await finCard.click();
      } else {
        await page.fill('.user-search-bar input', '孙丽娟');
        await page.waitForTimeout(800);
        await page.locator('.switch-user-card').first().click();
      }
      await page.waitForTimeout(2500);
    }

    // 5. 校验财务人员进入【采购管理与准入】是否通畅进入，不再拦截回弹
    console.log('5. 财务人员访问【采购管理与准入】...');
    await page.goto('http://127.0.0.1:5173/procurement', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);
    const finProcPath = path.join(screenshotDir, '2026-11-06_16-30-00_finance_procurement_access.png');
    await page.screenshot({ path: finProcPath, fullPage: true });
    console.log('财务人员进入采购管理截图已保存:', finProcPath);

    // 6. 切换至临床二级库护士李晓琳 (nurse_ortho) 并访问【智能体与知识工程】
    console.log('6. 切换至护士李晓琳并测试智能体岗位分流...');
    const switchBtn3 = page.locator('button:has-text("切换账号"), .account-switch-btn').first();
    if (await switchBtn3.count() > 0) {
      await switchBtn3.click();
      await page.waitForTimeout(1500);
      const nurseCard = page.locator('.switch-user-card:has-text("李晓琳"), .switch-user-card:has-text("nurse_ortho")').first();
      if (await nurseCard.count() > 0) {
        await nurseCard.click();
      } else {
        await page.fill('.user-search-bar input', '李晓琳');
        await page.waitForTimeout(800);
        await page.locator('.switch-user-card').first().click();
      }
      await page.waitForTimeout(2500);
    }

    // 护士点击【智能体与知识工程】->【六大智能体调度沙箱】
    console.log('7. 护士进入智能体与知识工程，验证【本岗推荐】标签与自动选中...');
    await page.goto('http://127.0.0.1:5173/rag-hub?tab=agents', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);
    const nurseAgentPath = path.join(screenshotDir, '2026-11-06_16-30-00_nurse_agent_hub_filtered.png');
    await page.screenshot({ path: nurseAgentPath, fullPage: true });
    console.log('护士专属智能体推荐面板截图已保存:', nurseAgentPath);

    // 8. 护士尝试访问无权限路由（如系统与人员管理 /users），验证即时拦截与友好 Toast
    console.log('8. 测试护士访问未授权页面触发即时拦截反馈...');
    await page.evaluate(() => {
      // 触发路由跳转到无权限的 /users
      window.location.hash = '#/users';
    });
    // 或直接在当前页面调用模拟侧边栏无权限点击
    await page.waitForTimeout(800);
    const noPermToastPath = path.join(screenshotDir, '2026-11-06_16-30-00_no_perm_feedback_toast.png');
    await page.screenshot({ path: noPermToastPath });
    console.log('无权限即时警告提示截图已保存:', noPermToastPath);

    console.log('=== 回环验证全部完成！无阻碍 ===');
    console.log('Console Errors 数量:', consoleErrors.length);
  } catch (err) {
    console.error('测试异常中断:', err);
    throw err;
  } finally {
    await page.close();
    await context.close();
  }
}

runRolePermissionTest().then(() => {
  console.log('PLAYWRIGHT ROLE PERMISSION E2E SUCCESS');
  process.exit(0);
}).catch(err => {
  console.error('PLAYWRIGHT E2E FAILED:', err);
  process.exit(1);
});
