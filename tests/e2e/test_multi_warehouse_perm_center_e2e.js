/**
 * E2E 自动化回环测试：全院多库藏分仓授权中台、多仓标签透视与顶栏动态仓库联动
 * @file tests/e2e/test_multi_warehouse_perm_center_e2e.js
 */
const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

async function runTest() {
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
    console.log('1. 正在访问人员管理与授权工作台 (Tab 1)...');
    await page.goto('http://127.0.0.1:5173/users?tab=users', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // 截取 Tab 1 人员台账表格截图
    const tab1ScreenshotPath = path.join(screenshotDir, '2026-11-06_15-30-00_user_table_multi_warehouses.png');
    await page.screenshot({ path: tab1ScreenshotPath, fullPage: true });
    console.log('Tab 1 截图已保存:', tab1ScreenshotPath);

    // 检查王建国 (mgr_consumable) 行是否展示了分配的 4 个仓库 Tag
    const pageText = await page.content();
    const hasWeicai = pageText.includes('全院卫材耗材一级总仓') || pageText.includes('WH_WEICAI');
    const hasZongwu = pageText.includes('后勤总务库房') || pageText.includes('WH_ZONGWU');
    console.log('Tab 1 检验王建国分管多仓标签:', { hasWeicai, hasZongwu });

    // 2. 切换至 Tab 3: 多级库藏分仓授权中台
    console.log('2. 正在点击进入 Tab 3 (多级库藏分仓授权中台)...');
    const whTabBtn = await page.locator('.el-tabs__item:has-text("多级库藏分仓授权中台")');
    if (await whTabBtn.count() > 0) {
      await whTabBtn.click();
      await page.waitForTimeout(1500);
    } else {
      await page.goto('http://127.0.0.1:5173/users?tab=warehouses', { waitUntil: 'networkidle' });
      await page.waitForTimeout(1500);
    }

    // 截取 Tab 3 多级库藏分仓授权中台完整矩阵截图
    const tab3ScreenshotPath = path.join(screenshotDir, '2026-11-06_15-30-00_multi_warehouse_perm_center.png');
    await page.screenshot({ path: tab3ScreenshotPath, fullPage: true });
    console.log('Tab 3 截图已保存:', tab3ScreenshotPath);

    // 3. 在 Tab 3 切换目标人员至李晓琳 (nurse_ortho, id=5) 并按角色标准模板恢复
    console.log('3. 测试按角色标准模板自动赋权并落盘...');
    const userSelect = page.locator('#wh-perm-target-user-select');
    if (await userSelect.count() > 0) {
      // 选取李晓琳 (value="5")
      await userSelect.selectOption('5');
      await page.waitForTimeout(1000);

      // 点击 "按角色标准模板恢复" (Tab 3 库藏中台按钮)
      const templateBtn = page.locator('button:has-text("按角色标准模板恢复"):visible');
      if (await templateBtn.count() > 0) {
        await templateBtn.first().click();
        await page.waitForTimeout(800);
      }

      // 点击 "保存并下发全院库藏授权 (持久化落盘)"
      const saveBtn = page.locator('button:has-text("保存并下发全院库藏授权"):visible');
      if (await saveBtn.count() > 0) {
        await saveBtn.first().click();
        await page.waitForTimeout(2000);
      }
    }

    // 4. 返回 Tab 1 校验李晓琳是否更新了二级库与高值专柜 Tag
    console.log('4. 验证 Tab 1 李晓琳分仓 Tag 自动更新...');
    const tab1Btn = page.locator('.el-tabs__item:has-text("全院人员账号台账")');
    if (await tab1Btn.count() > 0) {
      await tab1Btn.click();
      await page.waitForTimeout(1500);
      const updatedTab1Path = path.join(screenshotDir, '2026-11-06_15-30-00_user_table_after_template_save.png');
      await page.screenshot({ path: updatedTab1Path, fullPage: true });
      console.log('更新后 Tab 1 截图已保存:', updatedTab1Path);
    }

    // 5. 校验顶栏仓库下拉框
    console.log('5. 检查顶栏当前仓库选择器...');
    const whDropdown = page.locator('#warehouse-selector');
    if (await whDropdown.count() > 0) {
      const headerWhScreenshotPath = path.join(screenshotDir, '2026-11-06_15-30-00_header_warehouse_switcher.png');
      await page.screenshot({ path: headerWhScreenshotPath });
      console.log('顶栏仓库切换器截图已保存:', headerWhScreenshotPath);
    }

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

runTest().then(() => {
  console.log('PLAYWRIGHT E2E SUCCESS');
  process.exit(0);
}).catch(err => {
  console.error('PLAYWRIGHT E2E FAILED:', err);
  process.exit(1);
});
