import os
import random
import string
import csv

def generate_text_file(file_size_kb, output_file):
    """
    根据给定的文件大小（以KB为单位）生成文本文件
    
    参数:
        file_size_kb: 文件大小（以KB为单位）
        output_file: 输出文件名
    """
    # 将KB转换为字节
    target_bytes = int(file_size_kb * 1024)  # 确保为转换整数字节
    
    # 创建高效生成器（避免内存溢出）
    def text_generator():
        # 使用可打印ASCII字符（32-126）和换行符
        chars = string.ascii_letters + string.digits + string.punctuation + ' '
        
        # 预计算每行结构：平均75字符/行 + 换行符
        while True:
            # 随机行长度 (65-85字符)
            line_length = random.randint(65, 85)
            # 生成随机文本行
            yield ''.join(random.choices(chars, k=line_length)) + '\n'
    
    # 写入文件
    written_bytes = 0
    with open(output_file, 'w', encoding='ascii') as f:
        gen = text_generator()
        
        while written_bytes < target_bytes:
            # 获取下一行
            line = next(gen)
            line_bytes = len(line.encode('ascii'))
            
            # 检查是否超出目标
            if written_bytes + line_bytes > target_bytes:
                # 计算需要截断的字符数
                remaining = target_bytes - written_bytes
                # 生成刚好足够的ASCII字符（无换行符）
                chars = string.ascii_letters + string.digits + ' '
                f.write(''.join(random.choices(chars, k=remaining)))
                written_bytes += remaining
            else:
                f.write(line)
                written_bytes += line_bytes
    
    # 验证文件大小
    file_size = os.path.getsize(output_file)
    if file_size == target_bytes:
        print(f"✓ 成功生成 {file_size} 字节文件: {output_file}")
        print(f"  实际大小: {file_size/1024:.2f} KB (精确匹配 {file_size_kb} KB)")
    else:
        print(f"生成错误! 文件大小: {file_size} 字节 (目标: {target_bytes} 字节)")

def process_csv(input_csv, output_dir):
    """
    读取CSV文件中的id和file_size(KB)数据，并生成对应大小的文件
    
    参数:
        input_csv: CSV文件路径
        output_dir: 输出文件夹路径
    """
    # 确保输出文件夹存在
    os.makedirs(output_dir, exist_ok=True)
    
    with open(input_csv, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # 获取id和文件大小
            id_value = row['id']  # 假设CSV中有id列
            file_size_kb = int(float(row['file_size(KB)']))  # 处理浮点数字符串
            
            # 生成文件名格式为 [id]_file_sizeKB_text.txt
            output_file_name = f"[{id_value}]_{file_size_kb}KB_text.txt"
            output_file_path = os.path.join(output_dir, output_file_name)
            
            # 调用生成的文件函数
            generate_text_file(file_size_kb, output_file_path)

if __name__ == "__main__":
    # 替换为你的CSV文件路径
    csv_file_path = '/root/home/experiment/bad_behavior_data_fairswaponchain.csv'
    # 指定输出文件夹路径
    output_directory = '/root/home/experiment/fairswap_data2'
    process_csv(csv_file_path, output_directory)

