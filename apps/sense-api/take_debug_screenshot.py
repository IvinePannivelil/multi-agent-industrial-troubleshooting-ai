from playwright.sync_api import sync_playwright
import time
import os

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://localhost:3004')
    time.sleep(5)
    screenshot_path = os.path.join(os.getcwd(), 'debug_ui_state.png')
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot saved to {screenshot_path}")
    browser.close()
