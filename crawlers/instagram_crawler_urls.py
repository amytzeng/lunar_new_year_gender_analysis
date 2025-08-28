import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup


class InstagramHashtagScraper:
    def __init__(self, username, password, driver_path):
        self.username = username
        self.password = password
        self.driver_path = driver_path
        self.driver = None
        self.base_url = "https://www.instagram.com"

    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--lang=zh-TW")
        self.driver = webdriver.Chrome(service=Service(self.driver_path), options=options)

    def login(self):
        print("\n🔐 Logging into Instagram...")
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)

        try:
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.send_keys(self.username)
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)

            login_btn = self.driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[3]/button')
            login_btn.click()
            print("✅ Login submitted.")
            time.sleep(5)
        except Exception as e:
            print("❌ Login failed:", e)

    def collect_post_urls(self, hashtag, max_posts=100):
        print(f"\n🔍 Searching for hashtag: #{hashtag}")
        search_url = f"{self.base_url}/explore/tags/{hashtag}/"
        self.driver.get(search_url)
        time.sleep(5)

        post_urls = set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempt = 0
        max_scroll_attempts = 50  # 增加滾動次數限制

        while len(post_urls) < max_posts and scroll_attempt < max_scroll_attempts:
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            links = soup.find_all("a")
            for link in links:
                href = link.get("href", "")
                if "/p/" in href:
                    full_url = self.base_url + href
                    post_urls.add(full_url)
                    if len(post_urls) >= max_posts:
                        break

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(4, 6))  # 每次滾動等 4–6 秒

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempt += 1
            else:
                scroll_attempt = 0
                last_height = new_height

            print(f"🔄 Collected {len(post_urls)} URLs... (Scroll {scroll_attempt}/{max_scroll_attempts})")

        return list(post_urls)[:max_posts]

    def save_urls(self, urls, save_path):
        with open(save_path, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
        print(f"✅ Saved {len(urls)} post URLs to: {save_path}")

    def close(self):
        if self.driver:
            self.driver.quit()


def run_hashtag_scraper(keywords, max_posts_per_keyword=100):
    from getpass import getpass
    username = input("請輸入 Instagram 帳號：")
    password = getpass("請輸入 Instagram 密碼：")
    driver_path = r"C:\Users\Amy\Desktop\Uni\chromedriver-win64\chromedriver.exe"  # ← 替換為你的 chromedriver 路徑

    scraper = InstagramHashtagScraper(username, password, driver_path)
    scraper.initialize_driver()
    scraper.login()

    os.makedirs("./_爬蟲", exist_ok=True)
    all_urls = []

    for kw in keywords:
        urls = scraper.collect_post_urls(kw, max_posts=max_posts_per_keyword)
        all_urls.extend(urls)

    # 去除重複
    all_urls = list(set(all_urls))
    scraper.save_urls(all_urls, "./_爬蟲/urls.txt")
    scraper.close()


if __name__ == "__main__":
    keywords = ["回娘家", "煮年夜飯", "婆媳關係"]
    run_hashtag_scraper(keywords, max_posts_per_keyword=100)
