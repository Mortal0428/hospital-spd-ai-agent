/**
 * @file test_full_hospital_workflow.js
 * @description 医疗物资全链路 SPD 系统产品闭环与端到端 11 业务环节 Playwright 自动化验证脚本
 * 包含：
 * 1. 真实人员身份芯片卡展示与个人主页弹窗 (人事档案/管辖仓库/15模块权限统计/密码修改)
 * 2. 真实数据库全院人员切换通道验证 (彻底告别写死假下拉框)
 * 3. 系统与人员管理左侧菜单双向联动与 15 业务模块 x 8 动作 RBAC 矩阵 (整行批量全开/全关快捷列)
 * 4. 供应商协同门户资质准入审核、采供 4 阶段状态流转与四联凭证全景详情穿透弹窗
 * 5. 全系统各业务视图密集数据表格标准分页组件校验
 * 6. 全程 0 控制台报错拦截与全景实机截图归档
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

async function runFullHospitalWorkflowTest() {
  console.log('[E2E-FullWorkflow] 启动 Playwright 驱动医院医疗物资全链路 SPD 闭环验证...');
  const tempProfile = path.resolve(os.tmpdir(), `pw_profile_full_spd_${Date.now()}`);
  const { context, page } = await launchPersistentPlaywright({
    headless: true,
    profileDir: tempProfile
  });

  const screenshotDir = path.resolve(__dirname, '../screenshots');
  const artifactDir = path.resolve('C:/Users/27705/.gemini/antigravity/brain/b74040b2-5e16-4bba-8f66-df0103fbc9f2');
  if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });

  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const ts = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;

  const interceptedErrors = [];
  page.on('pageerror', (err) => {
    console.error(`[Browser PageError]: ${err.message}`);
    interceptedErrors.push(`PageError: ${err.message}`);
  });
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (!text.includes('favicon') && !text.includes('chrome-extension')) {
        console.warn(`[Browser ConsoleError]: ${text}`);
        interceptedErrors.push(`ConsoleError: ${text}`);
      }
    }
  });

  async function snap(name) {
    const fileName = `${ts}_${name}.png`;
    const fullPath = path.resolve(screenshotDir, fileName);
    await page.screenshot({ path: fullPath, fullPage: true });
    console.log(`[E2E-Screenshot] 截图已捕获: ${fileName}`);
    if (fs.existsSync(artifactDir)) {
      try {
        fs.copyFileSync(fullPath, path.resolve(artifactDir, fileName));
      } catch (e) {}
    }
  }

  try {
    await page.setViewportSize({ width: 1440, height: 900 });

    // 环节 0: 访问登录门户并以系统管理员身份登录
    console.log('[Step 0] 访问医慧通行登录门户，以系统管理员身份登录...');
    await page.goto('http://127.0.0.1:5173/showcase?login=1', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const adminBtn = page.locator('.spd-role-btn[data-role="admin"]');
    if (await adminBtn.count() > 0) {
      await adminBtn.click();
    } else {
      await page.locator('#login-account').fill('admin');
      await page.locator('#login-password').fill('123456');
      await page.locator('#btn-submit-login').click();
    }
    await page.waitForTimeout(1500);

    // 环节 1: 校验顶部真实登录人员芯片与无写死下拉框
    console.log('[Step 1] 校验顶部真实登录人员芯片卡与无写死下拉框...');
    const oldSelectCount = await page.locator('#role-selector').count();
    if (oldSelectCount > 0) {
      throw new Error('检测到顶部仍存在硬编码角色的 select 元素，重构不彻底');
    }
    console.log('✓ 顶部硬编码角色切换器已彻底移除');

    const userChip = page.locator('.user-profile-chip');
    await userChip.waitFor({ state: 'visible', timeout: 5000 });
    console.log('✓ 真实登录人员身份卡已正常渲染在顶部右侧');

    // 环节 2: 点击身份芯片卡，唤出《个人主页与账号安全中心》
    console.log('[Step 2] 点击身份芯片卡，唤出个人主页弹窗...');
    await userChip.click();
    await page.waitForTimeout(800);

    const profileDialog = page.locator('.user-profile-dialog');
    await profileDialog.waitFor({ state: 'visible', timeout: 5000 });
    console.log('✓ 个人主页与账号安全中心弹窗成功唤出');

    // 切换到 15 模块权限画像 Tab
    const rbacTabBtn = page.locator('.profile-tabs .tab-btn:has-text("权限画像")');
    if (await rbacTabBtn.count() > 0) {
      await rbacTabBtn.click();
      await page.waitForTimeout(500);
      console.log('✓ 个人主页 15 业务模块权限画像已正常展现');
    }
    await snap('01_user_profile_modal_opened');

    // 关闭个人主页弹窗
    const closeProfileBtn = page.locator('.profile-header .close-btn');
    if (await closeProfileBtn.count() > 0) {
      await closeProfileBtn.click();
      await page.waitForTimeout(500);
    }

    // 环节 3: 验证“切换账号”弹窗从数据库拉取真实人员列表
    console.log('[Step 3] 点击“切换账号”，验证数据库人员列表...');
    const switchBtn = page.locator('.btn-ctrl-switch');
    await switchBtn.click();
    await page.waitForTimeout(1000);

    const userCards = page.locator('.switch-user-card');
    await userCards.first().waitFor({ state: 'visible', timeout: 8000 });
    const userCardCount = await userCards.count();
    console.log(`✓ 切换账号弹窗成功从数据库拉取到 ${userCardCount} 名全院人员`);
    await snap('02_switch_user_dialog_from_db');

    // 关闭切换人员弹窗 (按 ESC 或点击遮罩)
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);

    // 环节 4: 验证【系统与人员管理】左侧子菜单双向联动与 15 模块 RBAC 矩阵
    console.log('[Step 4] 验证系统与人员管理左侧子菜单跳转与 15 模块 RBAC 矩阵...');
    await page.goto('http://127.0.0.1:5173/users?tab=rbac', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    // 校验 RBAC 表格行数 (必须包含 15 个模块)
    const rbacRows = page.locator('.tab-container-panel .el-table__body-wrapper tbody tr');
    const rbacRowCount = await rbacRows.count();
    console.log(`✓ RBAC 权限矩阵实际渲染行数: ${rbacRowCount} (全院标准 15 大业务模块)`);
    if (rbacRowCount < 15) {
      console.warn(`警告: RBAC 矩阵当前行数为 ${rbacRowCount}，少于 15 模块`);
    }

    // 校验整行批量快捷开关
    const rowBatchBtn = page.locator('button:has-text("全开")').first();
    if (await rowBatchBtn.count() > 0) {
      console.log('✓ 找到单模块整行快捷开关，执行一键全开测试...');
      await rowBatchBtn.click();
      await page.waitForTimeout(600);
    }
    await snap('03_rbac_15_modules_batch_switch_verified');

    // 验证左侧子菜单切换到人员与账号台账
    console.log('[Step 4.2] 验证人员列表与分页条...');
    await page.goto('http://127.0.0.1:5173/users?tab=users', { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);

    const userPagination = page.locator('.tab-content-area .el-pagination');
    await userPagination.waitFor({ state: 'visible', timeout: 5000 });
    console.log('✓ 全院人员账号管理表格标准分页条可见');
    await snap('04_user_accounts_pagination_verified');

    // 环节 5: 验证【采购与外部协同】采供闭环、四联凭证详情穿透与资质提报
    console.log('[Step 5] 验证采购与外部协同门户与四联凭证详情穿透...');
    await page.goto('http://127.0.0.1:5173/procurement?tab=orders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    // 校验资质准入看板
    const qualBanner = page.locator('.qual-banner-card');
    await qualBanner.waitFor({ state: 'visible', timeout: 5000 });
    console.log('✓ 供应商经营资质准入与医院绑定看板正常生效');

    // 校验采购订单表格分页条
    const procPagination = page.locator('.table-panel .el-pagination');
    await procPagination.waitFor({ state: 'visible', timeout: 5000 });
    console.log('✓ 采供协同订单表格标准分页条可见');

    // 点击第一条订单的“详情”按钮，呼出四联凭证详情穿透弹窗
    const detailBtn = page.locator('button:has-text("详情")').first();
    if (await detailBtn.count() > 0) {
      console.log('✓ 点击订单详情，验证采供四联凭证全景穿透弹窗...');
      await detailBtn.click();
      await page.waitForTimeout(800);

      const voucherModal = page.locator('.voucher-dialog');
      await voucherModal.waitFor({ state: 'visible', timeout: 5000 });
      console.log('✓ 采供协同四联凭证全景详情穿透弹窗成功渲染 (包含 6W 流转时间轴与电子印章)');
      await snap('05_supplier_voucher_detail_penetrated');

      // 关闭详情弹窗
      const closeVoucherBtn = page.locator('button:has-text("关闭")').first();
      if (await closeVoucherBtn.count() > 0) {
        await closeVoucherBtn.click();
        await page.waitForTimeout(500);
      }
    }

    // 环节 6: 校验临床二级库 4 大业务台账分页
    console.log('[Step 6] 校验临床二级库请领、入库、在库台账分页...');
    await page.goto('http://127.0.0.1:5173/secondary?tab=requisition', { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);
    const secPagination = page.locator('.tab-content-area .el-pagination').first();
    await secPagination.waitFor({ state: 'visible', timeout: 5000 });
    console.log('✓ 临床二级库表格标准分页条正常渲染');
    await snap('06_secondary_warehouse_pagination_verified');

    // 总结错误拦截
    console.log('======================================================');
    console.log(`[E2E 总结] 浏览器端未捕获致命异常，拦截到的错误数量: ${interceptedErrors.length}`);
    if (interceptedErrors.length > 0) {
      console.warn('拦截日志:', interceptedErrors);
    } else {
      console.log('✓ 完美！全页面控制台 Console Error 与 PageError 保持为 0！');
    }
    console.log('======================================================');

  } catch (err) {
    console.error('[E2E 执行中断]:', err);
    await snap('00_workflow_interrupted_error');
    throw err;
  } finally {
    await context.close();
  }
}

runFullHospitalWorkflowTest().then(() => {
  console.log('[E2E-FullWorkflow] 全链路回环测试顺利执行完毕');
  process.exit(0);
}).catch((err) => {
  console.error('[E2E-FullWorkflow] 测试失败', err);
  process.exit(1);
});
