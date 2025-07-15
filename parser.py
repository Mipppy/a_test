import re
import json,os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup Firefox WebDriver
options = FirefoxOptions()
options.add_argument("--width=1280")
options.add_argument("--height=800")
driver = webdriver.Firefox(service=FirefoxService(), options=options)

try:
    # Load the site
    driver.get("https://genshin-impact-map.appsample.com/")

    # Wait until the buttons are present
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid^="btn-o"]'))
    )

    # Extract data-testid and title
    pattern = re.compile(r'^btn-o\d+$')
    data = {}

    buttons = driver.find_elements(By.CSS_SELECTOR, '[data-testid^="btn-o"]')
    for btn in buttons:
        testid = btn.get_attribute("data-testid")
        if pattern.match(testid):
            title = btn.get_attribute("title") or ""
            data[testid] = title

    # Save to file
    output_path = "./data/unofficial/data_testid_title_map.json"
    os.makedirs("output", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(data)} items to {output_path}")

finally:
    driver.quit()
