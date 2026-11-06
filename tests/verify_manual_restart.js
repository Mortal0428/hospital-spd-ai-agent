const { launchPersistentPlaywright } = require('./e2e/browser_config');
const path = require('path');

async function testReboot() {
  const { context, page } = await launchPersistentPlaywright({ headless: true });
  const interceptedErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const t = msg.text();
      if (!t.includes('favicon') && !t.includes('chrome-extension')) {
        interceptedErrors.push(t);
      }
    }
  });

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/showcase?login=1');
  await page.waitForTimeout(1000);
  const adminBtn = page.locator('.spd-role-btn[data-role="admin"]');
  if ((await adminBtn.count()) > 0) {
    await adminBtn.click();
  }
  await page.waitForTimeout(1500);

  // 导航到 /rag-hub 并停留 3 秒
  await page.goto('http://127.0.0.1:5173/rag-hub');
  await page.waitForTimeout(3000);

  const screenshotPath = path.resolve('./tests/screenshots/manual_verify_reboot_success.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });

  console.log('Intercepted errors count:', interceptedErrors.length);
  if (interceptedErrors.length > 0) {
    console.log('Errors:', interceptedErrors);
  } else {
    console.log('SUCCESS: Page rendered perfectly with 0 errors!');
  }
  await context.close();
}

testReboot().catch(console.error);
