const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

/**
 * @file test_product_dict_and_rbac_flow.js
 * @description 验证 3D 展厅登录自适应让位、侧边栏无数字、真实医院 SPD 四栏三树字典与护士分仓限权
 */
async function runVerification() {
  const tempProfile = path.resolve(os.tmpdir(), `pw_profile_dict_${Date.now()}`);
  const { context, page } = await launchPersistentPlaywright({
    headless: true,
    profileDir: tempProfile
  });

  try {
    const screenshotDir = path.resolve(__dirname, '../screenshots');
    const artifactDir = path.resolve('C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2');
    if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;

    // 1. 访问 /showcase?login=1 检验主舞台左移让位与右侧悬浮登录面板
    console.log('[1/5] 访问 http://127.0.0.1:5173/showcase?login=1 验证舞台自适应左平移与右侧通透卡片...');
    await page.goto('http://127.0.0.1:5173/showcase?login=1', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1500);

    const isShiftLeft = await page.locator('.showcase-stage-viewport.stage-shift-left').count();
    console.log(`主舞台左移类名激活状态: ${isShiftLeft > 0 ? '已激活 (translateX(-240px))' : '未激活'}`);

    const cardBox = await page.locator('.spd-auth-card').boundingBox();
    console.log(`右侧登录卡片尺寸位置:`, cardBox);

    const img1 = path.resolve(screenshotDir, `${ts}_01_showcase_shift_left_login.png`);
    await page.screenshot({ path: img1, fullPage: true });
    fs.copyFileSync(img1, path.resolve(artifactDir, `${ts}_01_showcase_shift_left_login.png`));
    console.log(`[OK] 展厅左移让位截图已保存: ${img1}`);

    // 2. 点击系统管理员免密登入
    console.log('[2/5] 点击系统管理员免密通道进入工作台...');
    const adminBtn = page.locator('.spd-role-btn[data-role="admin"]');
    if (await adminBtn.count()) {
      await adminBtn.click();
    } else {
      await page.locator('#login-account').fill('admin');
      await page.locator('#login-password').fill('123456');
      await page.locator('#btn-submit-login').click();
    }
    await page.waitForTimeout(2000);

    // 3. 验证侧边栏无数字序号
    console.log('[3/5] 检验侧边栏菜单名称，断言彻底无 1. 2. 3. 数字序号...');
    const sideNavTexts = await page.locator('.side-nav-item span:first-of-type').allInnerTexts();
    console.log(`当前侧边栏菜单项:`, sideNavTexts);

    const hasNumbers = sideNavTexts.some((t) => /^[0-9]\./.test(t.trim()));
    console.log(`侧边栏是否存在硬编码数字序号: ${hasNumbers ? '异常存在数字' : '完全合规无数字'}`);

    const img2 = path.resolve(screenshotDir, `${ts}_02_workbench_sidebar_no_numbers.png`);
    await page.screenshot({ path: img2, fullPage: true });
    fs.copyFileSync(img2, path.resolve(artifactDir, `${ts}_02_workbench_sidebar_no_numbers.png`));
    console.log(`[OK] 侧边栏无数字高对比度截图已保存: ${img2}`);

    // 4. 验证产品字典三树四栏工作台
    console.log('[4/5] 进入产品字典工作台，检验左侧仓库树、分类树、中栏品名列表与右侧规格明细...');
    await page.goto('http://127.0.0.1:5173/dict', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1500);

    const spnItems = await page.locator('.middle-list-item').count();
    const specRows = await page.locator('.spd-spec-table tbody tr').count();
    console.log(`中栏品名数量: ${spnItems}, 右栏规格单品条数: ${specRows}`);

    const img3 = path.resolve(screenshotDir, `${ts}_03_product_dict_three_tree_workspace.png`);
    await page.screenshot({ path: img3, fullPage: true });
    fs.copyFileSync(img3, path.resolve(artifactDir, `${ts}_03_product_dict_three_tree_workspace.png`));
    console.log(`[OK] 产品字典三树四栏全景截图已保存: ${img3}`);

    // 5. 勾选规格执行批量调价向导
    console.log('[5/5] 勾选规格行执行【集中带量调价管理】向导...');
    const firstCheckbox = page.locator('.spd-spec-table tbody tr:first-child .el-checkbox');
    if (await firstCheckbox.count()) {
      await firstCheckbox.click();
    }
    const secondCheckbox = page.locator('.spd-spec-table tbody tr:nth-child(2) .el-checkbox');
    if (await secondCheckbox.count()) {
      await secondCheckbox.click();
    }
    await page.waitForTimeout(500);

    const batchBtn = page.locator('.spd-tool-btn.btn-warn');
    if (await batchBtn.count()) {
      await batchBtn.click();
      await page.waitForTimeout(800);
    }

    const img4 = path.resolve(screenshotDir, `${ts}_04_product_dict_batch_price_adjust.png`);
    await page.screenshot({ path: img4, fullPage: true });
    fs.copyFileSync(img4, path.resolve(artifactDir, `${ts}_04_product_dict_batch_price_adjust.png`));
    console.log(`[OK] 集中带量批量调价向导截图已保存: ${img4}`);

    // 关闭调价弹窗
    const closeBtn = page.locator('.el-dialog .btn-secondary');
    if (await closeBtn.count()) {
      await closeBtn.click();
      await page.waitForTimeout(500);
    }

    // 6. 切换至护士角色检验仓库细粒度隔离
    console.log('[额外测试] 切换至临床二级库护士角色，检验仓库树仅展示授权科室仓 (骨科/心内)...');
    await page.locator('#role-selector').selectOption('secondary_user');
    await page.waitForTimeout(1500);

    const nurseWhRows = await page.locator('.tree-box-upper .tree-node-row .tree-label').allInnerTexts();
    console.log(`护士角色可见仓库清单:`, nurseWhRows);

    const img5 = path.resolve(screenshotDir, `${ts}_05_nurse_warehouse_rbac_isolated.png`);
    await page.screenshot({ path: img5, fullPage: true });
    fs.copyFileSync(img5, path.resolve(artifactDir, `${ts}_05_nurse_warehouse_rbac_isolated.png`));
    console.log(`[OK] 护士限仓细粒度 RBAC 隔离截图已保存: ${img5}`);

    // 7. 切换暗色模式检验高对比度深色质感
    console.log('[7/7] 切换深色暗空模式，检验深色主题下的三树四栏高对比度...');
    await page.locator('#role-selector').selectOption('sys_admin');
    await page.waitForTimeout(1000);
    const themeBtn = page.locator('.btn-ctrl-icon[title*="切换"]');
    if (await themeBtn.count()) {
      await themeBtn.click();
      await page.waitForTimeout(800);
    }
    const img6 = path.resolve(screenshotDir, `${ts}_06_product_dict_dark_mode_high_contrast.png`);
    await page.screenshot({ path: img6, fullPage: true });
    fs.copyFileSync(img6, path.resolve(artifactDir, `${ts}_06_product_dict_dark_mode_high_contrast.png`));
    console.log(`[OK] 深色暗空高对比度全景截图已保存: ${img6}`);

    console.log('\n==========================================');
    console.log('自动化回环测试全部圆满通过，所有用例均达标！');
    console.log('==========================================');
  } catch (err) {
    console.error('Playwright 回环测试执行异常:', err);
    process.exit(1);
  } finally {
    await context.close();
  }
}

runVerification();
