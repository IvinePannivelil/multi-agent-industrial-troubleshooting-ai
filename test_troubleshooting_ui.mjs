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
        await page.setViewport({ width: 1280, height: 900 });

        console.log("Navigating to Portal...");
        await page.goto('http://localhost:3004', { waitUntil: 'networkidle2' });
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        console.log("Waiting for app to load...");
        await page.waitForSelector('button');
        
        // click New Chat to be safe
        await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const newChat = buttons.find(b => b.innerText.includes('New Chat'));
            if (newChat) newChat.click();
        });
        await new Promise(r => setTimeout(r, 2000));

        console.log("Waiting for chat input...");
        await page.waitForSelector('textarea');
        
        console.log("Sending initial message...");
        await page.type('textarea', 'pasteurizer not heating');
        await page.keyboard.press('Enter');

        // wait for agent to ask clarifying question
        await new Promise(r => setTimeout(r, 6000));

        console.log("Sending 'no' to trigger RESOLVED state...");
        await page.type('textarea', 'no');
        await page.keyboard.press('Enter');

        // wait for agent to generate resolution with media
        await new Promise(r => setTimeout(r, 25000));

        // Scroll the chat container to the bottom
        await page.evaluate(() => {
            const chatContainer = document.querySelector('.overflow-y-auto');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            } else {
                window.scrollTo(0, document.body.scrollHeight);
            }
        });
        await new Promise(r => setTimeout(r, 2000));

        const screenshotPath = path.join(outDir, 'troubleshooting_result.png');
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log("Screenshot Saved to " + screenshotPath);

        await browser.close();
        console.log("Visual test complete!");
    } catch (e) {
        console.error("Test failed", e);
        process.exit(1);
    }
})();
