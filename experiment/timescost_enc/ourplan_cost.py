import os
import hashlib
import csv
import time
from pathlib import Path
import sys
import secrets

# 配置参数
FIXED_BLOCK_COUNT = 64
HASH_FUNC = hashlib.sha3_256
KEY_LENGTH = 32
INPUT_DIR = "/root/home/timescost_enc/ourplan/files"
OUTPUT_DIR = "/root/home/timescost_enc/ourplan/1"
CSV_PATH = "/root/home/timescost_enc/ourplan/zzy.csv"
MIN_BLOCK_ALIGN = 32
MERKLE_NODE_SIZE = 32
TEST_STRING_LENGTH = 1024  # 测试用01串长度

def split_file_into_fixed_blocks(file_path):
    file_size = os.path.getsize(file_path)
    base_block_size = (file_size + FIXED_BLOCK_COUNT - 1) // FIXED_BLOCK_COUNT
    block_size = ((base_block_size + MIN_BLOCK_ALIGN - 1) // MIN_BLOCK_ALIGN) * MIN_BLOCK_ALIGN
    blocks = []
    with open(file_path, "rb") as f:
        for _ in range(FIXED_BLOCK_COUNT):
            block = f.read(block_size)
            if len(block) < block_size:
                block += b"\x00" * (block_size - len(block))
            blocks.append(block)
    assert len(blocks) == FIXED_BLOCK_COUNT, f"文件块数量错误（应为64，实际{len(blocks)}）"
    return blocks, block_size

def build_merkle_tree_with_all_nodes(blocks):
    if not blocks:
        return [], b"", []
    tree_nodes = [HASH_FUNC(block).digest() for block in blocks]
    layers = [tree_nodes.copy()]
    current_level = tree_nodes.copy()
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i+1] if (i+1) < len(current_level) else left
            parent = HASH_FUNC(left + right).digest()
            next_level.append(parent)
        tree_nodes.extend(next_level)
        layers.append(next_level)
        current_level = next_level
    merkle_root = current_level[0] if current_level else b""
    return tree_nodes, merkle_root, layers

def generate_encryption_keys(k, num_items, item_size):
    keys = []
    for i in range(num_items):
        key = b""
        while len(key) < item_size:
            iter_count = len(key) // HASH_FUNC().digest_size
            key_material = k + str(i).encode() + str(iter_count).encode()
            key_chunk = HASH_FUNC(key_material).digest()
            key += key_chunk
        key = key[:item_size]
        keys.append(key)
    return keys

def encrypt_items(items, k, item_size):
    num_items = len(items)
    keys = generate_encryption_keys(k, num_items, item_size)
    encrypted_items = []
    for i in range(num_items):
        encrypted_item = bytes([b ^ k_byte for b, k_byte in zip(items[i], keys[i])])
        encrypted_items.append(encrypted_item)
        assert len(encrypted_item) == item_size, f"第{i}个加密项大小错误（应为{item_size}，实际{len(encrypted_item)}）"
    return encrypted_items

def save_encrypted_file(encrypted_blocks, encrypted_merkle_nodes, 
                       block_size, merkle_node_count, output_path):
    with open(output_path, "wb") as f:
        f.write(block_size.to_bytes(4, byteorder="big"))
        f.write(FIXED_BLOCK_COUNT.to_bytes(4, byteorder="big"))
        f.write(merkle_node_count.to_bytes(4, byteorder="big"))
        f.write(MERKLE_NODE_SIZE.to_bytes(4, byteorder="big"))
        
        for block in encrypted_blocks:
            assert len(block) == block_size, f"加密块大小错误（应为{block_size}）"
            f.write(block)
        
        for node in encrypted_merkle_nodes:
            assert len(node) == MERKLE_NODE_SIZE, f"Merkle节点大小错误"
            f.write(node)

def generate_key(key_length):
    return os.urandom(key_length)

def hash_key(key):
    return HASH_FUNC(key).digest()

def generate_random_binary_string(length):
    """生成指定长度的随机01字节串"""
    return secrets.token_bytes(length)

def test_encrypt_binary_string():
    """测试随机01串加密性能（执行一次）"""
    # 生成随机01串和密钥
    binary_string = generate_random_binary_string(TEST_STRING_LENGTH)
    key = generate_key(KEY_LENGTH)
    
    # 测量加密时间
    start_time = time.time()
    encrypt_items([binary_string], key, TEST_STRING_LENGTH)
    elapsed_time = time.time() - start_time
    
    return elapsed_time

def test_generate_re_encryption_key():
    """测试生成重加密密钥性能（执行一次）"""
    # 测量生成密钥时间
    start_time = time.time()
    generate_key(KEY_LENGTH)
    elapsed_time = time.time() - start_time
    
    return elapsed_time

def process_directory():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    with open(CSV_PATH, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        # 写入CSV文件头
        header = ["文件名", "文件加密时间(秒)", "01串加密时间(秒)", "生成重加密密钥时间(秒)"]
        csv_writer.writerow(header)
        
        # 处理文件加密
        for root, _, files in os.walk(INPUT_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # 测试随机01串加密
                    binary_encryption_time = test_encrypt_binary_string()
                    
                    # 测试生成重加密密钥
                    key_generation_time = test_generate_re_encryption_key()
                    
                    # 1. 分块
                    blocks, block_size = split_file_into_fixed_blocks(file_path)
                    
                    # 2. 构建Merkle树
                    source_merkle_nodes, _, _ = build_merkle_tree_with_all_nodes(blocks)
                    merkle_node_count = len(source_merkle_nodes)
                    
                    # 3. 生成主密钥
                    k = generate_key(KEY_LENGTH)
                    
                    # 4. 加密文件块并记录时间
                    start_time = time.time()
                    encrypted_blocks = encrypt_items(blocks, k, block_size)
                    file_encryption_time = time.time() - start_time
                    
                    # 5. 加密Merkle节点
                    encrypted_merkle_nodes = encrypt_items(source_merkle_nodes, k, MERKLE_NODE_SIZE)
                    
                    # 6. 保存加密文件
                    rel_path = os.path.relpath(file_path, INPUT_DIR)
                    output_subdir = os.path.dirname(rel_path)
                    Path(os.path.join(OUTPUT_DIR, output_subdir)).mkdir(parents=True, exist_ok=True)
                    
                    encrypted_filename = f"{os.path.splitext(file)[0]}.enc"
                    output_path = os.path.join(OUTPUT_DIR, output_subdir, encrypted_filename)
                    save_encrypted_file(encrypted_blocks, encrypted_merkle_nodes,
                                       block_size, merkle_node_count, output_path)
                    
                    # 7. 记录所有时间
                    csv_writer.writerow([file, file_encryption_time, binary_encryption_time, key_generation_time])
                    
                except Exception as e:
                    print(f"处理文件{file}失败: {str(e)}")

if __name__ == "__main__":
    if not os.path.isdir(INPUT_DIR):
        print(f"错误: {INPUT_DIR} 不是有效的文件夹")
        sys.exit(1)
    process_directory()
    print(f"加密文件保存至{OUTPUT_DIR}，统计数据记录在{CSV_PATH}")