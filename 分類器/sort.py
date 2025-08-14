import os
import random
import shutil
from pathlib import Path

def split_files(source_dir, train_ratio=0.1, random_seed=42):
    """
    將源目錄中的txt文件按比例分配到training和testing資料夾
    :param source_dir: 源文件目錄
    :param train_ratio: 訓練集比例 (預設 0.1，即 10%)
    :param random_seed: 隨機種子 (確保可重現性)
    """
    # 設定路徑
    source_path = Path(source_dir)
    train_path = source_path / "training"
    test_path = source_path / "testing"
    
    # 建立目標資料夾
    train_path.mkdir(exist_ok=True)
    test_path.mkdir(exist_ok=True)
    
    # 獲取所有txt文件
    all_files = list(source_path.glob("*.txt"))
    total_files = len(all_files)
    
    print(f"找到 {total_files} 個txt文件")
    
    # 設置隨機種子以確保可重現性
    random.seed(random_seed)
    
    # 隨機打亂文件順序
    random.shuffle(all_files)
    
    # 計算分割點
    split_point = int(total_files * train_ratio)
    
    # 分割文件
    train_files = all_files[:split_point]
    test_files = all_files[split_point:]
    
    print(f"將 {len(train_files)} 個文件分配到 training 資料夾")
    print(f"將 {len(test_files)} 個文件分配到 testing 資料夾")
    
    # 移動文件到相應資料夾
    for file in train_files:
        shutil.move(str(file), str(train_path / file.name))
    
    for file in test_files:
        shutil.move(str(file), str(test_path / file.name))
    
    print("文件分配完成！")

if __name__ == "__main__":
    # 設定源文件目錄 (包含5298個txt文件的目錄)
    source_directory = "分類器\Result"  # 請修改為你的實際目錄

    # 檢查目錄是否存在
    if not Path(source_directory).exists():
        print(f"錯誤: 目錄 {source_directory} 不存在")
    else:
        # 調用分割函數 (10% training, 90% testing)
        split_files(source_directory, train_ratio=0.1)