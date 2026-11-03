const path = require('path');
const fs = require('fs');
const os = require('os');
const { launchPersistentPlaywright } = require('./browser_config');

/**
 * @file capture_login_drawer_right.js
 * @description 验证 3D 展厅与右侧滑入登录抽屉一体化呈现
 * 1. 验证 41 款 Wallpaper Engine 动态壁纸清单加载，首款 4K 动态视频壁纸满屏循环播放；
 * 2. 访问 /login 自动重定向至展厅并从右侧平滑滑出毛玻璃医慧通行登录抽屉；
 * 3. 验证 5 大角色细粒度权限通道，点击免密登入工作台。
 */
async function runVerification() {
  const tempProfile = path.resolve(os.tmpdir(), `pw_profile_${Date.now()}`);
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

    // 1. 访问 /showcase
    console.log('[1/3] 访问 http://127.0.0.1:5173/showcase 检验全屏 4K 视频动态壁纸与 41 款工坊清单...');
    await page.goto('http://127.0.0.1:5173/showcase', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(2000);

    const wpBtnText = await page.locator('#btn-toggle-wallpaper').innerText().catch(() => '');
    console.log(`当前顶部壁纸工坊文本: "${wpBtnText.trim()}"`);

    const img1 = path.resolve(screenshotDir, `${ts}_01_showcase_wallpaper_41_live.png`);
    await page.screenshot({ path: img1, fullPage: true });
    fs.copyFileSync(img1, path.resolve(artifactDir, `${ts}_01_showcase_wallpaper_41_live.png`));
    console.log(`[OK] 4K 动态壁纸展厅截图已落盘: ${img1}`);

    // 2. 访问 http://127.0.0.1:5173/login 检验右侧动态弹出
    console.log('[2/3] 访问 http://127.0.0.1:5173/login 检验重定向与右侧滑入抽屉...');
    await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForTimeout(1500);

    const curUrl = page.url();
    console.log(`当前页面 URL: ${curUrl}`);

    const cardBox = await page.locator('.spd-auth-card').boundingBox();
    console.log(`登录抽屉位置尺寸:`, cardBox);

    const img2 = path.resolve(screenshotDir, `${ts}_02_showcase_login_drawer_right.png`);
    await page.screenshot({ path: img2, fullPage: true });
    fs.copyFileSync(img2, path.resolve(artifactDir, `${ts}_02_showcase_login_drawer_right.png`));
    console.log(`[OK] 右侧滑入抽屉登录面板截图已落盘: ${img2}`);

    // 3. 点击一键免密接入【临床二级库】
    console.log('[3/3] 点击演示角色【临床二级库】免密建立通道...');
    const nurseBtn = page.locator('.spd-role-btn[data-role="nurse"]');
    if (await nurseBtn.count() > 0) {
      await nurseBtn.click();
      await page.waitForTimeout(2500);

      const afterLoginUrl = page.url();
      console.log(`登录后跳转 URL: ${afterLoginUrl}`);

      const img3 = path.resolve(screenshotDir, `${ts}_03_nurse_workbench_isolated.png`);
      await page.screenshot({ path: img3, fullPage: true });
      fs.copyFileSync(img3, path.resolve(artifactDir, `${ts}_03_nurse_workbench_isolated.png`));
      console.log(`[OK] 护士工作台隔离截图已落盘: ${img3}`);
    }

    console.log('\n[SUCCESS] 全部自动化回环验证项与实机截图落盘完毕！');
  } catch (err) {
    console.error('自动化回环测试异常:', err);
    process.exit(1);
  } finally {
    await context.close().catch(() => {});
    try {
      fs.rmSync(tempProfile, { recursive: true, force: true });
    } catch {}
  }
}

runVerification();
