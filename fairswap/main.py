import os
import sys
from pathlib import Path
import csv
from Crypto.Hash import keccak

# 配置参数（保留原有配置）
FIXED_BLOCK_COUNT = 64
KEY_LENGTH = 32
INPUT_DIR = "/root/home/fairswap/1"
OUTPUT_DIR = "/root/home/fairswap/2"
CSV_PATH = "/root/home/fairswap/3.csv"
MIN_BLOCK_ALIGN = 32
MERKLE_NODE_SIZE = 32


def keccak256(data):
    k = keccak.new(digest_bits=256)
    k.update(data)
    return k.digest()


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
    assert len(blocks) == FIXED_BLOCK_COUNT, f"块数量错误（应为64，实际{len(blocks)}）"
    return blocks, block_size


def build_merkle_tree_with_all_nodes(blocks):
    if not blocks:
        return [], b"", []
    tree_nodes = [keccak256(block) for block in blocks]
    layers = [tree_nodes.copy()]
    current_level = tree_nodes.copy()
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i+1] if (i+1) < len(current_level) else left
            parent = keccak256(left + right)
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
            iter_count = len(key) // 32
            key_material = k + str(i).encode() + str(iter_count).encode()
            key_chunk = keccak256(key_material)
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
        assert len(encrypted_item) == item_size, f"加密项大小错误"
    return encrypted_items


def save_encrypted_file(encrypted_blocks, encrypted_merkle_nodes, 
                       block_size, merkle_node_count, output_path):
    with open(output_path, "wb") as f:
        f.write(block_size.to_bytes(4, byteorder="big"))
        f.write(FIXED_BLOCK_COUNT.to_bytes(4, byteorder="big"))
        f.write(merkle_node_count.to_bytes(4, byteorder="big"))
        f.write(MERKLE_NODE_SIZE.to_bytes(4, byteorder="big"))
        
        for block in encrypted_blocks:
            assert len(block) == block_size, f"加密块大小错误"
            f.write(block)
        
        for node in encrypted_merkle_nodes:
            assert len(node) == MERKLE_NODE_SIZE, f"Merkle节点大小错误"
            f.write(node)


def generate_key(key_length):
    return os.urandom(key_length)


def hash_key(key):
    return keccak256(key)


def get_merkle_info(merkle_layers, target_leaf_index):
    if not merkle_layers or target_leaf_index >= len(merkle_layers[0]):
        return None
    
    info = {
        '_indexOut': None, '_Zout': None, '_proofZout': [],
        '_indexIn': None, '_Zin1': None, '_Zin2': None, '_proofZin': []
    }
    
    current_index = target_leaf_index
    current_level = 0
    
    info['_indexIn'] = current_index
    info['_Zin1'] = merkle_layers[0][current_index]
    
    sibling_index = current_index + 1 if current_index % 2 == 0 else current_index - 1
    if sibling_index < len(merkle_layers[0]):
        info['_Zin2'] = merkle_layers[0][sibling_index]
    
    parent_index = current_index // 2
    if current_level + 1 < len(merkle_layers):
        info['_indexOut'] = parent_index
        info['_Zout'] = merkle_layers[1][parent_index]
    
    current_index = parent_index
    current_level += 1
    while current_level < len(merkle_layers):
        sibling_index = current_index + 1 if current_index % 2 == 0 else current_index - 1
        sibling_hash = None
        if sibling_index < len(merkle_layers[current_level]):
            sibling_hash = merkle_layers[current_level][sibling_index]
        info['_proofZout'].append((current_level, sibling_hash))
        info['_proofZin'].append((current_level, sibling_hash))
        current_index = current_index // 2
        current_level += 1
    
    return info


def split_block_into_bytes32(block, block_size):
    length = block_size // 32
    bytes32_array = []
    for i in range(length):
        start = i * 32
        end = start + 32
        bytes32_element = block[start:end]
        assert len(bytes32_element) == 32, f"子单元大小错误"
        bytes32_array.append(bytes32_element)
    return bytes32_array, length


def crypt_large(index_block, bytes32_array, key):
    encrypted_array = []
    length = len(bytes32_array)
    current_index = index_block * length
    for i in range(length):
        key_material = current_index.to_bytes(32, byteorder="big") + key
        sub_key = keccak256(key_material)
        plaintext = bytes32_array[i]
        ciphertext = bytes([p ^ k for p, k in zip(plaintext, sub_key)])
        encrypted_array.append(ciphertext)
        current_index += 1
    return encrypted_array


