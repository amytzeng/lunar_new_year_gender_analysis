import os
import glob
import torch
from transformers import BertTokenizer, BertModel
import numpy as np
import time
import jieba
import re
import matplotlib.pyplot as plt
from itertools import cycle
from sklearn.svm import SVC
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score, roc_curve, auc
from sklearn.preprocessing import label_binarize
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report, precision_score, recall_score, f1_score

# ------------------------
# 1. 資源與設備設定
# ------------------------

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

MODEL_TYPE = 'bert-base-chinese'  # 使用中文 BERT 模型
tokenizer = BertTokenizer.from_pretrained(MODEL_TYPE)  # 載入 BERT 分詞器
model = BertModel.from_pretrained(MODEL_TYPE).to(DEVICE)
model.eval()  # 設定為評估模式

stopword_file_path = "Classification/chinese_stopwords.txt"  # 停用詞文件路徑
training_label_path = "Classification/training_label.txt"    # 標籤文件路徑
train_data_dir = "Classification/Result"                   # 訓練集資料夾路徑
test_label_path = "Classification/test_label.txt"          # 測試集對應答案檔案路徑

# ------------------------
# 2. 通用函式：前處理、特徵擷取、資料讀取等
# ------------------------

def load_stopwords(filepath):
    """讀取停用詞檔，回傳 set。"""
    stopwords = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            stopwords.add(line.strip())
    return stopwords

