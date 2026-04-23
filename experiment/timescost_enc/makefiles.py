import os

def generate_file(size_in_bytes, file_name):
    """生成指定大小的文件"""
    try:
        with open(file_name, 'wb') as f:
            # 每次写入1MB以避免内存问题
            chunk_size = 1024 * 1024
            remaining_bytes = size_in_bytes
            
            while remaining_bytes > 0:
                write_size = min(chunk_size, remaining_bytes)
                f.write(b'\0' * write_size)
                remaining_bytes -= write_size
        
        print(f"成功生成文件: {file_name}, 大小: {size_in_bytes / (1024 * 1024):.2f} MB")
    except Exception as e:
        print(f"生成文件时出错: {e}")

def main():
    """主函数，生成不同大小的文件"""
    # 定义要生成的文件大小（字节）
    sizes = {
        '10k' : 10 * 1024
        # '100k': 100 * 1024,
        # '500k': 500 * 1024,
        # '1M': 1 * 1024 * 1024,
        # '5M': 5 * 1024 * 1024,
        # '10M': 10 * 1024 * 1024,
        # '50M': 50 * 1024 * 1024
    }
    
    # 获取当前工作目录
    current_dir = os.getcwd()
    
    # 为每个大小生成文件
    for size_name, size_bytes in sizes.items():
        file_name = os.path.join(current_dir, f"file_{size_name}.txt")
        generate_file(size_bytes, file_name)

if __name__ == "__main__":
    main()