def process_directory():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    with open(CSV_PATH, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["原始文件名", "加密后文件名", "加密后大小(字节)"])
        
        for root, _, files in os.walk(INPUT_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # 分块与Merkle树
                    blocks, block_size = split_file_into_fixed_blocks(file_path)
                    source_merkle_nodes, source_root_hash, source_merkle_layers = build_merkle_tree_with_all_nodes(blocks)
                    merkle_node_count = len(source_merkle_nodes)
                    print(f"处理{file}：块大小={block_size}，Merkle节点数={merkle_node_count}")
                    
                    # 密钥与加密
                    k = generate_key(KEY_LENGTH)
                    key_commitment = hash_key(k)
                    encrypted_blocks = encrypt_items(blocks, k, block_size)
                    encrypted_merkle_nodes, encrypted_root_hash, _ = build_merkle_tree_with_all_nodes(encrypted_blocks)
                    
                    # ---------------- 新增：合约初始化所需参数 ----------------
                    print("\n=== 合约初始化所需参数 ===")
                    print(f"_ciphertextRoot = \"0x{encrypted_root_hash.hex()}\"")  # 密文Merkle树根哈希
                    print(f"_fileRoot = \"0x{source_root_hash.hex()}\"")        # 原始文件Merkle树根哈希
                    print(f"_keyCommit = \"0x{key_commitment.hex()}\"")      # 密钥承诺
                    # --------------------------------------------------------
                    
                    # 打印关键值
                    print("\n=== 四个关键值（bytes32格式） ===")
                    print(f"密钥原文: 0x{k.hex()}")
                    print(f"密钥承诺: 0x{key_commitment.hex()}")
                    print(f"源文件根哈希: 0x{source_root_hash.hex()}")
                    print(f"密文根哈希: 0x{encrypted_root_hash.hex()}")
                    
                    # Merkle证明信息
                    target_leaf_index = 63
                    merkle_info = get_merkle_info(source_merkle_layers, target_leaf_index)
                    if merkle_info:
                        print("\n生成所需Merkle树信息：")
                        print(f"_indexOut: {merkle_info['_indexOut']}（父节点索引）")
                        print(f"_Zout: 0x{merkle_info['_Zout'].hex()}（父节点哈希）")
                        print(f"_indexIn: {merkle_info['_indexIn']}，_Zin1哈希: 0x{merkle_info['_Zin1'].hex()}")
                    
                    # 输出Zin1和Zin2数组
                    print("\n===== Zin1和Zin2（带双引号的bytes32[length]数组） =====")
                    target_block_index = 63
                    adjacent_block_index = 16 if 16 < len(blocks) else 14
                    
                    target_block = blocks[target_block_index]
                    adjacent_block = blocks[adjacent_block_index]
                    zin1_plain_array, length = split_block_into_bytes32(target_block, block_size)
                    zin2_plain_array, _ = split_block_into_bytes32(adjacent_block, block_size)
                    zin1_cipher_array = crypt_large(target_block_index, zin1_plain_array, k)
                    zin2_cipher_array = crypt_large(adjacent_block_index, zin2_plain_array, k)
                    
                    print(f"\nZin1（index={target_block_index}，bytes32[{length}]）：")
                    print("[")
                    for elem in zin1_cipher_array:
                        print(f'    "0x{elem.hex()}",')
                    print("]")
                    
                    print(f"\nZin2（index={adjacent_block_index}，bytes32[{length}]）：")
                    print("[")
                    for elem in zin2_cipher_array:
                        print(f'    "0x{elem.hex()}",')
                    print("]")
                    
                    # 输出proofZout数组
                    print("\n===== proofZout（Merkle证明路径） =====")
                    proofZout_array = []
                    for level, sibling_hash in merkle_info['_proofZout']:
                        if sibling_hash:
                            proofZout_array.append(f'"0x{sibling_hash.hex()}"')
                        else:
                            proofZout_array.append('null')
                    
                    print("proofZout = [")
                    for i, proof in enumerate(proofZout_array):
                        print(f"    {proof},  ")
                    print("]")
                    
                    # 输出proofZin数组
                    print("\n===== proofZin（Merkle证明路径 - 叶子到父节点） =====")
                    proofZin_array = []
                    for level, sibling_hash in merkle_info['_proofZin']:
                        if sibling_hash:
                            proofZin_array.append(f'"0x{sibling_hash.hex()}"')
                        else:
                            proofZin_array.append('null')
                    
                    print("proofZin = [")
                    for i, proof in enumerate(proofZin_array):
                        print(f"    {proof},  ")
                    print("]")
                    
                    # 输出_Zout值
                    print("\n===== _Zout（父节点哈希值） =====")
                    print(f"_Zout = \"0x{merkle_info['_Zout'].hex()}\"")
                    
                    # 保存加密文件与记录
                    rel_path = os.path.relpath(file_path, INPUT_DIR)
                    output_subdir = os.path.dirname(rel_path)
                    Path(os.path.join(OUTPUT_DIR, output_subdir)).mkdir(parents=True, exist_ok=True)
                    
                    encrypted_filename = f"{os.path.splitext(file)[0]}.enc"
                    output_path = os.path.join(OUTPUT_DIR, output_subdir, encrypted_filename)
                    save_encrypted_file(encrypted_blocks, encrypted_merkle_nodes,
                                       block_size, merkle_node_count, output_path)
                    
                    encrypted_size = os.path.getsize(output_path)
                    csv_writer.writerow([file, encrypted_filename, encrypted_size])
                    print(f"\n加密完成: {file} → {encrypted_filename}，大小={encrypted_size}字节")
                    
                except Exception as e:
                    print(f"处理文件{file}失败: {str(e)}")


if __name__ == "__main__":
    if not os.path.isdir(INPUT_DIR):
        print(f"错误: {INPUT_DIR} 不是有效的文件夹")
        sys.exit(1)
    process_directory()
    print(f"\n加密文件保存至{OUTPUT_DIR}，大小记录在{CSV_PATH}")