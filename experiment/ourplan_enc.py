'''
NAL16 Proxy Re-Encryption
| From: Nunez, D., Agudo, I., & Lopez, J. (2016). On the application of generic CCA-secure transformations to proxy re-encryption
| Published in: Security and Communication Networks
| Available from: http://onlinelibrary.wiley.com/doi/10.1002/sec.1434/full
* type:           proxy encryption
* properties:     CCA_21-secure, unidirectional, single-hop, non-interactive, collusion-resistant
* setting:        Pairing groups (Type 1 "symmetric")
* assumption:     3-wDBDHI (3-weak Decisional Bilinear DH Inversion)
* to-do:          first-level encryption & second-level decryption, type annotations
:Authors:    D. Nuñez
:Date:       04/2016
'''

from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair
from charm.toolbox.PREnc import PREnc
from charm.toolbox.hash_module import Hash, int2Bytes, integer
import ast
import base64
import os
import csv
import time

debug = False
class NAL16a(PREnc):
    """
    Testing NAL16a implementation 

    >>> from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
    >>> groupObj = PairingGroup('SS512')
    >>> pre = NAL16a(groupObj)
    >>> params = pre.setup()
    >>> (pk_a, sk_a) = pre.keygen(params)
    >>> (pk_b, sk_b) = pre.keygen(params)
    >>> msg = groupObj.random(GT)
    >>> c_a = pre.encrypt(params, pk_a, msg)
    >>> rk = pre.rekeygen(params, pk_a, sk_a, pk_b, sk_b)
    >>> c_b = pre.re_encrypt(params, rk, c_a)
    >>> assert msg == pre.decrypt(params, sk_b, c_b), 'Decryption of re-encrypted ciphertext was incorrect'
    """
    
    def __init__(self, groupObj):
        global group
        group = groupObj
        
    def F(self, params, t):
        return (params['u'] ** t) * params['v']

    def setup(self):
        g, u, v = group.random(G1), group.random(G1), group.random(G1)
        Z = pair(g,g)

        params = {'g': g, 'u': u, 'v': v, 'Z': Z} 
        if(debug):
            print("Setup: Public parameters...")
            group.debug(params)
        return params

    def keygen(self, params):
        x = group.random(ZR)
        g_x = params['g'] ** x

        sk = x
        pk = g_x

        if(debug):
            print('\nKeygen...')
            print("pk => '%s'" % pk)
            print("sk => '%s'" % sk)
        return (pk, sk)

    def rekeygen(self, params, pk_a, sk_a, pk_b, sk_b):
        rk = pk_b ** (~sk_a)
        if(debug):
            print('\nReKeyGen...')
            print("rk => '%s'" % rk)
        return rk

    def encrypt(self, params, pk, m):
        r1, r2 = group.random(ZR), group.random(ZR)
        
        c0 = self.F(params, r1) ** r2
        c1 = m * (params['Z'] ** r2)
        c2 = pk ** r2

        c = {'c0': c0, 'c1': c1, 'c2': c2}
               
        if(debug):
            print('\nEncrypt...')
            print('m => %s' % m)
            print('r1 => %s' % r1)
            print('r2 => %s' % r2)
            print('c => %s' % c)
            group.debug(c)
        return c  
        
    def decrypt(self, params, sk, c):
        c1 = c['c1'] 
        c2 = c['c2']

        m = c1 / (c2 ** (~sk))
        
        if(debug):
            print('\nDecrypt...')
            print('m => %s' % m)

        return m
        
    def re_encrypt(self, params, rk, c_a):
        c2 = c_a['c2']

        c_b = c_a
        c_b['c2'] = pair(c2, rk)
        
        if(debug):
            print('\nRe-encrypt...')
            print('c\' => %s' % c_b)
        return c_b

class NAL16b(NAL16a):
    """
    Testing NAL16 implementation 

    >>> from charm.toolbox.pairinggroup import PairingGroup,ZR,G1,G2,GT,pair
    >>> groupObj = PairingGroup('SS512')
    >>> pre = NAL16b(groupObj)
    >>> params = pre.setup()
    >>> (pk_a, sk_a) = pre.keygen(params)
    >>> (pk_b, sk_b) = pre.keygen(params)
    >>> msg = b"Hello world!"
    >>> c_a = pre.encrypt(params, pk_a, msg)
    >>> rk = pre.rekeygen(params, pk_a, sk_a, pk_b, sk_b)
    >>> c_b = pre.re_encrypt(params, rk, c_a)
    >>> assert msg == pre.decrypt(params, sk_b, c_b), 'Decryption of re-encrypted ciphertext was incorrect'
    """

    def __init__(self, groupObj):
        global group, h
        group = groupObj
        h = Hash(group)

    def H(self, gt, s):
        h1 = group.hash((gt, s, 1), ZR)
        h2 = group.hash((gt, s, 2), ZR)
        if(debug):
            print('\nH ...')
            print("gt => '%s'" % gt)
            print("s => '%s'" % s)
            print("h1 => '%s'" % h1)
            print("h2 => '%s'" % h2)
        return (h1, h2)

    def G(self, x):
        hh = h.hashToZn(x)
        if(debug):
            print('\nG ...')
            print("x => '%s'" % x)
            print("G(x) => '%s'" % hh)
        return hh

    def encrypt(self, params, pk, m):
        sigma = group.random(GT)
        c3 = self.G(sigma) ^ integer(m)
        (r1, r2) = self.H(sigma, c3)

        c = super(NAL16b, self).encrypt(params, pk, sigma)

        c['c3'] = c3
               
        if(debug):
            print('\nEncrypt...')
            print('m => %s' % m)
            print('r1 => %s' % r1)
            print('r2 => %s' % r2)
            print('c => %s' % c)
            group.debug(c)
        return c 

    def decrypt_original(self, params, sk, c):
        T = pair(c['c2'], params['g'])
        sigma = c['c1'] / (T ** (~sk))
        
        c3 = c['c3']
        (r1, r2) = self.H(sigma, c3)
        
        c0_prime = self.F(params, r1) ** r2
        m_int = c3 ^ self.G(sigma)
        m = int2Bytes(m_int)
        
        if debug:
            print('\nDecrypt_original...')
            print('m => %s' % m)
        return m

    def decrypt(self, params, sk, c):
        sigma = super(NAL16b, self).decrypt(params, sk, c)
        c3 = c['c3']
        (r1, r2) = self.H(sigma, c3)
        m = int2Bytes(c3 ^ self.G(sigma))
        
        if(debug):
            print('\nDecrypt...')
            print('m => %s' % m)
        return m

    def re_encrypt(self, params, rk, c_a):
        c_b = super(NAL16b, self).re_encrypt(params, rk, c_a)
        c_b['c3'] = c_a['c3']
        if(debug):
            print('\nRe-encrypt...')
            print('c\' => %s' % c_b)
        return c_b

