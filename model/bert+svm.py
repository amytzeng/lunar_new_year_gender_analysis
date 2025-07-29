import torch
import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.metrics import classification_report, f1_score
from transformers import BertTokenizer, BertModel
from tqdm import tqdm
import os
from collections import defaultdict

# 1. 設備檢查
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"使用設備: {device}")

# 2. 載入BERT模型和分詞器
model_name = "bert-base-uncased"
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)
model.to(device)
model.eval()

# 3. 讀取已分類的標籤檔案
def load_label_file(label_file_path, text_folder):
    """
    讀取標籤檔案並返回訓練數據
    """
    # 讀取所有文本文件內容
    text_data = {}
    for file in os.listdir(text_folder):
        if file.endswith('.txt') and file != "training_label.txt":
            file_id = int(file.split('.')[0])
            with open(os.path.join(text_folder, file), 'r', encoding='utf-8') as f:
                text_data[file_id] = f.read().strip()
    
    # 讀取標籤檔案
    label_data = defaultdict(list)
    with open(label_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                class_label = int(parts[0])
                file_ids = list(map(int, parts[1:]))
                label_data[class_label].extend(file_ids)
    
    # 檢查是否所有類別都存在
    for class_label in range(1, 6):
        if class_label not in label_data:
            print(f"警告: 類別 {class_label} 在訓練數據中不存在!")
    
    # 準備訓練數據
    texts = []
    labels = []
    used_file_ids = []
    for class_label, ids in label_data.items():
        for file_id in ids:
            if file_id in text_data:
                texts.append(text_data[file_id])
                labels.append(class_label)
                used_file_ids.append(file_id)
            else:
                print(f"警告: 檔案 {file_id}.txt 在 {text_folder} 中找不到")
    
    return texts, labels, used_file_ids

# 4. 準備訓練數據
print("準備訓練數據...")
training_label_file = r"model/training/training_label.txt"
training_text_folder = r"model/training"
train_texts, train_labels, _ = load_label_file(training_label_file, training_text_folder)

# 檢查類別分佈
unique, counts = np.unique(train_labels, return_counts=True)
print("\n訓練數據類別分佈:")
for cls, cnt in zip(unique, counts):
    print(f"類別 {cls}: {cnt} 個樣本")

# 5. 提取BERT [CLS]嵌入向量
def extract_cls_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True, padding="max_length")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
    return cls_embedding

print("\n提取訓練數據的BERT嵌入向量...")
train_embeddings = []
for text in tqdm(train_texts):
    emb = extract_cls_embedding(text)
    train_embeddings.append(emb)

X_train = np.array(train_embeddings)
y_train = np.array(train_labels)

# 6. 訓練SVM分類器
print("\n訓練SVM分類器...")
svm = SVC(kernel="rbf", probability=True, class_weight='balanced')  # 添加 class_weight 處理不平衡數據
svm.fit(X_train, y_train)

# 7. 評估訓練集表現
train_preds = svm.predict(X_train)
print("\n訓練集分類報告:")
print(classification_report(y_train, train_preds))
print(f"F1分數 (加權平均): {f1_score(y_train, train_preds, average='weighted')}")

# 8. 處理待分類的數據
print("\n處理待分類數據...")
testing_text_folder = r"model/testing"

# 讀取所有待分類文本
unlabeled_texts = []
unlabeled_ids = []
for file in os.listdir(testing_text_folder):
    if file.endswith('.txt') and file != "testing_label.txt":
        file_id = int(file.split('.')[0])
        with open(os.path.join(testing_text_folder, file), 'r', encoding='utf-8') as f:
            unlabeled_texts.append(f.read().strip())
            unlabeled_ids.append(file_id)

# 提取BERT特徵
print("\n提取測試數據的BERT嵌入向量...")
test_embeddings = []
for text in tqdm(unlabeled_texts):
    emb = extract_cls_embedding(text)
    test_embeddings.append(emb)

X_test = np.array(test_embeddings)

# 9. 預測類別
print("\n進行分類預測...")
test_preds = svm.predict(X_test)

# 10. 組織預測結果
predictions = defaultdict(list)
for file_id, pred in zip(unlabeled_ids, test_preds):
    predictions[pred].append(file_id)

# 11. 輸出分類結果到 testing_label.txt
output_file = r"model/testing/testing_label.txt"
print(f"\n將分類結果保存到 {output_file}...")

# 確保所有5個類別都會出現在輸出檔案中
with open(output_file, 'w', encoding='utf-8') as f:
    for class_label in range(1, 6):  # 強制輸出1-5類
        # 排序檔案ID
        sorted_ids = sorted(predictions.get(class_label, []))
        # 寫入一行: 類別 檔案ID1 檔案ID2 ...
        f.write(f"{class_label} " + " ".join(map(str, sorted_ids)) + "\n")

print("\n分類完成! 結果已保存到 testing/testing_label.txt")
print("最終分類統計:")
for class_label in range(1, 6):
    cnt = len(predictions.get(class_label, []))
    print(f"類別 {class_label}: {cnt} 個檔案")