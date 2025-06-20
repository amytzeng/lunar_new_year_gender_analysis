import requests
import os
import json
from tqdm import tqdm
import pandas as pd

DATA_DIR = "data"
POST_DIR = os.path.join(DATA_DIR, "posts")
COMMENT_DIR = os.path.join(DATA_DIR, "comments")
CSV_PATH = os.path.join(DATA_DIR, "dcard.csv")

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(COMMENT_DIR, exist_ok=True)

def fetch_dcard_posts(keyword, limit=100):
    url = f"https://www.dcard.tw/service/api/v2/search/posts?query={keyword}&limit={limit}"
    res = requests.get(url)
    return res.json()

def fetch_dcard_comments(post_id):
    url = f"https://www.dcard.tw/service/api/v2/posts/{post_id}/comments"
    res = requests.get(url)
    return res.json()

def save_txt(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def run_dcard(start_year, end_year, keywords):
    df_rows = []
    for kw in keywords:
        print(f"[Dcard] 關鍵字：{kw}")
        posts = fetch_dcard_posts(kw)
        for post in tqdm(posts[:100]):
            post_id = post['id']
            title = post['title']
            content = post['excerpt']
            created_at = post['createdAt']
            like_count = post['likeCount']
            comment_count = post['commentCount']
            full_text = f"{title}\n\n{content}"

            # Save post
            post_path = os.path.join(POST_DIR, f"post_{post_id}.txt")
            save_txt(post_path, full_text)

            # Save comments
            comments = fetch_dcard_comments(post_id)
            for idx, comment in enumerate(comments):
                comment_txt = comment.get("content", "")
                comment_path = os.path.join(COMMENT_DIR, f"post_{post_id}_comment_{idx}.txt")
                save_txt(comment_path, comment_txt)

            df_rows.append({
                "post_id": post_id,
                "發文時間": created_at,
                "觸及率": "N/A",
                "點讚數": like_count,
                "留言數": comment_count,
                "關鍵字": kw
            })

    df = pd.DataFrame(df_rows)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[Dcard] 已儲存至 {CSV_PATH}")
