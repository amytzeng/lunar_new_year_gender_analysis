from openai import OpenAI
import os
from collections import defaultdict
import time

# 初始化 OpenAI 客戶端
client = OpenAI(api_key="key")

# 單篇分類函式（這裡不用批次，因為是重跑 error）
def classify_text(post_id, text):
    system_prompt = """你是一個文字分類助手。
請依照以下規則判斷這段文字的情緒分類，僅輸出數字：
1 - 正面、贊成
2 - 中性、問問題
3 - 無奈、抱怨
4 - 生氣、負面
5 - 無關（如廣告）
只回傳數字，不要有其他內容。"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text[:800]}  # 限制長度避免太長
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()

# 讀取原分類檔案
classified_file = "classified_posts.txt"
classified_groups = defaultdict(list)

with open(classified_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if not parts:
            continue
        label = parts[0]
        ids = parts[1:]
        for pid in ids:
            classified_groups[label].append(pid)

# 找出 error 的文章
error_ids = classified_groups.get("error", [])

if not error_ids:
    print("沒有 error 的資料需要重新判斷。")
else:
    print(f"發現 {len(error_ids)} 篇 error 資料，重新進行判斷...")

    # 移除舊的 error
    classified_groups.pop("error", None)

    disputed_cases = []  # 存放重新判斷後還是失敗的篇章

    # 逐篇重新判斷
    for idx, post_id in enumerate(error_ids, 1):
        file_path = os.path.join("data", f"{post_id}.txt")
        if not os.path.exists(file_path):
            print(f"⚠️ 找不到檔案: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        try:
            label = classify_text(post_id, text)
            if label not in {"1", "2", "3", "4", "5"}:
                label = "需要人工判斷"
        except Exception as e:
            print(f"Error on {post_id}: {e}")
            label = "需要人工判斷"

        if label == "需要人工判斷":
            disputed_cases.append({
                "id": post_id,
                "text": text[:50]  # 只存前 50 字方便人工檢查
            })
        else:
            classified_groups[label].append(post_id)

        if idx % 5 == 0 or idx == len(error_ids):
            print(f"進度: {idx}/{len(error_ids)}")

    # --- 輸出需要人工判斷的篇章 ---
    if disputed_cases:
        with open("disputed_cases_retry.txt", "w", encoding="utf-8") as f:
            for case in disputed_cases:
                f.write(f"編號: {case['id']} | 內文前50字: {case['text']}\n")
        print(f"\n⚠️ 仍有 {len(disputed_cases)} 篇需要人工判斷，已存成 disputed_cases_retry.txt")

# --- 重新輸出分類結果 ---
with open("classified_posts.txt", "w", encoding="utf-8") as f:
    for label in sorted(classified_groups.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        ids = " ".join(classified_groups[label])
        f.write(f"{label} {ids}\n")

print("\n✅ error 重新判斷完成，classified_posts.txt 已更新。")
