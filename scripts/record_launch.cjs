// Record the actual local application; no injected scene or mocked responses.
const { chromium } = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');

async function main() {
  const output = path.resolve(process.argv[2] || 'artifacts/launch');
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  try {
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: { dir: path.join(output, 'recordings'), size: { width: 1920, height: 1080 } },
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5174');
  await page.getByRole('button', { name: '全屏预览', exact: true }).waitFor();
  await page.waitForFunction(() => document.querySelector('.asset-stats')?.textContent.includes('12'));
  await page.locator('.preview-message').waitFor({ state: 'hidden' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(output, 'desktop.png') });
  await page.getByRole('button', { name: '全屏预览', exact: true }).click();
  await page.locator('.preview-message').waitFor({ state: 'hidden' });
  await page.waitForTimeout(1800);
  const canvas = page.locator('.mesh-preview canvas');
  const box = await canvas.boundingBox();
  const before = await page.screenshot({ clip: box });
  await page.screenshot({ path: path.join(output, 'scene.png') });
  for (let pass = 0; pass < 2; pass += 1) {
    await page.mouse.move(box.x + box.width * 0.60, box.y + box.height * 0.55);
    await page.mouse.down();
    for (let step = 0; step < 45; step += 1) {
      await page.mouse.move(box.x + box.width * (0.60 - step * 0.0015), box.y + box.height * 0.55);
      await page.waitForTimeout(35);
    }
    await page.mouse.up();
  }
  const after = await page.screenshot({ clip: box });
  if (before.equals(after)) throw new Error('3D viewport did not respond to orbit input');
  await page.getByRole('button', { name: '退出全屏', exact: true }).click();
  await page.getByRole('button', { name: '验证', exact: true }).click();
  await page.waitForTimeout(500);
  await page.locator('.panel').filter({ has: page.getByRole('button', { name: '验证', exact: true }) })
    .screenshot({ path: path.join(output, 'validation.png') });
  await fs.writeFile(path.join(output, 'browser-evidence.json'), JSON.stringify({
    pageErrors: errors, orbitFramesDiffer: true, viewport: { width: 1920, height: 1080 },
  }, null, 2));
  if (errors.length) throw new Error(errors.join('\n'));
  const video = page.video();
  await page.goto('about:blank');
  await page.close();
  await context.close();
  await video.saveAs(path.join(output, 'desktop-recording.webm'));
  console.log('Recorded real UI and orbit interaction:', output);
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
