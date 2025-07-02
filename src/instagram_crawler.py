# coding: utf-8
import os
import csv
import sys
import time
import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Instagram 爬蟲主類別
class InstagramCrawler:
    def __init__(self, username, password, driver_path, keywords):
        self.username = username
        self.password = password
        self.driver_path = driver_path
        self.driver = None
        self.keywords = keywords
        self.post_count = 0
        self.comment_count = 0
        self.results = []

        # 儲存資料夾初始化
        self.base_dir = os.path.join("data", "instagram")
        self.post_dir = os.path.join(self.base_dir, "post")
        self.comment_dir = os.path.join(self.base_dir, "comment")
        os.makedirs(self.post_dir, exist_ok=True)
        os.makedirs(self.comment_dir, exist_ok=True)

    # 啟動瀏覽器
    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=Service(self.driver_path), options=options)

    # 登入 Instagram
    def login(self):
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)
        username_input = self.driver.find_element(By.NAME, "username")
        password_input = self.driver.find_element(By.NAME, "password")
        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        self.driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[3]/button').click()
        time.sleep(5)  # 等待登入

    # 取得貼文內容與留言
    def scrape_post(self, url, post_id):
        try:
            self.driver.get(url)
            time.sleep(5)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # 擷取貼文標題
            try:
                title = soup.find("meta", property="og:title")["content"]
            except:
                title = ""

            # 擷取留言元素（需要等待載入）
            self.scroll_comments()
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            comment_elements = soup.find_all("span", class_=lambda x: x and "x1lliihq" in x)
            comments = [c.text for c in comment_elements]

            # 檢查是否包含關鍵字
            content_all = title + " " + " ".join(comments)
            if not any(k in content_all for k in self.keywords):
                return  # 跳過此篇

            # 儲存貼文
            post_path = os.path.join(self.post_dir, f"{post_id}.txt")
            with open(post_path, "w", encoding="utf-8") as f:
                f.write(title)

            # 儲存留言
            saved_comments = 0
            for i, comment in enumerate(comments):
                if any(k in comment for k in self.keywords):
                    comment_id = self.comment_count + 1
                    comment_path = os.path.join(
                        self.comment_dir, f"post_{post_id}_comment_{comment_id}.txt")
                    with open(comment_path, "w", encoding="utf-8") as f:
                        f.write(comment)
                    self.comment_count += 1
                    saved_comments += 1

            # 收集資訊至 csv
            self.results.append({
                "id": post_id,
                "platform": "instagram",
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "title": title,
                "like_count": None,
                "comment_count": saved_comments,
                "reach": None,
                "keywords": ",".join([k for k in self.keywords if k in content_all])
            })

            print(f"✅已處理第 {post_id}/100 篇：{title[:20]}...")
            self.post_count += 1
        except Exception as e:
            print(f"❌ 錯誤發生於第 {post_id} 篇：{e}")

    # 模擬滾動載入所有留言
    def scroll_comments(self, max_scrolls=5):
        try:
            scroll_area = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.x5yr21d"))
            )
        except TimeoutException:
            return

        for _ in range(max_scrolls):
            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", scroll_area)
            time.sleep(2)

    # 儲存最終 csv 結果
    def save_csv(self):
        csv_path = os.path.join(self.base_dir, "instagram.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "id", "platform", "date", "title",
                "like_count", "comment_count", "reach", "keywords"
            ])
            writer.writeheader()
            writer.writerows(self.results)
        print(f"[Instagram] 已儲存至 {csv_path}，共 {len(self.results)} 筆資料")

    # 關閉瀏覽器
    def close(self):
        if self.driver:
            self.driver.quit()

def run_instagram(keywords):
    from getpass import getpass

    # ❗ 可自行改為從設定檔或環境變數讀取
    username = input("請輸入 Instagram 帳號：")
    password = getpass("請輸入 Instagram 密碼：")  # 安全起見用 getpass 隱藏輸入
    driver_path = "/usr/local/bin/chromedriver"  # 修改為你本機路徑

    # 讀網址列表
    urls_path = os.path.join(os.path.dirname(__file__), "../urls.txt")
    with open(urls_path, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    crawler = InstagramCrawler(username, password, driver_path, keywords)
    crawler.initialize_driver()
    crawler.login()

    for i, url in enumerate(urls[:100]):
        crawler.scrape_post(url, i + 1)

    crawler.save_csv()
    crawler.close()


# 主程式
if __name__ == "__main__":
    # Instagram 帳號登入資訊
    INSTAGRAM_USERNAME = "your_username"   # 👈 在這裡填帳號
    INSTAGRAM_PASSWORD = "your_password"   # 👈 在這裡填密碼
    CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"  # 👈 依環境調整路徑

    keywords = ["回娘家", "煮年夜飯", "婆媳關係"]

    # 讀取網址
    with open("urls.txt", "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    crawler = InstagramCrawler(
        INSTAGRAM_USERNAME,
        INSTAGRAM_PASSWORD,
        CHROME_DRIVER_PATH,
        keywords
    )

    crawler.initialize_driver()
    crawler.login()

    # 顯示 tqdm 進度條
    print(f"[Instagram] 關鍵字：{'、'.join(keywords)}")
    for i, url in enumerate(tqdm(urls[:100], desc=f"處理關鍵字：{'、'.join(keywords)}")):
        crawler.scrape_post(url, i + 1)  # post_id 從 1 開始

    crawler.save_csv()
    crawler.close()
