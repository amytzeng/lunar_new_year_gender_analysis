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

def main():
	# 設定路徑
	base_dir = os.path.dirname(os.path.abspath(__file__))
	data_dir = os.path.join(base_dir, 'data')
	classified_file = os.path.join(base_dir, 'classified_posts.txt')

	# 創建分類資料夾
	create_category_folders(data_dir)

	# 解析分類檔案
	if os.path.exists(classified_file):
		category_files = parse_label_file(classified_file)
		organize_files(data_dir, category_files)
	else:
		print(f"錯誤: 找不到分類檔案 - {classified_file}")

	print("\n檔案分類完成!")

if __name__ == "__main__":
	main()
import os
import shutil

# 路徑設定
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, 'data')
classified_file = os.path.join(base_dir, 'classified_posts.txt')

# 建立五個資料夾（1~5）
for i in range(1, 6):
	folder_path = os.path.join(data_dir, str(i))
	os.makedirs(folder_path, exist_ok=True)

# 讀取分類結果
with open(classified_file, 'r', encoding='utf-8') as f:
	for line in f:
		line = line.strip()
		if not line:
			continue
		# 假設格式：組別 編號（例如：1 10001）
		parts = line.split()
		if len(parts) < 2:
			continue
		group = parts[0]
		file_id = parts[1]
		src_file = os.path.join(data_dir, f'{file_id}.txt')
		dst_folder = os.path.join(data_dir, group)
		dst_file = os.path.join(dst_folder, f'{file_id}.txt')
		if os.path.exists(src_file):
			shutil.move(src_file, dst_file)
		else:
			print(f'檔案不存在: {src_file}')
