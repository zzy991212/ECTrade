import os
import hashlib
import time
import math
import sys
from collections import defaultdict

def find_text_in_file(file_path, search_text):
    """
    在文件中查找文本内容，返回所有匹配位置
    
    参数:
        file_path: 文件路径
        search_text: 要搜索的文本
    
    返回:
        list: 匹配位置的字节偏移量列表
        int: 文本长度
    """
    # 读取整个文件内容
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # 将搜索文本转换为字节
    try:
        search_bytes = search_text.encode('utf-8')
    except UnicodeEncodeError:
        print(f"警告: 无法编码文本 '{search_text}' 为UTF-8")
        return [], 0
    
    text_length = len(search_bytes)
    
    if text_length == 0:
        print("警告: 搜索文本为空")
        return [], 0
    
    # 查找所有匹配位置
    matches = []
    start = 0
    
    while start < len(content):
        pos = content.find(search_bytes, start)
        if pos == -1:
            break
        matches.append(pos)
        start = pos + 1
    
    return matches, text_length

def compute_file_merkle_root(file_path, block_size=None, output_dir=None, search_text=None):
    """
    计算文件的Merkle根哈希并保存分块文件
    
    参数:
        file_path: 文件路径
        block_size: 分块大小(字节)，默认为10KB (10240字节)
        output_dir: 分块文件输出目录
        search_text: 要查找的文本内容
    
    返回:
        merkle_root: Merkle根哈希(十六进制字符串)
        block_hashes: 所有分块的哈希列表
        text_blocks: 包含搜索文本的块索引列表
    """
    # 验证文件存在
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 获取文件基本信息
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    # 设置输出目录
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(file_path), "blocks")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"文件: {file_name}")
    print(f"大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
    
    # 处理搜索文本
    text_positions = []
    text_length = 0
    if search_text:
        # 查找文本位置
        text_positions, text_length = find_text_in_file(file_path, search_text)
        
        if not text_positions:
            print(f"\n警告: 未找到文本 '{search_text}'")
        else:
            print(f"\n搜索文本: '{search_text}' (长度: {text_length} 字节)")
            print(f"在文件中找到 {len(text_positions)} 处匹配")
            
            # 设置分块大小为文本长度
            block_size = text_length
            print(f"设置分块大小: {block_size} 字节 (等于文本长度)")
    else:
        # 使用默认分块大小
        if not block_size:
            block_size = 10240  # 默认10KB
        print(f"分块大小: {block_size} 字节")
    
    # 计算分块数量
    num_blocks = math.ceil(file_size / block_size)
    print(f"分块数量: {num_blocks}")
    
    # 存储每个块的哈希
    block_hashes = []
    # 存储包含搜索文本的块索引
    text_blocks = []
    # 存储每个块的实际大小（防止填充影响）
    block_actual_sizes = []
    
    # 读取文件
    with open(file_path, 'rb') as f:
        # 创建块索引映射：文本位置 -> 块索引
        text_to_block = {}
        
        # 首先处理包含文本的块
        for i, pos in enumerate(text_positions):
            # 计算块的起始位置，确保文本在块中心
            start_pos = max(0, pos - block_size // 2)
            end_pos = min(file_size, start_pos + block_size)
            
            # 调整起始位置确保块大小一致
            if end_pos - start_pos < block_size:
                if start_pos == 0:
                    # 文件开头，扩展结束位置
                    end_pos = min(file_size, start_pos + block_size)
                else:
                    # 文件末尾，调整起始位置
                    start_pos = max(0, end_pos - block_size)
            
            # 移动到块起始位置
            f.seek(start_pos)
            block = f.read(block_size)
            
            # 如果块不足，填充0（仅用于哈希计算）
            if len(block) < block_size:
                padded_block = block + b'\0' * (block_size - len(block))
            else:
                padded_block = block
            
            # 计算块哈希(SHA-256)
            block_hash = hashlib.sha256(padded_block).digest()
            block_hashes.append(block_hash)
            block_actual_sizes.append(len(block))
            
            # 保存分块文件
            block_idx = len(block_hashes) - 1
            block_path = os.path.join(output_dir, f"{file_name}_textblock_{i+1:05d}.bin")
            with open(block_path, 'wb') as block_file:
                block_file.write(block)
            
            # 标记为文本块
            text_blocks.append(block_idx)
            
            # 检查文本是否在块中
            block_text = block[pos - start_pos:pos - start_pos + text_length].decode('utf-8', errors='replace')
            print(f"  创建文本块 {block_idx+1} (位置: {start_pos}-{start_pos+len(block)}): '{block_text}'")
            
            # 记录文本位置到块的映射
            text_to_block[pos] = block_idx
        
        # 处理剩余的文件部分（非文本块）
        current_pos = 0
        block_idx = len(block_hashes)
        
        while current_pos < file_size:
            # 跳过已处理的文本块区域
            skip = False
            for pos in text_positions:
                start_pos = max(0, pos - block_size // 2)
                end_pos = min(file_size, start_pos + block_size)
                
                if start_pos <= current_pos < end_pos:
                    current_pos = end_pos
                    skip = True
                    break
            
            if current_pos >= file_size:
                break
                
            if skip:
                continue
                
            # 读取块数据
            f.seek(current_pos)
            block = f.read(block_size)
            actual_size = len(block)
            
            # 如果块不足，填充0（仅用于哈希计算）
            if actual_size < block_size:
                padded_block = block + b'\0' * (block_size - actual_size)
            else:
                padded_block = block
            
            # 计算块哈希(SHA-256)
            block_hash = hashlib.sha256(padded_block).digest()
            block_hashes.append(block_hash)
            block_actual_sizes.append(actual_size)
            
            # 保存分块文件
            block_path = os.path.join(output_dir, f"{file_name}_block_{block_idx+1:05d}.bin")
            with open(block_path, 'wb') as block_file:
                block_file.write(block)
            
            # 移动到下一个位置
            current_pos += actual_size
            block_idx += 1
            
            # 打印进度
            if block_idx % 100 == 0 or current_pos >= file_size:
                progress = min(100.0, 100.0 * current_pos / file_size)
                print(f"已处理块: {block_idx} ({progress:.1f}%)")
    
    # 构建Merkle树并返回根哈希
    merkle_root = build_merkle_tree(block_hashes)
    return merkle_root.hex(), block_hashes, text_blocks

def build_merkle_tree(hashes):
    """
    构建Merkle树并返回根哈希
    
    参数:
        hashes: 哈希值列表(二进制格式)
    
    返回:
        merkle_root: Merkle根哈希(二进制格式)
    """
    # 如果没有哈希值，返回空
    if not hashes:
        return b''
    
    # 如果只有一个哈希值，直接返回
    if len(hashes) == 1:
        return hashes[0]
    
    # 处理奇数个节点情况
    if len(hashes) % 2 != 0:
        hashes.append(hashes[-1])
    
    # 创建下一层节点
    next_level = []
    for i in range(0, len(hashes), 2):
        # 拼接两个哈希值
        combined = hashes[i] + hashes[i+1]
        # 计算父节点哈希
        parent_hash = hashlib.sha256(combined).digest()
        next_level.append(parent_hash)
    
    # 递归构建树
    return build_merkle_tree(next_level)

def save_merkle_info(file_path, merkle_root, block_hashes, text_blocks, search_text):
    """保存Merkle信息和所有分块哈希"""
    info_file = file_path + ".merkle_info"
    with open(info_file, "w") as f:
        f.write(f"Merkle root: {merkle_root}\n")
        f.write(f"File: {file_path}\n")
        f.write(f"Block count: {len(block_hashes)}\n")
        
        # 如果搜索了文本，记录相关信息
        if search_text:
            f.write(f"\nSearch text: '{search_text}'\n")
            f.write(f"Text length: {len(search_text.encode('utf-8'))} bytes\n")
            f.write(f"Blocks containing text: {len(text_blocks)}\n")
            
            for block_idx in text_blocks:
                f.write(f"  Block {block_idx+1}: {block_hashes[block_idx].hex()}\n")
        
        f.write("\nAll block hashes:\n")
        
        for i, block_hash in enumerate(block_hashes):
            # 标记包含文本的块
            if search_text and i in text_blocks:
                f.write(f"Block {i+1} [TEXT]: {block_hash.hex()}\n")
            else:
                f.write(f"Block {i+1}: {block_hash.hex()}\n")
    
    return info_file

def main():
    # 设置文件路径和输出目录
    file_path = "/root/home/devide/testfile/testfile.txt"
    output_dir = "/root/home/devide/testfile/blocks"
    
    # 检查路径是否存在
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        sys.exit(1)
    
    if not os.path.exists(os.path.dirname(output_dir)):
        print(f"错误: 输出目录不存在 - {output_dir}")
        sys.exit(1)
    
    # 用户输入要搜索的文本内容
    search_text = input("请输入要搜索的文本内容: ")
    if not search_text.strip():
        print("未输入搜索文本，将使用默认分块大小")
        search_text = None
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 计算Merkle根并保存分块
        merkle_root, block_hashes, text_blocks = compute_file_merkle_root(
            file_path, 
            output_dir=output_dir,
            search_text=search_text
        )
        
        # 输出结果
        print("\n" + "="*50)
        print(f"Merkle根哈希: {merkle_root}")
        print("="*50)
        
        # 显示处理时间
        elapsed = time.time() - start_time
        print(f"处理完成! 耗时: {elapsed:.2f}秒")
        
        # 保存Merkle信息和所有分块哈希
        info_file = save_merkle_info(file_path, merkle_root, block_hashes, text_blocks, search_text)
        print(f"\n分块哈希信息已保存到: {info_file}")
        
        # 输出分块文件信息
        block_files = sorted(os.listdir(output_dir))
        print(f"\n已创建 {len(block_files)} 个分块文件在目录: {output_dir}")
        
        # 如果搜索了文本，显示包含文本的块
        if search_text and text_blocks:
            print("\n包含搜索文本的块:")
            for block_idx in text_blocks:
                block_file = f"{os.path.basename(file_path)}_textblock_{text_blocks.index(block_idx)+1:05d}.bin"
                print(f"  块 {block_idx+1}: {block_file}")
        elif search_text and not text_blocks:
            print("\n警告: 未找到包含搜索文本的块")
    
    except FileNotFoundError as e:
        print(f"错误: {e}")
    except Exception as e:
        import traceback
        print(f"处理过程中发生错误: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()