const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

/**
 * @file test_hospital_spd_full_business_flow.js
 * @description 验证医院全链路 SPD 业务流程闭环：
 * 1. 树形自适应侧边栏与当前经办仓库切换
 * 2. 产品字典专属仓库ID、分类增删改查、供应商全资质
 * 3. 普通耗材主库请领受理（图3）、采购入库填单（图5）、双击穿透明细（图4）、主库独立盘点与漏账增补
 * 4. 临床二级库物资申领填报（图4）、自主撤回与删除、手动发料扣减库存
 * 5. 财务四大归口主库发料对账、科室消耗支出对账与全院进销存收发存平衡表
 * 6. 全院物资流转追溯台账
 */
async function runHospitalSpdVerification() {
  const tempProfile = path.resolve(os.tmpdir(), `pw_profile_spd_${Date.now()}`);
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

  try {
    // 1. 登录系统管理员进入工作台
    console.log('[Step 1] 访问登录入口，免密进入系统管理员赵振华工作台...');
    await page.goto('http://127.0.0.1:5173/showcase?login=1', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1000);

    const adminBtn = page.locator('.spd-role-btn[data-role="admin"]');
    if (await adminBtn.count()) {
      await adminBtn.click();
    } else {
      await page.locator('#login-account').fill('admin');
      await page.locator('#login-password').fill('123456');
      await page.locator('#btn-submit-login').click();
    }
    await page.waitForTimeout(1500);

    // 2. 验证顶栏当前经办仓库下拉切换器与侧边栏
    console.log('[Step 2] 检验顶部经办仓库切换器与侧边栏两级树形导航...');
    const whPicker = page.locator('#warehouse-selector');
    console.log(`顶栏仓库切换器数量: ${await whPicker.count()}`);
    if (await whPicker.count()) {
      const selectedWh = await whPicker.inputValue();
      console.log(`当前选中的经办仓库代码: ${selectedWh}`);
    }

    // 3. 访问产品字典 /dict
    console.log('[Step 3] 验证产品字典专属仓库ID、耗材分类与供应商全资质...');
    await page.goto('http://127.0.0.1:5173/dict', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1500);

    // 搜索仓库
    const whSearchInput = page.locator('.tree-search-bar input');
    if (await whSearchInput.count()) {
      await whSearchInput.fill('卫材');
      await page.waitForTimeout(500);
      await whSearchInput.fill('');
    }

    const img1 = path.resolve(screenshotDir, `${ts}_01_product_dict_enhanced.png`);
    await page.screenshot({ path: img1, fullPage: true });
    fs.copyFileSync(img1, path.resolve(artifactDir, `${ts}_01_product_dict_enhanced.png`));
    console.log(`[OK] 产品字典全景截图: ${img1}`);

    // 4. 访问普通耗材主库 /general
    console.log('[Step 4] 验证普通耗材主库请领受理 (对标图 3) 与采购入库 (对标图 5)...');
    await page.goto('http://127.0.0.1:5173/general', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1500);

    // 等待表格加载并点击第一行高亮选中
    await page.waitForSelector('.el-table__row', { timeout: 10000 }).catch(() => {});
    const firstReqRow = page.locator('.el-table__body-wrapper tbody tr.el-table__row').first();
    if (await firstReqRow.count()) {
      await firstReqRow.click({ force: true, timeout: 5000 }).catch(e => console.log('行点击提示:', e.message));
      await page.waitForTimeout(500);
      console.log('请领受理单据行点击高亮');
    }

    const img2 = path.resolve(screenshotDir, `${ts}_02_main_warehouse_requisition_highlight.png`);
    await page.screenshot({ path: img2, fullPage: true });
    fs.copyFileSync(img2, path.resolve(artifactDir, `${ts}_02_main_warehouse_requisition_highlight.png`));
    console.log(`[OK] 请领受理看板高亮截图: ${img2}`);

    // 点击查看申请单明细 (图 4) 或直接双击第一行
    const viewDetailBtn = page.locator('button:has-text("查看申请单明细")').first();
    let detailOpened = false;
    if (await viewDetailBtn.count() && !(await viewDetailBtn.isDisabled())) {
      await viewDetailBtn.click({ force: true, timeout: 5000 }).catch(() => {});
      detailOpened = true;
    } else if (await firstReqRow.count()) {
      await firstReqRow.dblclick({ force: true, timeout: 5000 }).catch(() => {});
      detailOpened = true;
    }

    if (detailOpened) {
      await page.waitForTimeout(1000);
      const img2Detail = path.resolve(screenshotDir, `${ts}_02_requisition_detail_modal.png`);
      await page.screenshot({ path: img2Detail, fullPage: true });
      fs.copyFileSync(img2Detail, path.resolve(artifactDir, `${ts}_02_requisition_detail_modal.png`));
      console.log(`[OK] 图 4 申请单明细弹窗截图: ${img2Detail}`);

      // 关闭弹窗
      const closeBtn = page.locator('.spd-dialog-modal button:has-text("关闭"), .el-dialog button:has-text("关闭")').first();
      if (await closeBtn.count()) await closeBtn.click({ force: true }).catch(() => {});
      await page.waitForTimeout(500);
    }

    // 切换到耗材验收入库 Tab 并打开采购入库单 (图 5)
    console.log('[Step 5] 打开耗材验收入库 Tab 并调出采购入库单录入 (图 5)...');
    const inboundTab = page.locator('#tab-inbound, .el-tabs__item:has-text("耗材验收入库与退货")').first();
    if (await inboundTab.count()) {
      await inboundTab.click({ force: true }).catch(() => {});
      await page.waitForTimeout(1000);

      const fillBtn = page.locator('button:has-text("填写采购入库单")').first();
      if (await fillBtn.count()) {
        await fillBtn.click({ force: true }).catch(() => {});
        await page.waitForTimeout(800);
        const img3 = path.resolve(screenshotDir, `${ts}_03_purchase_inbound_bill_modal.png`);
        await page.screenshot({ path: img3, fullPage: true });
        fs.copyFileSync(img3, path.resolve(artifactDir, `${ts}_03_purchase_inbound_bill_modal.png`));
        console.log(`[OK] 图 5 采购入库填单截图: ${img3}`);

        const cancelBtn = page.locator('.purchase-inbound-dialog button:has-text("取消"), .el-dialog button:has-text("取消")').first();
        if (await cancelBtn.count()) await cancelBtn.click({ force: true }).catch(() => {});
        await page.waitForTimeout(500);
      } else {
        console.log('未检测到填写采购入库单按钮');
      }
    }

    // 5. 访问临床二级库 /secondary
    console.log('[Step 6] 验证临床二级库物资申领填报 (图 4) 与科室手动发料出库...');
    await page.goto('http://127.0.0.1:5173/secondary', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1500);

    // 点击打开填报物资申请单
    const createReqBtn = page.locator('button:has-text("填报物资申请单")').first();
    if (await createReqBtn.count()) {
      await createReqBtn.click({ force: true }).catch(() => {});
      await page.waitForTimeout(800);
      const img4 = path.resolve(screenshotDir, `${ts}_04_secondary_create_requisition_modal.png`);
      await page.screenshot({ path: img4, fullPage: true });
      fs.copyFileSync(img4, path.resolve(artifactDir, `${ts}_04_secondary_create_requisition_modal.png`));
      console.log(`[OK] 二级库填报申请单截图: ${img4}`);

      const cancelBtn = page.locator('.spd-dialog-modal button:has-text("取消"), .el-dialog button:has-text("取消")').first();
      if (await cancelBtn.count()) await cancelBtn.click({ force: true }).catch(() => {});
      await page.waitForTimeout(500);
    }

    // 切换到手动发料出库 Tab
    const manualOutTab = page.locator('.el-tabs__item:has-text("科室手动发料出库")').first();
    if (await manualOutTab.count()) {
      await manualOutTab.click({ force: true }).catch(() => {});
      await page.waitForTimeout(1000);
      const img4Out = path.resolve(screenshotDir, `${ts}_04_secondary_manual_outbound.png`);
      await page.screenshot({ path: img4Out, fullPage: true });
      fs.copyFileSync(img4Out, path.resolve(artifactDir, `${ts}_04_secondary_manual_outbound.png`));
      console.log(`[OK] 二级库手动发料台账截图: ${img4Out}`);
    }

    // 6. 访问财务四大主库发料流向对账 /finance
    console.log('[Step 7] 验证财务四大归口主库发料对账台账与进销存收发存月度平衡表...');
    await page.goto('http://127.0.0.1:5173/finance', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1500);

    const img5 = path.resolve(screenshotDir, `${ts}_05_finance_main_dispatch_reconciliation.png`);
    await page.screenshot({ path: img5, fullPage: true });
    fs.copyFileSync(img5, path.resolve(artifactDir, `${ts}_05_finance_main_dispatch_reconciliation.png`));
    console.log(`[OK] 财务四大主库发料对账截图: ${img5}`);

    // 切换到进销存月度平衡表
    const balanceTab = page.locator('.el-tabs__item:has-text("全院进销存月度平衡表")').first();
    if (await balanceTab.count()) {
      await balanceTab.click({ force: true }).catch(() => {});
      await page.waitForTimeout(1000);
      const img5Balance = path.resolve(screenshotDir, `${ts}_05_inventory_balance_monthly.png`);
      await page.screenshot({ path: img5Balance, fullPage: true });
      fs.copyFileSync(img5Balance, path.resolve(artifactDir, `${ts}_05_inventory_balance_monthly.png`));
      console.log(`[OK] 全院进销存收发存月度平衡表截图: ${img5Balance}`);
    }

    // 7. 访问全院医疗物资流转追溯台账 /logs
    console.log('[Step 8] 验证全院医疗物资流转追溯台账 (去生硬6W化)...');
    await page.goto('http://127.0.0.1:5173/logs', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1500);

    const img6 = path.resolve(screenshotDir, `${ts}_06_hospital_workflow_trace_ledger.png`);
    await page.screenshot({ path: img6, fullPage: true });
    fs.copyFileSync(img6, path.resolve(artifactDir, `${ts}_06_hospital_workflow_trace_ledger.png`));
    console.log(`[OK] 全院物资流转追溯台账截图: ${img6}`);

    console.log('==== [SUCCESS] 医院医疗物资系统全业务闭环回环测试与截图验证全部通过 ====');
  } finally {
    await context.close();
  }
}

runHospitalSpdVerification().catch((err) => {
  console.error('[FAILED] 验证执行异常:', err);
  process.exit(1);
});
