import os
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
from Crypto.Hash import keccak
import csv

def encrypt_data(data_chunk, key):
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = iv + cipher.encrypt(pad(data_chunk, AES.block_size))
    return encrypted_data

def compute_tag(hash_S1, hash_S2):
    return bytes([a ^ b for a, b in zip(hash_S1, hash_S2)])

def process_file(file_path, output_dir, size_data):
    start = time.time()
    
    # 读取文件
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # 分割文件
    if len(file_data) <= 32:
        print(f"Error: File {file_path} is too small to split into S1 and S2")
        return
    
    S1 = file_data[:-32]
    S2 = file_data[-32:]
    
    # 生成文件保存路径
    base_name = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    
    # 原始分割文件路径
    s1_path = os.path.join(output_dir, file_name_without_ext + "_S1.bin")
    s2_path = os.path.join(output_dir, file_name_without_ext + "_S2.bin")
    
    # 保存原始S1和S2
    with open(s1_path, 'wb') as f:
        f.write(S1)
    with open(s2_path, 'wb') as f:
        f.write(S2)
    
    print(f"Original S1 saved to: {s1_path}")
    print(f"Original S2 saved to: {s2_path}")
    
    # 使用S2作为密钥加密S1
    aes_key = S2
    encrypted_S1 = encrypt_data(S1, aes_key)
    
    # 保存加密后的S1
    encrypted_s1_path = os.path.join(output_dir, file_name_without_ext + "_encrypted_S1.bin")
    with open(encrypted_s1_path, 'wb') as f:
        f.write(encrypted_S1)
    print(f"Encrypted S1 saved to: {encrypted_s1_path}")
    
    # 计算哈希值
    k1 = keccak.new(digest_bits=256)
    k1.update(encrypted_S1)
    hash_S1 = k1.digest()

    k2 = keccak.new(digest_bits=256)
    k2.update(S2)
    hash_S2 = k2.digest()
    
    tag_S = compute_tag(hash_S1, hash_S2)
    
    end = time.time()
    print(f"\nProcessing Summary for {file_path}:")
    print(f"  Original file size: {len(file_data)} bytes")
    print(f"  S1 size: {len(S1)} bytes")
    print(f"  S2 size: {len(S2)} bytes")
    print(f"  Encrypted S1 size: {len(encrypted_S1)} bytes")
    print(f"\nOff-chain time: {end - start:.4f} seconds")
    print(f"Tag (hex): {tag_S.hex()}")
    print(f"Keccak of encrypted S1 (hex): {hash_S1.hex()}")
    print(f"Keccak of S2 (hex): {hash_S2.hex()}")
    
    # 保存标签到文件
    tag_path = os.path.join(output_dir, file_name_without_ext + "_tag.bin")
    with open(tag_path, 'wb') as f:
        f.write(tag_S)
    print(f"\nTag saved to: {tag_path}")
    
    # 收集文件大小信息
    size_data.append({
        'file_name': base_name,
        'original_size': len(file_data),
        'S1_size': len(S1),
        'S2_size': len(S2),
        'encrypted_S1_size': len(encrypted_S1),
        'tag_size': len(tag_S)
    })

def main(input_dir, output_dir, size_csv_path):
    # 确保输出文件夹存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化文件大小数据列表
    size_data = []
    
    # 获取输入文件夹中的所有txt文件
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.txt'):
            file_path = os.path.join(input_dir, file_name)
            print(f"Processing file: {file_path}")
            process_file(file_path, output_dir, size_data)
    
    # 保存文件大小数据到CSV文件
    with open(size_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['file_name', 'original_size', 'S1_size', 'S2_size', 'encrypted_S1_size', 'tag_size']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(size_data)
    print(f"\nFile sizes saved to: {size_csv_path}")

if __name__ == "__main__":
    input_directory = "/root/home/experiment/wrongfile"  # 输入文件夹路径
    output_directory = "/root/home/experiment/wrongfile"  # 输出文件夹路径
    size_csv_path = "/root/home/experiment/wrongfile/infocom_file_sizes.csv"  # 文件大小CSV路径
    main(input_directory, output_directory, size_csv_path)