def remove_emojis(text):
    """移除表情符號與相關特殊字元。"""
    emoji_pattern = re.compile(
        "[" 
        u"\U0001F600-\U0001F64F"  # 表情符號
        u"\U0001F300-\U0001F5FF"  # 符號和圖標
        u"\U0001F680-\U0001F6FF"  # 交通和地圖符號
        u"\U0001F1E0-\U0001F1FF"  # 國旗
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def tokenize(text):
    """使用 jieba 斷詞。"""
    return jieba.lcut(text)

def filter_stopwords_and_english(words, stopwords):
    """過濾停用詞與英文字元（帳號）。"""
    filtered = [
        w for w in words 
        if w not in stopwords and not re.match(r'[a-zA-Z]+', w)
    ]
    return ' '.join(filtered)

def get_cls_embedding(text, tokenizer, model, device):
    """
    給定文本，執行 BERT Tokenizer、Model 前向計算，取 [CLS] 向量。
    若文本為空回傳 None。
    """
    text = text.strip()
    if not text:
        return None
    # 轉換為 BERT input
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
    cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
    return cls_embedding

def load_labels(filepath):
    """
    從指定標籤文件中讀取標籤，
    每行格式：label idx1 idx2 ...
    回傳字典 { idx: label }
    """
    labels_dict = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:  # 確保每行至少有標籤和一個文件編號
                print(f"[Warning] 跳過無效行: {line.strip()}")
                continue
            try:
                label = int(parts[0])
                indices = list(map(int, parts[1:]))
                for index in indices:
                    labels_dict[index] = label
            except ValueError:
                print(f"[Warning] 跳過無效行: {line.strip()}")
                continue
    return labels_dict

def extract_features_and_labels(
    data_dir, labels_dict, tokenizer, model, device, stopwords
):
    """
    依照 labels_dict (idx -> label) 到 data_dir 中尋找對應檔案，並萃取 BERT 特徵。
    回傳:
       - embeddings: List of CLS 向量
       - labels: List of 對應的類別標籤
    """
    embeddings, labels = [], []
    start_time = time.time()
    found_files = 0
    missing_files = 0

    for idx, label in labels_dict.items():
        filepath = os.path.join(data_dir, f"{idx}.txt")
        if not os.path.exists(filepath):
            print(f"[Warning] File not found: {filepath}")
            missing_files += 1
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read().strip()
                
            if not text:  # 跳過空文件
                print(f"[Warning] 空文件: {filepath}")
                continue
                
            # 前處理
            text = remove_emojis(text)
            words = tokenize(text)
            text_filtered = filter_stopwords_and_english(words, stopwords)

            # BERT 向量
            cls_emb = get_cls_embedding(text_filtered, tokenizer, model, device)
            if cls_emb is not None:
                embeddings.append(cls_emb)
                labels.append(label)
                found_files += 1
                
        except Exception as e:
            print(f"[Error] 處理文件 {filepath} 時出錯: {str(e)}")
            continue

    end_time = time.time()
    print(f"找到 {found_files}/{len(labels_dict)} 個文件")
    print(f"缺失 {missing_files} 個文件")
    print(f"BERT 特徵提取時間: {end_time - start_time:.2f} 秒")

    if not embeddings:
        print("[Error] 未提取到任何特徵，請檢查:")
        print("1. 標籤文件和數據文件是否對應")
        print("2. 文件命名格式是否正確")
        print("3. 文件內容是否為有效文本")
        
    return np.array(embeddings), np.array(labels)

def train_evaluate_svm_with_kfold(X, y, n_splits=10):
    """
    使用 StratifiedKFold 對 (X, y) 進行 k 折交叉驗證，訓練 SVM 並評估。
    回傳最終的 (avg_precision, avg_recall, avg_f1)。
    """
    kf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    precision_scores, recall_scores, f1_scores = [], [], []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X, y), 1):
        print(f"[Fold {fold}]")
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        # 訓練 SVM
        svm_clf = SVC(kernel='rbf', class_weight='balanced')
        start_time = time.time()
        svm_clf.fit(X_train, y_train)
        train_time = time.time() - start_time
        print(f"  SVM 訓練時間: {train_time:.2f} 秒")

        # 預測
        start_time = time.time()
        val_pred = svm_clf.predict(X_val)
        pred_time = time.time() - start_time
        print(f"  SVM 預測時間: {pred_time:.2f} 秒")

        # 評估
        precision = precision_score(y_val, val_pred, average='weighted')
        recall = recall_score(y_val, val_pred, average='weighted')
        f1 = f1_score(y_val, val_pred, average='weighted')
        report = classification_report(y_val, val_pred)

        precision_scores.append(precision)
        recall_scores.append(recall)
        f1_scores.append(f1)

        print(f"  Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
        print(f"  Classification Report:\n{report}")

    # 平均分數
    avg_precision = np.mean(precision_scores)
    avg_recall = np.mean(recall_scores)
    avg_f1 = np.mean(f1_scores)
    return avg_precision, avg_recall, avg_f1

# ------------------------
# 3. 主程式流程
# ------------------------
if __name__ == "__main__":
    # 讀取停用詞
    stopwords = load_stopwords(stopword_file_path)

    # 讀取訓練標籤
    print("正在讀取標籤文件...")
    labels_dict = load_labels(training_label_path)
    print(f"成功讀取 {len(labels_dict)} 個標籤")
    
    # 讀取訓練資料 & 萃取特徵
    print("\n正在提取訓練特徵...")
    X, y = extract_features_and_labels(
        data_dir=train_data_dir,
        labels_dict=labels_dict,
        tokenizer=tokenizer,
        model=model,
        device=DEVICE,
        stopwords=stopwords
    )
    print(f"X shape: {X.shape}, y shape: {y.shape}")
    if X.size == 0 or y.size == 0:
        raise ValueError("Failed to extract training features or labels.")

    # k-fold 交叉驗證
    print("\n=== K-Fold Cross Validation ===")
    avg_precision, avg_recall, avg_f1 = train_evaluate_svm_with_kfold(X, y, n_splits=10)
    print(f"[KFold] Average Precision: {avg_precision:.4f}")
    print(f"[KFold] Average Recall:    {avg_recall:.4f}")
    print(f"[KFold] Average F1 Score:  {avg_f1:.4f}")

    # 用所有資料訓練最終模型
    print("\n=== Train Final SVM on All Data ===")
    final_svm_clf = SVC(kernel='rbf', class_weight='balanced')
    start_time = time.time()
    final_svm_clf.fit(X, y)
    print(f"Final SVM 訓練時間: {time.time() - start_time:.2f} 秒")

    # 讀取測試集（與訓練檔同資料夾，但索引不在 labels_dict 中）
    train_file_indices = set(labels_dict.keys())
    
    # 提取測試集特徵
    print("\n=== Extract Test Features ===")
    test_embeddings = []
    test_file_indices = []
    start_time = time.time()
    
    # 獲取所有數字.txt格式的文件
    for filepath in glob.glob(os.path.join(train_data_dir, "*.txt")):
        try:
            # 從文件名中提取數字
            filename = os.path.basename(filepath)
            idx = int(filename.split('.')[0])  # 假設文件名為"數字.txt"
            
            if idx in train_file_indices:
                continue  # 跳過訓練集文件
                
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read().strip()

            if not text:  # 跳過空文件
                continue

            # 前處理
            text = remove_emojis(text)
            words = tokenize(text)
            text_filtered = filter_stopwords_and_english(words, stopwords)
            
            # BERT 向量
            cls_emb = get_cls_embedding(text_filtered, tokenizer, model, DEVICE)
            if cls_emb is not None:
                test_embeddings.append(cls_emb)
                test_file_indices.append(idx)
                
        except Exception as e:
            print(f"[Error] 處理測試文件 {filepath} 時出錯: {str(e)}")
            continue

    print(f"BERT 測試集特徵提取時間: {time.time() - start_time:.2f} 秒")
    X_test = np.array(test_embeddings)
    print(f"找到 {len(test_file_indices)} 個測試文件")
    print(f"X_test shape: {X_test.shape}")
    if X_test.size == 0:
        raise ValueError("Failed to extract test features.")

    # 測試集推論
    print("\n=== Predict Test Data ===")
    start_time = time.time()
    predictions = final_svm_clf.predict(X_test)
    print(f"SVM 預測時間: {time.time() - start_time:.2f} 秒")

    # 讀取真實標籤
    print("\n=== Evaluate with Test Labels ===")
    true_labels_dict = load_labels(test_label_path)

    # 查找測試檔案缺少標籤的情況
    missing_indices = [idx for idx in test_file_indices if idx not in true_labels_dict]
    if missing_indices:
        print(f"[Warning] Missing labels for {len(missing_indices)} test files")

    true_labels = [true_labels_dict[idx] for idx in test_file_indices if idx in true_labels_dict]

    if len(true_labels) == 0:
        print("[Error] 沒有找到任何測試標籤，請檢查 test_label.txt 文件")
    else:
        precision = precision_score(true_labels, predictions, average='weighted')
        recall = recall_score(true_labels, predictions, average='weighted')
        f1 = f1_score(true_labels, predictions, average='weighted')
        report = classification_report(true_labels, predictions)

        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1 Score:  {f1:.4f}")
        print("Classification Report:")
        print(report)