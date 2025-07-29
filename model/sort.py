import os
import shutil
from collections import defaultdict

def create_category_folders(base_folder):
    """創建1-5類別資料夾"""
    for i in range(1, 6):
        folder_path = os.path.join(base_folder, str(i))
        os.makedirs(folder_path, exist_ok=True)
        print(f"已創建資料夾: {folder_path}")

def parse_label_file(label_file_path):
    """解析標籤檔案，返回{類別: [檔案ID列表]}"""
    category_files = defaultdict(list)
    with open(label_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                category = int(parts[0])
                file_ids = list(map(int, parts[1:]))
                category_files[category].extend(file_ids)
    return category_files

def organize_files(source_folder, target_base_folder, category_files):
    """根據分類結果移動檔案"""
    moved_count = 0
    for category, file_ids in category_files.items():
        target_folder = os.path.join(target_base_folder, str(category))
        
        for file_id in file_ids:
            src_file = os.path.join(source_folder, f"{file_id}.txt")
            
            if os.path.exists(src_file):
                shutil.move(src_file, target_folder)
                moved_count += 1
            else:
                print(f"警告: 檔案不存在 - {src_file}")
    
    print(f"已從 {source_folder} 移動 {moved_count} 個檔案到 {target_base_folder}")

def main():
    # 設定路徑
    base_dir = "model"
    training_dir = os.path.join(base_dir, "training")
    testing_dir = os.path.join(base_dir, "testing")
    
    # 創建分類資料夾結構
    print("正在創建分類資料夾...")
    categorized_dir = os.path.join(base_dir, "categorized")
    os.makedirs(categorized_dir, exist_ok=True)
    
    training_categorized = os.path.join(categorized_dir, "training")
    testing_categorized = os.path.join(categorized_dir, "testing")
    
    create_category_folders(training_categorized)
    create_category_folders(testing_categorized)
    
    # 處理training數據
    print("\n處理training數據...")
    training_label_file = os.path.join(training_dir, "training_label.txt")
    if os.path.exists(training_label_file):
        training_categories = parse_label_file(training_label_file)
        organize_files(training_dir, training_categorized, training_categories)
    else:
        print(f"錯誤: 找不到training標籤檔案 - {training_label_file}")
    
    # 處理testing數據
    print("\n處理testing數據...")
    testing_label_file = os.path.join(testing_dir, "testing_label.txt")
    if os.path.exists(testing_label_file):
        testing_categories = parse_label_file(testing_label_file)
        organize_files(testing_dir, testing_categorized, testing_categories)
    else:
        print(f"錯誤: 找不到testing標籤檔案 - {testing_label_file}")
    
    print("\n檔案分類完成!")

if __name__ == "__main__":
    main()