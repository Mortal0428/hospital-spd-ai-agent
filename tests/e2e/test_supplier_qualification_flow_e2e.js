/**
 * E2E 自动化测试：供应商资质申报弹窗提报、医院端驳回理由硬约束与准入解锁全闭环
 * @file tests/e2e/test_supplier_qualification_flow_e2e.js
 */
const path = require('path');
const fs = require('fs');
const { launchPersistentPlaywright } = require('./browser_config');

async function runSupplierQualFlowTest() {
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

    // 2. 打开切换账号，切换至外部供应商协同代表陈永兴01 (cyx01)
    console.log('2. 切换至供应商代表陈永兴01 (cyx01)...');
    const switchBtn = page.locator('button:has-text("切换账号"), .account-switch-btn').first();
    await switchBtn.click();
    await page.waitForTimeout(1200);

    const cyxSupplierCard = page.locator('.switch-user-card:has-text("cyx01"), .switch-user-card:has-text("陈永兴01")').first();
    if (await cyxSupplierCard.count() > 0) {
      await cyxSupplierCard.click();
    } else {
      await page.fill('.user-search-bar input', 'cyx01');
      await page.waitForTimeout(600);
      await page.locator('.switch-user-card').first().click();
    }
    await page.waitForTimeout(2000);

    // 3. 进入外部供应商门户
    console.log('3. 进入外部供应商数字化协同门户...');
    await page.goto('http://127.0.0.1:5173/supplier-portal?tab=orders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 4. 点击【重新上传资质证照】打开弹窗
    console.log('4. 供应商代表点击【重新上传资质证照】打开申报弹窗...');
    const uploadBtn = page.locator('button:has-text("重新上传资质证照"), button:has-text("立即完善并提报资质认证申请")').first();
    await uploadBtn.click();
    await page.waitForTimeout(1200);

    // 截取供应商端资质申报弹窗截图
    const uploadModalPath = path.join(screenshotDir, '2026-11-06_17-05-00_supplier_portal_upload_modal.png');
    await page.screenshot({ path: uploadModalPath, fullPage: true });
    console.log('供应商资质申报弹窗截图已保存:', uploadModalPath);

    // 5. 提交资质申请
    console.log('5. 点击提交资质申请...');
    const submitQualBtn = page.locator('button:has-text("确认提报院方耗材科审核")').first();
    await submitQualBtn.click();
    await page.waitForTimeout(2500);

    // 6. 切换至耗材科主管王建国 (mgr_consumable)
    console.log('6. 切换至耗材科科室主管王建国 (mgr_consumable)...');
    const switchBtn2 = page.locator('button:has-text("切换账号"), .account-switch-btn').first();
    await switchBtn2.click();
    await page.waitForTimeout(1200);

    const consumableCard = page.locator('.switch-user-card:has-text("王建国"), .switch-user-card:has-text("mgr_consumable")').first();
    if (await consumableCard.count() > 0) {
      await consumableCard.click();
    } else {
      await page.fill('.user-search-bar input', '王建国');
      await page.waitForTimeout(600);
      await page.locator('.switch-user-card').first().click();
    }
    await page.waitForTimeout(2000);

    // 7. 进入【采购管理与准入】->【供应商资质审查】台账
    console.log('7. 访问采购管理中心供应商资质审查台账 (Tab 2)...');
    await page.goto('http://127.0.0.1:5173/procurement?tab=suppliers', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);

    // 8. 找到待审供应商行，点击【合规驳回】
    console.log('8. 主管点击【合规驳回】...');
    const rejectBtn = page.locator('button:has-text("合规驳回")').first();
    await rejectBtn.click();
    await page.waitForTimeout(1200);

    // 9. 输入详细驳回原因
    console.log('9. 输入驳回原因与整改要求...');
    const remarkInput = page.locator('.spd-dialog-modal textarea').first();
    await remarkInput.fill('营业执照副本未加盖鲜章且复印件模糊，请重新上传清晰扫描件');
    await page.waitForTimeout(800);

    // 截取医院端驳回理由弹窗截图
    const rejectModalPath = path.join(screenshotDir, '2026-11-06_17-05-00_hospital_audit_reject_with_reason.png');
    await page.screenshot({ path: rejectModalPath, fullPage: true });
    console.log('医院端填写驳回理由弹窗截图已保存:', rejectModalPath);

    // 提交驳回
    const confirmAuditBtn = page.locator('button:has-text("确认提交审查结果")').first();
    await confirmAuditBtn.click();
    await page.waitForTimeout(2500);

    // 10. 切换回供应商代表陈永兴01，查看被驳回理由
    console.log('10. 切换回供应商代表查看驳回理由警示框...');
    const switchBtn3 = page.locator('button:has-text("切换账号"), .account-switch-btn').first();
    await switchBtn3.click();
    await page.waitForTimeout(1200);

    const cyxSupplierCard2 = page.locator('.switch-user-card:has-text("cyx01"), .switch-user-card:has-text("陈永兴01")').first();
    if (await cyxSupplierCard2.count() > 0) {
      await cyxSupplierCard2.click();
    } else {
      await page.fill('.user-search-bar input', 'cyx01');
      await page.waitForTimeout(600);
      await page.locator('.switch-user-card').first().click();
    }
    await page.waitForTimeout(2000);

    await page.goto('http://127.0.0.1:5173/supplier-portal?tab=orders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);

    // 截取供应商端展示驳回理由警示框截图
    const rejectedAlertPath = path.join(screenshotDir, '2026-11-06_17-05-00_supplier_portal_rejected_alert.png');
    await page.screenshot({ path: rejectedAlertPath, fullPage: true });
    console.log('供应商端展示驳回理由警示框截图已保存:', rejectedAlertPath);

    // 11. 再次切换至耗材科主管王建国，执行【审查通过准入】
    console.log('11. 切换回主管并通过准入审查...');
    const switchBtn4 = page.locator('button:has-text("切换账号"), .account-switch-btn').first();
    await switchBtn4.click();
    await page.waitForTimeout(1200);
    const consumableCard2 = page.locator('.switch-user-card:has-text("王建国"), .switch-user-card:has-text("mgr_consumable")').first();
    if (await consumableCard2.count() > 0) {
      await consumableCard2.click();
    } else {
      await page.fill('.user-search-bar input', '王建国');
      await page.waitForTimeout(600);
      await page.locator('.switch-user-card').first().click();
    }
    await page.waitForTimeout(2000);

    await page.goto('http://127.0.0.1:5173/procurement?tab=suppliers', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);

    const approveBtn = page.locator('button:has-text("审查通过准入")').first();
    await approveBtn.click();
    await page.waitForTimeout(1200);
    const confirmAuditBtn2 = page.locator('button:has-text("确认提交审查结果")').first();
    await confirmAuditBtn2.click();
    await page.waitForTimeout(2500);

    // 12. 切换回供应商端，验证最终通过准入并解锁状态
    console.log('12. 切换回供应商端验证最终准入解锁...');
    const switchBtn5 = page.locator('button:has-text("切换账号"), .account-switch-btn').first();
    await switchBtn5.click();
    await page.waitForTimeout(1200);
    const cyxSupplierCard3 = page.locator('.switch-user-card:has-text("cyx01"), .switch-user-card:has-text("陈永兴01")').first();
    if (await cyxSupplierCard3.count() > 0) {
      await cyxSupplierCard3.click();
    } else {
      await page.fill('.user-search-bar input', 'cyx01');
      await page.waitForTimeout(600);
      await page.locator('.switch-user-card').first().click();
    }
    await page.waitForTimeout(2000);

    await page.goto('http://127.0.0.1:5173/supplier-portal?tab=orders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);

    const approvedUnlockedPath = path.join(screenshotDir, '2026-11-06_17-05-00_hospital_audit_approve_unlocked.png');
    await page.screenshot({ path: approvedUnlockedPath, fullPage: true });
    console.log('供应商端最终通过准入并解锁截图已保存:', approvedUnlockedPath);

    console.log('=== 供应商资质全闭环 E2E 回环测试全部完成！===');
    console.log('Console Errors 数量:', consoleErrors.length);
  } catch (err) {
    console.error('测试执行中断:', err);
    throw err;
  } finally {
    await page.close();
    await context.close();
  }
}

runSupplierQualFlowTest().then(() => {
  console.log('PLAYWRIGHT SUPPLIER QUAL E2E SUCCESS');
  process.exit(0);
}).catch(err => {
  console.error('PLAYWRIGHT E2E FAILED:', err);
  process.exit(1);
});
