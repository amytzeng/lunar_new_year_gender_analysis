import os

# 讀取分類檔案
classified_file = "classified_posts.txt"
counts = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

with open(classified_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if not parts:
            continue
        label = parts[0]
        ids = parts[1:]
        if label in counts:
            counts[label] += len(ids)

total = sum(counts.values())

# 分類對應說明
label_map = {
    "1": "正面、贊成",
    "2": "中性、問問題",
    "3": "無奈、抱怨",
    "4": "生氣、負面",
    "5": "無關（如廣告）"
}

# 輸出結果
with open("result.txt", "w", encoding="utf-8") as f:
    for label in ["1", "2", "3", "4", "5"]:
        count = counts[label]
        ratio = (count / total * 100) if total > 0 else 0
        f.write(f"{label} - {label_map[label]}：{count} 篇、{ratio:.2f} %\n")
    f.write(f"總貼文數：{total}\n")

print("✅ 統計完成，結果已存成 result.txt")
