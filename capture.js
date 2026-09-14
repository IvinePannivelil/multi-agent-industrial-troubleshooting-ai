const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const outDir = path.join(__dirname, 'screenshots');
if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
}
const apps = [
    { name: 'goose-mart', port: 3000 },
    { name: 'goose-digital', port: 3001 },
    { name: 'goose-elevate', port: 3002 },
    { name: 'hire-my-engineer', port: 3003 },
    { name: 'portal', port: 3004 }
];

async function capture() {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    for (const app of apps) {
        try {
            console.log(`Navigating to ${app.name} on port ${app.port}...`);
            await page.goto(`http://localhost:${app.port}`, { waitUntil: 'networkidle2', timeout: 15000 });
            // wait a bit for any client side rendering
            await new Promise(r => setTimeout(r, 2000));
            const outPath = path.join(outDir, `${app.name}.png`);
            await page.screenshot({ path: outPath, fullPage: true });
            console.log(`Saved screenshot for ${app.name} at ${outPath}`);
        } catch (err) {
            console.error(`Failed to capture ${app.name}:`, err.message);
        }
    }

    await browser.close();
}

capture().catch(console.error);
