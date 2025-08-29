from openai import OpenAI
import os
from collections import Counter, defaultdict
import time

# 初始化 OpenAI 客戶端
client = OpenAI(api_key="key")

# 批次大小
BATCH_SIZE = 5

# 定義批次分類
def classify_batch(batch):
    """
    batch: list of (post_id, text)
    return: dict {post_id: label}
    """
    system_prompt = """你是一個文字分類助手。
請依照以下規則判斷每段文字的情緒分類，僅輸出編號與對應數字，格式為「編號: 分類」。
分類規則：
1 - 正面、贊成
2 - 中性、問問題
3 - 無奈、抱怨
4 - 生氣、負面
5 - 無關（如廣告）
只回傳分類結果，不要有解釋。"""

    # 拼接使用者輸入
    user_prompt = "以下是多篇文章，請依規則輸出分類：\n\n"
    for post_id, text in batch:
        snippet = text[:500]  # 避免太長
        user_prompt += f"{post_id}: {snippet}\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    output = response.choices[0].message.content.strip()
    results = {}
    for line in output.split("\n"):
        line = line.strip()
        if ":" in line:
            try:
                pid, label = line.split(":")
                results[pid.strip()] = label.strip()
            except:
                continue
    return results

# 多數決分類（整批）
def classify_batch_with_majority(batch, trials=3):
    """
    batch: list of (post_id, text)
    return: dict {post_id: (final_label, [trial_results])}
    """
    all_results = []
    for _ in range(trials):
        res = classify_batch(batch)
        all_results.append(res)
        time.sleep(0.5)

    results_dict = {}
    for post_id, _ in batch:
        votes = [res.get(post_id, "error") for res in all_results]
        counter = Counter(votes)
        most_common = counter.most_common()
        if len(most_common) == 1:
            results_dict[post_id] = (most_common[0][0], votes)
        elif most_common[0][1] > most_common[1][1]:
            results_dict[post_id] = (most_common[0][0], votes)
        else:
            results_dict[post_id] = ("需要人工判斷", votes)
    return results_dict

# 讀取 data 資料夾
data_dir = "data"
files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]

classified_groups = defaultdict(list)
disputed_cases = []

# 總數
total_files = len(files)
processed = 0

for i in range(0, total_files, BATCH_SIZE):
    batch_files = files[i:i+BATCH_SIZE]
    batch_data = []
    for fname in batch_files:
        post_id = os.path.splitext(fname)[0]
        with open(os.path.join(data_dir, fname), "r", encoding="utf-8") as f:
            text = f.read().strip()
        batch_data.append((post_id, text))

    batch_results = classify_batch_with_majority(batch_data)

    for post_id, (label, votes) in batch_results.items():
        if label == "需要人工判斷":
            disputed_cases.append({"id": post_id, "results": votes, "text": batch_data[0][1][:50]})
        else:
            classified_groups[label].append(post_id)

    processed += len(batch_data)
    if processed % 10 == 0 or processed == total_files:
        percent = processed / total_files * 100
        print(f"進度: {processed}/{total_files} ({percent:.2f}%)")

# --- 輸出分類結果 ---
with open("classified_posts.txt", "w", encoding="utf-8") as f:
    for label in sorted(classified_groups.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        ids = " ".join(classified_groups[label])
        f.write(f"{label} {ids}\n")

# --- 輸出需要人工判斷 ---
with open("disputed_cases.txt", "w", encoding="utf-8") as f:
    for case in disputed_cases:
        f.write(f"編號: {case['id']} | 判斷結果: {case['results']} | 內文前50字: {case['text']}\n")

# --- 統計比例 ---
total = sum(len(v) for v in classified_groups.values())
print("\n分類統計：")
for label in sorted(classified_groups.keys(), key=lambda x: int(x) if x.isdigit() else 999):
    count = len(classified_groups[label])
    ratio = count / total * 100 if total > 0 else 0
    print(f"類別 {label}: {count} 篇 ({ratio:.2f}%)")

print(f"\n需要人工判斷: {len(disputed_cases)} 篇，已存成 disputed_cases.txt")
print("分類完成，結果存成 classified_posts.txt")
