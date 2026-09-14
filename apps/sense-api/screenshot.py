from playwright.sync_api import sync_playwright
import time
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:3004')
    print("Page loaded")
    time.sleep(3) # Let React fully hydrate
    
    # This phrase has "fault" keyword to force TROUBLESHOOTING intent in the classifier
    # AND "TEST UI RENDER" to trigger the agent's hardcoded bypass
    page.click('textarea[placeholder="Ask Goose Sense..."]')
    page.keyboard.type('fault error TEST UI RENDER')
    page.keyboard.press('Enter')
    print("Test trigger sent")
    
    time.sleep(12) # Wait for response
    
    # Take screenshot of the entire page
    screenshot_path = os.path.join(os.getcwd(), 'frontend_media_verification_final.png')
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot saved to {screenshot_path}")
    browser.close()
