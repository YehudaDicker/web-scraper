import csv
import time
import re
from urllib.parse import urljoin
import hashlib, os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

START_URL = "https://www.net32.com/ec/dental-supplies"

def create_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--blink-settings=imagesEnabled=false")  # disables images
    driver = uc.Chrome(options=options)
    return driver

def get_category_links(driver):
    driver.get(START_URL)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "aside#top-categories ol li a[href^='/ec/']"))
    )
    anchors = driver.find_elements(By.CSS_SELECTOR, "aside#top-categories ol li a[href^='/ec/']")
    links = sorted({urljoin(START_URL, a.get_attribute("href")) for a in anchors})
    return links

def scrape_category(driver, category_url):
    driver.get(category_url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "ol.ais-Hits-list > li.ais-Hits-item"))
    )

    items = []
    page = 0
    seen = set()
    while True:
        tiles = driver.find_elements(By.CSS_SELECTOR, "ol.ais-Hits-list > li.ais-Hits-item")
        if not tiles:
            break
        for tile in tiles:
            try:
                name = tile.find_element(By.CSS_SELECTOR, "a#product-description").text.strip()
                price = tile.find_element(By.CSS_SELECTOR, "span.productsGrid_price__cUEKu").text.strip()
                url = tile.find_element(By.CSS_SELECTOR, "a#product-description").get_attribute("href")

                try:
                    desc = tile.find_element(By.CSS_SELECTOR, "p.productsGrid_packagingInfo__kZntF").text.strip()
                except:
                    desc = ""

                key = (name, url, price)
                if key in seen:
                    print(f"[DUPLICATE SKIPPED] {key}")
                    continue
                seen.add(key)

                items.append({
                    "Category": category_url,
                    "Name": name,
                    "Price": price,
                    "Description": desc,
                    "URL": url
                })
            except Exception as e:
                print("Skipped product due to error:", e)
                continue

        try:
            current_page_number = page + 1
            next_button = driver.find_element(By.CSS_SELECTOR, ".ais-Pagination-item--selected + li a")
            driver.execute_script("arguments[0].click();", next_button)
            WebDriverWait(driver, 10).until(
                lambda d: str(current_page_number + 1) in d.page_source
            )
        except Exception as e:
            print(f"Pagination ended or failed: {e}")
            break

        page += 1

    return items


def main():
    all_products = []
    cats = get_category_links(create_driver())[30:41]  # temp driver just to get category links

    for c in cats:
        print(f"Scraping: {c}")
        driver = create_driver()
        try:
            all_products += scrape_category(driver, c)
        except Exception as e:
            print(f"Failed to scrape category {c}: {e}")
        finally:
            driver.quit()

    keys = ["Category", "Name", "Price", "Description", "URL"]
    with open("net32_products_4.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_products)

    print(f"Done! {len(all_products)} rows")
    
if __name__ == "__main__":
    main()