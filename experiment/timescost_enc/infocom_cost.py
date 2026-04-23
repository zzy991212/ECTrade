import os
import time
import csv
import random
import secrets
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
from Crypto.Hash import keccak

def encrypt_data(data_chunk, key):
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = iv + cipher.encrypt(pad(data_chunk, AES.block_size))
    return encrypted_data

def compute_tag(hash_S1, hash_S2):
    return bytes([a ^ b for a, b in zip(hash_S1, hash_S2)])

def main():
    # 输入和输出目录配置
    input_dir = "/root/home/timescost_enc/infocom/files"
    output_dir = "/root/home/timescost_enc/infocom/output"
    csv_path = "/root/home/timescost_enc/infocom/zzy.csv"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有文件
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    
    # 结果存储列表
    results = []
    
    for file_name in files:
        file_path = os.path.join(input_dir, file_name)
        print(f"\nProcessing file: {file_name}")
        
        try:
            start = time.time()
            
            # 读取文件
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 检查文件大小
            if len(file_data) <= 32:
                print("Error: File is too small to split into S1 and S2")
                results.append({
                    'file_name': file_name,
                    'file_size': len(file_data),
                    'encryption_time': 'N/A',
                    'status': 'Error: File too small'
                })
                continue
            
            # 分割文件
            S1 = file_data[:-32]
            S2 = file_data[-32:]
            
            # 生成随机密钥（而不是使用S2作为密钥）
            aes_key = secrets.token_bytes(32)  # 256位随机密钥
            
            # 加密S1
            encrypted_S1 = encrypt_data(S1, aes_key)
            
            # 计算哈希值
            k1 = keccak.new(digest_bits=256)
            k1.update(encrypted_S1)
            hash_S1 = k1.digest()

            k2 = keccak.new(digest_bits=256)
            k2.update(S2)
            hash_S2 = k2.digest()
            
            # 计算标签
            tag_S = compute_tag(hash_S1, hash_S2)
            
            end = time.time()
            encryption_time = end - start
            
            # 保存结果
            results.append({
                'file_name': file_name,
                'file_size': len(file_data),
                'encryption_time': encryption_time,
                'status': 'Success'
            })
            
            print(f"  File size: {len(file_data)} bytes")
            print(f"  Encryption time: {encryption_time:.4f} seconds")
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            results.append({
                'file_name': file_name,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 'Unknown',
                'encryption_time': 'N/A',
                'status': f'Error: {str(e)}'
            })
    
    # 写入CSV文件
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['file_name', 'file_size', 'encryption_time', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"\nEncryption times saved to: {csv_path}")

if __name__ == "__main__":
    main()    