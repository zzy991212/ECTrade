import os
import hashlib
import csv
import time
from pathlib import Path
import sys

# 配置参数（依据文档《2018-740.pdf》）
FIXED_BLOCK_COUNT = 64  # 固定64个文件块
HASH_FUNC = hashlib.sha3_256  # 文档1-198节指定哈希函数（输出32字节）
KEY_LENGTH = 32  # 文档1-309节主密钥长度
INPUT_DIR = "/root/home/timescost_enc/fairswap/files"  # 自动读取此目录中的文件
OUTPUT_DIR = "/root/home/timescost_enc/fairswap/1"
CSV_PATH = "/root/home/timescost_enc/fairswap/csv/zzy.csv"
MIN_BLOCK_ALIGN = 32  # 文档1-198节要求块大小为32字节倍数
MERKLE_NODE_SIZE = 32  # 文档1-47节Merkle节点哈希长度（32字节）


def split_file_into_fixed_blocks(file_path):
    """文档1-120节：分块为64块，大小为32字节最小倍数"""
    file_size = os.path.getsize(file_path)
    base_block_size = (file_size + FIXED_BLOCK_COUNT - 1) // FIXED_BLOCK_COUNT
    block_size = ((base_block_size + MIN_BLOCK_ALIGN - 1) // MIN_BLOCK_ALIGN) * MIN_BLOCK_ALIGN
    blocks = []
    with open(file_path, "rb") as f:
        for _ in range(FIXED_BLOCK_COUNT):
            block = f.read(block_size)
            if len(block) < block_size:
                block += b"\x00" * (block_size - len(block))  # 填充至块大小
            blocks.append(block)
    assert len(blocks) == FIXED_BLOCK_COUNT, f"文件块数量错误（应为64，实际{len(blocks)}）"
    return blocks, block_size


def build_merkle_tree_with_all_nodes(blocks):
    """文档1-47节Algorithm 1：构建Merkle树并收集所有节点"""
    if not blocks:
        return [], b"", []
    tree_nodes = [HASH_FUNC(block).digest() for block in blocks]  # 叶子节点
    layers = [tree_nodes.copy()]  # 保存每一层的节点
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
    """文档1-309节Algorithm 9：生成与item_size等长的密钥（核心修正）"""
    keys = []
    for i in range(num_items):
        key = b""
        # 循环生成哈希，拼接至密钥长度等于item_size
        while len(key) < item_size:
            # 密钥材料：主密钥k + 索引i + 迭代次数（确保唯一性）
            iter_count = len(key) // HASH_FUNC().digest_size
            key_material = k + str(i).encode() + str(iter_count).encode()
            key_chunk = HASH_FUNC(key_material).digest()
            key += key_chunk
        # 截取至精确的item_size
        key = key[:item_size]
        keys.append(key)
    return keys


def encrypt_items(items, k, item_size):
    """文档1-309节Algorithm 9：XOR加密（确保加密后大小与原始一致）"""
    num_items = len(items)
    keys = generate_encryption_keys(k, num_items, item_size)
    encrypted_items = []
    for i in range(num_items):
        # 逐字节XOR，确保覆盖整个块
        encrypted_item = bytes([b ^ k_byte for b, k_byte in zip(items[i], keys[i])])
        encrypted_items.append(encrypted_item)
        # 验证加密后大小与原始块一致
        assert len(encrypted_item) == item_size, \
            f"第{i}个加密项大小错误（应为{item_size}，实际{len(encrypted_item)}）"
    return encrypted_items


def save_encrypted_file(encrypted_blocks, encrypted_merkle_nodes, 
                       block_size, merkle_node_count, output_path):
    """保存加密文件：元数据 + 加密块 + 加密Merkle节点"""
    with open(output_path, "wb") as f:
        # 元数据（16字节）
        f.write(block_size.to_bytes(4, byteorder="big"))  # 文件块大小
        f.write(FIXED_BLOCK_COUNT.to_bytes(4, byteorder="big"))  # 文件块数量
        f.write(merkle_node_count.to_bytes(4, byteorder="big"))  # Merkle节点数量
        f.write(MERKLE_NODE_SIZE.to_bytes(4, byteorder="big"))  # Merkle节点大小
        
        # 写入加密文件块（确保每个块大小正确）
        for block in encrypted_blocks:
            assert len(block) == block_size, f"加密块大小错误（应为{block_size}）"
            f.write(block)
        
        # 写入加密Merkle节点
        for node in encrypted_merkle_nodes:
            assert len(node) == MERKLE_NODE_SIZE, f"Merkle节点大小错误"
            f.write(node)


def generate_key(key_length):
    """文档1-309节：生成随机主密钥"""
    return os.urandom(key_length)


def hash_key(key):
    """生成密钥的哈希承诺"""
    return HASH_FUNC(key).digest()


def get_merkle_info(merkle_layers, target_leaf_index):
    """
    生成指定叶子节点的Merkle证明信息
    用于验证特定块在Merkle树中的存在性
    """
    if not merkle_layers or target_leaf_index >= len(merkle_layers[0]):
        return None
    
    info = {
        '_indexOut': None,  # 父节点索引
        '_Zout': None,      # 父节点哈希
        '_proofZout': [],   # 父节点路径证明
        '_indexIn': None,   # 目标节点索引
        '_Zin1': None,      # 目标节点哈希
        '_Zin2': None,      # 兄弟节点哈希
        '_proofZin': []     # 目标节点路径证明
    }
    
    current_index = target_leaf_index
    current_level = 0
    
    # 目标节点信息
    info['_indexIn'] = current_index
    info['_Zin1'] = merkle_layers[0][current_index]
    
    # 获取兄弟节点
    sibling_index = current_index + 1 if current_index % 2 == 0 else current_index - 1
    if sibling_index < len(merkle_layers[0]):
        info['_Zin2'] = merkle_layers[0][sibling_index]
    
    # 生成父节点信息
    parent_index = current_index // 2
    if current_level + 1 < len(merkle_layers):
        info['_indexOut'] = parent_index
        info['_Zout'] = merkle_layers[1][parent_index]
    
    # 生成路径证明（从叶子到根）
    current_index = parent_index
    current_level += 1
    
    while current_level < len(merkle_layers):
        # 收集当前节点的兄弟节点作为证明
        sibling_index = current_index + 1 if current_index % 2 == 0 else current_index - 1
        sibling_hash = None
        if sibling_index < len(merkle_layers[current_level]):
            sibling_hash = merkle_layers[current_level][sibling_index]
        
        # 记录证明（层级，兄弟节点哈希）
        info['_proofZout'].append((current_level, sibling_hash))
        
        # 向上移动一层
        current_index = current_index // 2
        current_level += 1
    
    # 复制证明信息（用于双重验证）
    info['_proofZin'] = info['_proofZout'].copy()
    
    return info


def process_directory():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    with open(CSV_PATH, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["原始文件名", "加密后文件名", "加密后大小(字节)", "生成密钥时间(ms)", "加密文件块时间(ms)"])
        
        for root, _, files in os.walk(INPUT_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # 1. 分块
                    blocks, block_size = split_file_into_fixed_blocks(file_path)
                    
                    # 2. 构建Merkle树（同时获取分层结构）
                    source_merkle_nodes, source_root_hash, source_merkle_layers = build_merkle_tree_with_all_nodes(blocks)
                    merkle_node_count = len(source_merkle_nodes)
                    
                    # 3. 生成主密钥并记录时间
                    start_time = time.time()
                    k = generate_key(KEY_LENGTH)
                    key_commitment = hash_key(k)
                    keygen_time = (time.time() - start_time) * 1000  # 转换为毫秒
                    
                    # 4. 加密文件块并记录时间
                    start_time = time.time()
                    encrypted_blocks = encrypt_items(blocks, k, block_size)
                    encryption_time = (time.time() - start_time) * 1000  # 转换为毫秒
                    
                    # 5. 构建加密数据的Merkle树
                    encrypted_merkle_nodes, encrypted_root_hash, _ = build_merkle_tree_with_all_nodes(encrypted_blocks)
                    
                    # 6. 加密Merkle节点
                    x1 = time.time()
                    encrypted_merkle_nodes = encrypt_items(source_merkle_nodes, k, MERKLE_NODE_SIZE)
                    x2 = time.time()
                    print(file_path)
                    print(x2-x1)
                    
                    # 7. 保存加密文件
                    rel_path = os.path.relpath(file_path, INPUT_DIR)
                    output_subdir = os.path.dirname(rel_path)
                    Path(os.path.join(OUTPUT_DIR, output_subdir)).mkdir(parents=True, exist_ok=True)
                    
                    encrypted_filename = f"{os.path.splitext(file)[0]}.enc"
                    output_path = os.path.join(OUTPUT_DIR, output_subdir, encrypted_filename)
                    save_encrypted_file(encrypted_blocks, encrypted_merkle_nodes,
                                       block_size, merkle_node_count, output_path)
                    
                    # 8. 验证大小
                    encrypted_size = os.path.getsize(output_path)
                    expected_size = 16 + (block_size * FIXED_BLOCK_COUNT) + (MERKLE_NODE_SIZE * merkle_node_count)
                    assert encrypted_size == expected_size, f"大小异常：预期{expected_size}，实际{encrypted_size}"
                    csv_writer.writerow([file, encrypted_filename, encrypted_size, keygen_time, encryption_time])
                    
                except Exception as e:
                    print(f"处理文件{file}失败: {str(e)}")


if __name__ == "__main__":
    if not os.path.isdir(INPUT_DIR):
        print(f"错误: {INPUT_DIR} 不是有效的文件夹")
        sys.exit(1)
    process_directory()
    print(f"加密文件保存至{OUTPUT_DIR}，统计数据记录在{CSV_PATH}")