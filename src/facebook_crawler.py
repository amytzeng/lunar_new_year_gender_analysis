# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
from tqdm import tqdm
import csv
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from fb_graphql_scraper.facebook_graphql_scraper import FacebookGraphqlScraper
from facebook_scraper import get_posts

# =======================
# ⚙️ 設定區：使用者需修改
# =======================
DRIVER_PATH = r"C:\Users\Amy\Desktop\Uni\chromedriver-win64\chromedriver.exe"  # ← 你的 ChromeDriver 路徑
FB_USERNAME = "textmining714"  # ← 若需登入帳號則填入帳號（此 scraper 不支援登入，僅預留）
FB_PASSWORD = "txtmining7144"  # ← 若需登入帳號則填入密碼（此 scraper 不支援登入，僅預留）
TARGET_USER = "coobepowtf"  # ← 目標粉專 ID 或用戶名
KEYWORDS = ["年夜飯", "圍爐", "春節", "娘家", "婆媳"]  # ← 關鍵字列表
MAX_POSTS = 100  # ← 要爬的貼文數量
DAYS_LIMIT = 1000  # ← 幾天內的貼文

# =======================
# 📁 資料夾初始化
# =======================
POST_DIR = "data/facebook/post"
COMMENT_DIR = "data/facebook/comment"
CSV_PATH = "data/facebook/facebook.csv"
os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(COMMENT_DIR, exist_ok=True)
os.makedirs("data/facebook", exist_ok=True)

# =======================
# 🚀 啟動 Chrome Driver
# =======================
driver = webdriver.Chrome(service=Service(DRIVER_PATH))
scraper = FacebookGraphqlScraper(driver_path=DRIVER_PATH)

# =======================
# 🕒 爬取貼文資料
# =======================

print(f"[Facebook] 正在抓取粉專：{TARGET_USER}")
all_posts = []
try:
    for post in get_posts(TARGET_USER, pages=20, options={"comments": True}):
        all_posts.append(post)
except Exception as e:
    print(f"❌ 爬取失敗：{e}")
    driver.quit()
    exit(1)

# =======================
# 📦 過濾並儲存資料
# =======================
filtered_posts = []
count = 0
progress = tqdm(all_posts, desc=f"處理關鍵字：{KEYWORDS[0]}", ncols=100)

for idx, post in enumerate(progress, start=1):
    if count >= MAX_POSTS:
        break

    try:
        text = post.get("text", "")
        if not any(kw in text for kw in KEYWORDS):
            continue

        post_id = post.get("post_id") or post.get("id") or f"noid_{idx}"
        title = text.strip().split("\n")[0][:50]
        created_time = datetime.fromtimestamp(post.get("time", time.time())).isoformat()
        like_count = post.get("likes", 0)
        comment_count = len(post.get("comments", []))
        reach = post.get("share_count", 0)

        # 儲存貼文
        with open(f"{POST_DIR}/{post_id}.txt", "w", encoding="utf-8") as f:
            f.write(text)

        # 儲存留言
        for comment in post.get("comments", []):
            comment_id = comment.get("comment_id") or comment.get("id") or "nocid"
            comment_text = comment.get("text", "")
            fname = f"post_{post_id}_comment_{comment_id}.txt"
            with open(f"{COMMENT_DIR}/{fname}", "w", encoding="utf-8") as f:
                f.write(comment_text)

        # 收集資料供 CSV 使用
        filtered_posts.append({
            "id": post_id,
            "platform": "facebook",
            "date": created_time,
            "title": title,
            "like_count": like_count,
            "comment_count": comment_count,
            "reach": reach,
            "keywords": ",".join([kw for kw in KEYWORDS if kw in text])
        })

        count += 1
        print(f"\n✅已處理第 {count}/{MAX_POSTS} 篇：{title}")

    except Exception as e:
        print(f"⚠️ 發生錯誤，略過此篇：{e}")
        continue

# =======================
# 🧾 儲存 CSV 統整資料
# =======================
with open(CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["id", "platform", "date", "title", "like_count", "comment_count", "reach", "keywords"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(filtered_posts)

print(f"\n[Facebook] 已儲存至 {CSV_PATH}，共 {len(filtered_posts)} 筆資料")

# =======================
# ✅ 關閉瀏覽器
# =======================
driver.quit()

# =======================
# 📞 封裝成主流程函式
# =======================
def run_facebook():
    os.system("python src/facebook_crawler.py")