# 配置目录路径
input_dir = "/root/home/experiment/ourplan_data"
output_dir = "/root/home/experiment/ourplan_data_enc"
stats_dir = "/root/home/experiment/ourplan_data_enc_size"
stats_dir_rk = "/root/home/experiment/ourplan_data_enc_rk_size"  # 新增的rk大小统计目录

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)
os.makedirs(stats_dir, exist_ok=True)
os.makedirs(stats_dir_rk, exist_ok=True)  # 创建rk大小统计目录

# 初始化加密方案
groupObj = PairingGroup('SS512')
pre = NAL16b(groupObj)
params = pre.setup()

# 生成Bob的密钥对（固定接收者）
(pk_bob, sk_bob) = pre.keygen(params)

# 创建CSV文件记录大小信息
csv_path = os.path.join(stats_dir, 'encrypted_file_sizes.csv')
csv_rk_path = os.path.join(stats_dir_rk, 'rekey_sizes.csv')  # rk大小统计文件

with open(csv_path, 'w', newline='') as csvfile, open(csv_rk_path, 'w', newline='') as csv_rk_file:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(['Filename', 'Original Size (bytes)', 'Encrypted Size (bytes)', 'Encryption Time (s)'])
    
    csv_rk_writer = csv.writer(csv_rk_file)
    csv_rk_writer.writerow(['Filename', 'Rekey Size (bytes)'])

# 遍历输入目录中的所有txt文件
for filename in os.listdir(input_dir):
    if filename.endswith('.txt'):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, os.path.splitext(filename)[0] + '.enc')
        
        # 读取文件内容
        with open(input_path, 'rb') as f:
            original_data = f.read()
        original_size = len(original_data)
        
        # 生成临时发送者密钥对
        (pk_alice, sk_alice) = pre.keygen(params)
        
        # 生成重加密密钥(rk)并计算其大小
        rk = pre.rekeygen(params, pk_alice, sk_alice, pk_bob, sk_bob)
        rk_ser = group.serialize(rk)
        rk_size = len(rk_ser)
        
        # 加密文件内容
        start_time = time.time()
        ciphertext = pre.encrypt(params, pk_bob, original_data)
        encryption_time = time.time() - start_time
        
        # 计算加密后大小（Base64格式）
        encrypted_size = 0
        lines = []
        
        # 处理c0, c1, c2（群元素）
        for key in ['c0', 'c1', 'c2']:
            value = ciphertext[key]
            # 序列化群元素
            ser_data = group.serialize(value)
            # Base64编码
            base64_str = base64.b64encode(ser_data).decode('ascii')
            # 添加类型标记
            if key in ['c0', 'c2']:
                type_str = 'g1'
            else:  # c1
                type_str = 'gt'
            line = f"{key}:{type_str}:{base64_str}\n"
            lines.append(line)
            encrypted_size += len(line.encode('utf-8'))
        
        # 处理c3（整数）
        c3_value = ciphertext['c3']
        # 将整数转换为字节串
        c3_bytes = int2Bytes(c3_value)
        # Base64编码
        c3_base64 = base64.b64encode(c3_bytes).decode('ascii')
        c3_line = f"c3:int:{c3_base64}\n"
        lines.append(c3_line)
        encrypted_size += len(c3_line.encode('utf-8'))
        
        # 写入加密文件（Base64格式）
        with open(output_path, 'w') as f_out:
            f_out.writelines(lines)
        
        # 记录统计信息
        with open(csv_path, 'a', newline='') as csvfile, open(csv_rk_path, 'a', newline='') as csv_rk_file:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow([filename, original_size, encrypted_size, encryption_time])
            
            csv_rk_writer = csv.writer(csv_rk_file)
            csv_rk_writer.writerow([filename, rk_size])
        
        print(f"Encrypted {filename}: "
              f"{original_size} bytes -> {encrypted_size} bytes, "
              f"RK size: {rk_size} bytes, "
              f"time: {encryption_time:.4f}s")

print("Encryption completed. Size statistics saved to:", csv_path)
print("Rekey size statistics saved to:", csv_rk_path)
print(f"Encrypted files saved to: {output_dir}")