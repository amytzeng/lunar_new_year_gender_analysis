import os
import shutil
from collections import defaultdict

def create_category_folders(base_folder):
	"""創建1-5類別資料夾"""
	for i in range(1, 6):
		folder_path = os.path.join(base_folder, str(i))
		os.makedirs(folder_path, exist_ok=True)

def parse_label_file(label_file_path):
	"""解析標籤檔案，返回{類別: [檔案ID列表]}"""
	category_files = defaultdict(list)
	with open(label_file_path, 'r', encoding='utf-8') as f:
		for line in f:
			parts = line.strip().split()
			if parts:
				category = parts[0]
				file_ids = parts[1:]
				category_files[category].extend(file_ids)
	return category_files

def organize_files(source_folder, category_files):
	"""根據分類結果移動檔案"""
	moved_count = 0
	for category, file_ids in category_files.items():
		target_folder = os.path.join(source_folder, str(category))
		for file_id in file_ids:
			src_file = os.path.join(source_folder, f"{file_id}.txt")
			dst_file = os.path.join(target_folder, f"{file_id}.txt")
			if os.path.exists(src_file):
				shutil.move(src_file, dst_file)
				moved_count += 1
			else:
				print(f"警告: 檔案不存在 - {src_file}")
	print(f"已移動 {moved_count} 個檔案到各分類資料夾")

def print_statistics(data_dir):
	"""統計各類別的檔案數量"""
	print("\n各類別統計：")
	print("=" * 60)
	
	category_names = {
		"1": "農曆新年與文化慶祝",
		"2": "政治與政策",
		"3": "衝突與安全",
		"4": "經濟與商業",
		"5": "其他/不相關"
	}
	
	total = 0
	for i in range(1, 6):
		folder_path = os.path.join(data_dir, str(i))
		if os.path.exists(folder_path):
			files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
			count = len(files)
			total += count
			category_name = category_names.get(str(i), "未知")
			print(f"類別 {i} ({category_name}): {count} 篇")
	
	print("=" * 60)
	print(f"總計: {total} 篇")

def main():
	# 設定路徑
	base_dir = os.path.dirname(os.path.abspath(__file__))
	data_dir = os.path.join(base_dir, 'data')
	classified_file = os.path.join(base_dir, 'classified_articles.txt')

	print("=" * 60)
	print(" " * 15 + "文章分類整理程式")
	print("=" * 60)
	print()

	# 檢查分類檔案是否存在
	if not os.path.exists(classified_file):
		print(f"❌ 錯誤: 找不到分類檔案 - {classified_file}")
		print("請先執行 classify_news_articles.py 進行分類")
		return

	# 創建分類資料夾
	print("正在創建分類資料夾...")
	create_category_folders(data_dir)
	print("✅ 已創建類別 1-5 資料夾")
	print()

	# 解析分類檔案
	print("正在讀取分類結果...")
	category_files = parse_label_file(classified_file)
	print(f"✅ 已讀取 {len(category_files)} 個類別")
	print()

	# 移動檔案
	print("正在移動檔案到各分類資料夾...")
	organize_files(data_dir, category_files)
	print()

	# 顯示統計
	print_statistics(data_dir)
	print()

	print("✅ 檔案分類完成!")

if __name__ == "__main__":
	main()

