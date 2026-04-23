import os
import time
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

def main(file_path):
    start = time.time()
    
    # 读取文件
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # 分割文件
    if len(file_data) <= 32:
        print("Error: File is too small to split into S1 and S2")
        return
    
    S1 = file_data[:-32]
    S2 = file_data[-32:]
    
    # 生成文件保存路径
    base_name = os.path.basename(file_path)
    dir_name = os.path.dirname(file_path)
    
    # 原始分割文件路径
    s1_path = os.path.join(dir_name, base_name + "_S1")
    s2_path = os.path.join(dir_name, base_name + "_S2")
    
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
    encrypted_s1_path = os.path.join(dir_name, base_name + "_encrypted_S1___")
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
    print(f"\nProcessing Summary:")
    print(f"  Original file size: {len(file_data)} bytes")
    print(f"  S1 size: {len(S1)} bytes")
    print(f"  S2 size: {len(S2)} bytes")
    print(f"  Encrypted S1 size: {len(encrypted_S1)} bytes")
    print(f"\nOff-chain time: {end - start:.4f} seconds")
    print(f"Tag (hex): {tag_S.hex()}")
    print(f"Keccak of encrypted S1 (hex): {hash_S1.hex()}")
    print(f"Keccak of S2 (hex): {hash_S2.hex()}")
    
    # 保存标签到文件
    tag_path = os.path.join(dir_name, base_name + "_tag.bin")
    with open(tag_path, 'wb') as f:
        f.write(tag_S)
    print(f"\nTag saved to: {tag_path}")

if __name__ == "__main__":
    file_path = "/root/home/infocom/5m.txt"  # 更改为实际文件路径
    main(file_path)