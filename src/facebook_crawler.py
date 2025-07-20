# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime, timedelta
from tqdm import tqdm
import csv
from seleniumwire import webdriver
from fb_graphql_scraper.facebook_graphql_scraper import FacebookGraphqlScraper

# =======================
# ⚙️ 設定區：使用者需修改
# =======================
DRIVER_PATH = "/path/to/chromedriver"  # ← 你的 ChromeDriver 路徑
FB_USERNAME = None  # ← 若需登入帳號則填入帳號
FB_PASSWORD = None  # ← 若需登入帳號則填入密碼
TARGET_USER = "nintendo"  # ← 目標粉專 ID 或用戶名
KEYWORDS = ["年夜飯", "圍爐", "春節"]  # ← 關鍵字列表
MAX_POSTS = 100  # ← 要爬的貼文數量
DAYS_LIMIT = 30  # ← 幾天內的貼文

# =======================
# 📁 資料夾初始化
# =======================
POST_DIR = "data/facebook/post"
COMMENT_DIR = "data/facebook/comment"
CSV_PATH = "data/instagram/instagram.csv"
os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(COMMENT_DIR, exist_ok=True)
os.makedirs("data/instagram", exist_ok=True)

# =======================
# 🚀 啟動 Chrome Driver
# =======================
driver = webdriver.Chrome(executable_path=DRIVER_PATH)
scraper = FacebookGraphqlScraper(driver_path=DRIVER_PATH)

# =======================
# 🕒 爬取貼文資料
# =======================
print(f"[Instagram] 關鍵字：{'、'.join(KEYWORDS)}")

try:
    results = scraper.get_user_posts(
        fb_username_or_userid=TARGET_USER,
        loop_times=MAX_POSTS,
        username_or_userid=FB_USERNAME,
        pwd=FB_PASSWORD,
        days_limit=DAYS_LIMIT,
        display_progress=False
    )
except Exception as e:
    print(f"❌ 爬取錯誤：{e}")
    driver.quit()
    exit(1)

# =======================
# 📦 過濾並儲存資料
# =======================
filtered_posts = []
progress = tqdm(results[:MAX_POSTS], desc=f"處理關鍵字：{KEYWORDS[0]}", ncols=100)

for idx, post in enumerate(progress, start=1):
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
            "platform": "instagram",
            "date": created_time,
            "title": title,
            "like_count": like_count,
            "comment_count": comment_count,
            "reach": reach,
            "keywords": ",".join([kw for kw in KEYWORDS if kw in text])
        })

        print(f"\n✅已處理第 {idx}/{MAX_POSTS} 篇：{title}")

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

print(f"\n[Instagram] 已儲存至 {CSV_PATH}，共 {len(filtered_posts)} 筆資料")

# =======================
# ✅ 關閉瀏覽器
# =======================
driver.quit()
