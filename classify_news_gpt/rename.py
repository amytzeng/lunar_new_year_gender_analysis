"""
重新編號 data 目錄下的文章檔案
將所有 .txt 檔案從 1 開始重新編號
"""

import os
import shutil

def renumber_files(data_dir="classify_news_gpt/data", backup=True):
    """
    重新編號資料夾中的文件
    
    Args:
        data_dir: 資料目錄路徑
        backup: 是否備份原始檔案
    """
    
    if not os.path.exists(data_dir):
        print(f"❌ 資料目錄不存在: {data_dir}")
        return
    
    # 收集所有 .txt 檔案
    txt_files = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(data_dir, filename)
            txt_files.append((filename, file_path))
    
    if not txt_files:
        print(f"❌ 在 {data_dir} 中找不到 .txt 檔案")
        return
    
    # 按照檔案名排序（保持原有順序）
    txt_files.sort(key=lambda x: x[0])
    
    total_files = len(txt_files)
    print(f"找到 {total_files} 個 .txt 檔案")
    print()
    
    # 顯示前10個和後10個檔案作為預覽
    print("檔案預覽（前10個）:")
    for i, (filename, _) in enumerate(txt_files[:10], 1):
        print(f"  {i}. {filename}")
    if total_files > 20:
        print(f"  ... (省略 {total_files - 20} 個檔案)")
    if total_files > 10:
        print("檔案預覽（後10個）:")
        for i, (filename, _) in enumerate(txt_files[-10:], total_files - 9):
            print(f"  {i}. {filename}")
    print()
    
    # 確認是否繼續
    response = input(f"即將將這 {total_files} 個檔案重新編號為 1.txt ~ {total_files}.txt，是否繼續？ (y/n): ")
    if response.lower() != 'y':
        print("操作已取消")
        return
    
    # 備份原始檔案（如果需要）
    if backup:
        backup_dir = f"{data_dir}_backup"
        if os.path.exists(backup_dir):
            response = input(f"⚠️  備份目錄 {backup_dir} 已存在，是否覆蓋？ (y/n): ")
            if response.lower() != 'y':
                print("操作已取消")
                return
            shutil.rmtree(backup_dir)
        
        print(f"正在備份到 {backup_dir}...")
        shutil.copytree(data_dir, backup_dir)
        print(f"✅ 備份完成")
        print()
    
    # 建立重新編號的對應表
    renumber_mapping = {}
    for new_num, (old_filename, old_path) in enumerate(txt_files, 1):
        new_filename = f"{new_num}.txt"
        renumber_mapping[old_filename] = new_filename
    
    # 先將所有檔案移動到臨時名稱（避免衝突）
    print("步驟 1/2: 將檔案移動到臨時名稱...")
    temp_mapping = {}
    for old_filename, old_path in txt_files:
        temp_filename = f"temp_{old_filename}"
        temp_path = os.path.join(data_dir, temp_filename)
        shutil.move(old_path, temp_path)
        temp_mapping[temp_filename] = renumber_mapping[old_filename]
    
    # 再將臨時檔案重新命名為最終編號
    print("步驟 2/2: 重新編號檔案...")
    for temp_filename, new_filename in temp_mapping.items():
        temp_path = os.path.join(data_dir, temp_filename)
        new_path = os.path.join(data_dir, new_filename)
        shutil.move(temp_path, new_path)
    
    print()
    print("=" * 60)
    print("✅ 重新編號完成！")
    print("=" * 60)
    print(f"總共處理: {total_files} 個檔案")
    print(f"新檔案範圍: 1.txt ~ {total_files}.txt")
    if backup:
        print(f"備份位置: {backup_dir}/")
    print()
    
    # 輸出對應表到檔案
    mapping_file = "renumber_mapping.txt"
    print(f"正在儲存對應表到 {mapping_file}...")
    with open(mapping_file, "w", encoding="utf-8") as f:
        f.write("原始檔名 -> 新檔名\n")
        f.write("=" * 60 + "\n")
        for old_filename, new_filename in renumber_mapping.items():
            f.write(f"{old_filename} -> {new_filename}\n")
    
    print(f"✅ 對應表已儲存到 {mapping_file}")
    print()
    
    # 顯示前10個對應關係
    print("對應表預覽（前10個）:")
    for i, (old_filename, new_filename) in enumerate(list(renumber_mapping.items())[:10], 1):
        print(f"  {old_filename} -> {new_filename}")
    if total_files > 10:
        print(f"  ... (完整對應表請查看 {mapping_file})")
    print()

def main():
    """主程式"""
    print("=" * 60)
    print(" " * 15 + "資料重新編號工具")
    print("=" * 60)
    print()
    
    # 預設處理 data 目錄
    data_dir = "classify_news_gpt/data"
    
    # 檢查目錄是否存在
    if not os.path.exists(data_dir):
        print(f"❌ 找不到 {data_dir} 目錄")
        print("請確認你在正確的目錄下執行此程式")
        return
    
    # 執行重新編號
    renumber_files(data_dir, backup=True)
    
    print("操作完成！")

if __name__ == "__main__":
    main()

