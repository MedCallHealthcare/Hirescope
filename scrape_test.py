from playwright.sync_api import sync_playwright

url = "https://sports.yahoo.com/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)

    page.wait_for_load_state("networkidle")

    games = page.locator("._ys_6mtdyh")

    for i in range(games.count()):
        print(games.nth(i).inner_text())

    browser.close()