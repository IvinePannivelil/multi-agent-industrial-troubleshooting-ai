import puppeteer from 'puppeteer';
import * as path from 'path';
import * as fs from 'fs';

(async () => {
    try {
        const outDir = path.join(process.cwd(), 'screenshots');
        if (!fs.existsSync(outDir)) {
            fs.mkdirSync(outDir, { recursive: true });
        }
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 800 });

        console.log("Testing Scenario 1: HireMyEngineer");
        await page.goto('http://localhost:3000');
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        await page.waitForSelector('textarea');
        await page.type('textarea', 'I need to modernize my legacy S7-300 system.');
        await page.keyboard.press('Enter');

        await new Promise(r => setTimeout(r, 6000));

        await page.type('textarea', 'We need an expert for Siemens TIA Portal next week.');
        await page.keyboard.press('Enter');

        await new Promise(r => setTimeout(r, 10000));

        await page.screenshot({ path: path.join(outDir, 'scenario1_talent.png') });
        console.log("Scenario 1 Saved");

        console.log("Testing Scenario 2: GooseMart");
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        await page.waitForSelector('textarea');
        await page.type('textarea', 'Hardware failure on line 2.');
        await page.keyboard.press('Enter');
        await new Promise(r => setTimeout(r, 6000));

        await page.type('textarea', 'We need to procure a replacement S7-1500 PLC.');
        await page.keyboard.press('Enter');
        await new Promise(r => setTimeout(r, 10000));

        await page.screenshot({ path: path.join(outDir, 'scenario2_hardware.png') });
        console.log("Scenario 2 Saved");

        console.log("Testing Scenario 3: Courses");
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        await page.waitForSelector('textarea');
        await page.type('textarea', 'We want the basic S7-1500 training course.');
        await page.keyboard.press('Enter');
        await new Promise(r => setTimeout(r, 10000));

        await page.screenshot({ path: path.join(outDir, 'scenario3_training.png') });
        console.log("Scenario 3 Saved");

        await browser.close();
        console.log("All UI tests complete!");
    } catch (e) {
        console.error("Test failed", e);
    }
})();
