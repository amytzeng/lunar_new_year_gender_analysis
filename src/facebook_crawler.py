# -*- coding: utf-8 -*-
import os
import csv
from datetime import datetime
from tqdm import tqdm
from facebook_scraper import get_posts, set_cookies, get_profile

# ====================
# ⚙️ 設定區
# ====================
COOKIES_FILE = "cookies.txt"
TARGET_USERS = [
    "coobepowtf",                 # 但此粉專可能沒有公開貼文
    "100084717466395",           # 靠北婚姻 的粉專數字 ID
    "coobehaspon"                # 正確的粉專 ID，不包含參數
]
KEYWORDS = ["年夜飯", "圍爐", "春節", "娘家", "婆媳"]
MAX_POSTS_PER_USER = 100
PAGES_PER_USER = 30  # 每個粉專最多看幾頁

# ====================
# 📁 初始化資料夾
# ====================
BASE_DIR = "data/facebook"
POST_DIR = f"{BASE_DIR}/post"
COMMENT_DIR = f"{BASE_DIR}/comment"
CSV_PATH = f"{BASE_DIR}/facebook.csv"
os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(COMMENT_DIR, exist_ok=True)

# ====================
# 🔐 設定 Cookie
# ====================
try:
    set_cookies(COOKIES_FILE)
    print("✅ Cookies 載入成功")
except Exception as e:
    print(f"❌ Cookies 載入失敗：{e}")
    exit(1)

# ====================
# 🚀 開始爬取
# ====================
all_filtered_posts = []

for user in TARGET_USERS:
    print(f"\n🔍 開始處理粉專：{user}")

    try:
        profile = get_profile(user)
        if not profile:
            print(f"⚠️ 無法存取 {user}，可能 cookies 失效或粉專不存在")
            continue
        print(f"📘 粉專名稱：{profile.get('Name', user)}")

        user_posts = []
        for post in get_posts(user, pages=PAGES_PER_USER, options={"comments": True}):
            user_posts.append(post)
            if len(user_posts) >= MAX_POSTS_PER_USER:
                break

        print(f"✅ 共取得 {len(user_posts)} 篇貼文")

        # 🧹 處理與儲存
        for idx, post in enumerate(tqdm(user_posts, desc="處理貼文")):
            try:
                text = post.get("text", "")
                if not text:
                    continue

                post_id = post.get("post_id") or f"{user}_{idx}"
                title = text.strip().split("\n")[0][:50]
                created_time = post.get("time")
                created_time = created_time.isoformat() if isinstance(created_time, datetime) else datetime.now().isoformat()
                like_count = post.get("likes", 0)
                comment_count = len(post.get("comments", []))
                reach = post.get("shares", 0)

                # 儲存貼文文字
                with open(f"{POST_DIR}/{post_id}.txt", "w", encoding="utf-8") as f:
                    f.write(text)

                # 儲存留言
                for i, comment in enumerate(post.get("comments", [])):
                    comment_text = comment.get("comment_text", "")
                    fname = f"post_{post_id}_comment_{i}.txt"
                    with open(f"{COMMENT_DIR}/{fname}", "w", encoding="utf-8") as f:
                        f.write(comment_text)

                # 儲存資訊到 CSV 列表
                all_filtered_posts.append({
                    "id": post_id,
                    "platform": "facebook",
                    "user": user,
                    "date": created_time,
                    "title": title,
                    "like_count": like_count,
                    "comment_count": comment_count,
                    "reach": reach,
                    "keywords": ",".join([kw for kw in KEYWORDS if kw in text])
                })

            except Exception as e:
                print(f"⚠️ 發生錯誤：{e}")
                continue

    except Exception as e:
        print(f"❌ 無法處理 {user}：{e}")
        continue

# ====================
# 🧾 儲存 CSV
# ====================
if all_filtered_posts:
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["id", "platform", "user", "date", "title", "like_count", "comment_count", "reach", "keywords"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_filtered_posts)

    print(f"\n📁 已儲存 {len(all_filtered_posts)} 筆貼文資料到 {CSV_PATH}")
else:
    print("\n⚠️ 沒有抓到任何貼文")

# ====================
# ✅ 封裝主函式
# ====================
def run_facebook():
    os.system("python src/facebook_crawler.py")
