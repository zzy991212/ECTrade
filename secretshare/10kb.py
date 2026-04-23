import os
import random
import string

def generate_10kb_text(output_file='10kb_text.txt'):
    """
    生成一个精确10KB（10240字节）的文本文件
    
    参数:
        output_file: 输出文件名（默认：10kb_text.txt）
    """
    # 目标大小：10KB = 10 * 1024 = 10240字节
    target_bytes = 10240
    
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
        print(f"  实际大小: {file_size/1024:.2f} KB (精确匹配10KB)")
    else:
        print(f"生成错误! 文件大小: {file_size} 字节 (目标: {target_bytes} 字节)")

if __name__ == "__main__":
    generate_10kb_text()