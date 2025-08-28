import os
import re


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]

def read_files_from_directory(directory):
    files_content = {}
    for filename in sorted(os.listdir(directory), key=natural_sort_key):
        if filename.endswith('.txt'):
            # 提取檔案編號 (移除 .txt 副檔名)
            file_number = filename[:-4]  # 直接去掉最後4個字元(.txt)
            try:
                # 驗證確實是數字檔名
                file_number_int = int(file_number)
                with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                    files_content[filename] = file.read()
            except ValueError:
                # 如果不是純數字檔名，跳過
                continue
    return files_content
1
def write_labeled_output(output_file, labels):
    with open(output_file, 'w', encoding='utf-8') as file:
        for label, file_numbers in labels.items():
            file.write(f"{label} {' '.join(file_numbers)}\n")

def main():
    input_directory = r'分類器\Result\training'
    output_file = r'分類器\label_output.txt'
    files_content = read_files_from_directory(input_directory)

    labels = {1: [], 2: [], 3: [], 4:[], 5:[]}

    print("Press 1, 2, 3, 4, or 5 to label the files. Press 'q' to quit.")

    for filename, content in files_content.items():
        print(f"Content of {filename}:\n{content}\n")
        label = None
        while label not in ['1', '2', '3', '4', '5']:
            label = input("Enter label (1, 2, 3, 4, 5) or 'q' to quit: ")
            if label == 'q':
                print("Quitting...")
                write_labeled_output(output_file, labels)
                print("Labeled output has been written to", output_file)
                return
        # 修改這裡，直接使用去掉.txt的檔名作為編號
        file_number = filename[:-4]  # 移除 .txt 副檔名
        labels[int(label)].append(file_number)

    write_labeled_output(output_file, labels)
    print("Labeled output has been written to", output_file)

if __name__ == "__main__":
    main()