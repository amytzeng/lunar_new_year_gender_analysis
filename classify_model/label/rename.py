import os
import re

def natural_sort_key(s):
    """自然排序輔助函數"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]

def rename_files_in_directory(directory):
    """重新命名目錄中的所有txt文件為連續編號"""
    # 獲取目錄中所有txt文件並按自然順序排序
    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    files.sort(key=natural_sort_key)
    
    # 檢查目錄是否為空
    if not files:
        print(f"目錄 {directory} 中沒有找到任何txt文件")
        return
    
    print(f"找到 {len(files)} 個txt文件，準備重新命名...")
    
    # 重新命名文件
    for index, filename in enumerate(files, start=1):
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, f"{index}.txt")
        
        # 避免覆蓋已存在的文件
        if os.path.exists(new_path):
            print(f"警告: {new_path} 已存在，跳過重命名 {filename}")
            continue
            
        os.rename(old_path, new_path)
        print(f"已將 {filename} 重命名為 {index}.txt")
    
    print("所有文件重命名完成！")

if __name__ == "__main__":
    # 設定要處理的目錄
    target_directory = "分類器\Result"
    
    # 檢查目錄是否存在
    if not os.path.exists(target_directory):
        print(f"錯誤: 目錄 {target_directory} 不存在")
    else:
        rename_files_in_directory(target_directory)