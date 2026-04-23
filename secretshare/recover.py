import SS_zzy as Shamir
import os
import struct
import random
from Cryptodome.Random import get_random_bytes
import time
from multiprocessing import Pool
#random_id = []

def split_file(file_path, tot, n, k, output_dir, fake_count=0):  # 添加output_dir参数
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取文件大小并计算块数
    file_size = os.path.getsize(file_path)
    block_size = 16
    num_blocks = (file_size + block_size - 1) // block_size  # 向上取整
    
    # 创建n个真实份额文件并写入元数据
    share_files = {}
    
    # 生成真实份额
    for i in range(1, n + 1):
        # 使用新的输出目录
        share_path = os.path.join(output_dir, f'share_{random_id[i-1]}.bin')
        f = open(share_path, 'wb')
        # 写入元数据: 文件大小(8字节) + 份额索引(4字节)
        f.write(struct.pack('>Q', file_size))  # 大端8字节无符号整数
        f.write(struct.pack('>I', random_id[i-1]))          # 大端4字节无符号整数
        share_files[i] = f

    # 分块处理文件
    with open(file_path, 'rb') as f:
        for _ in range(num_blocks):
            block = f.read(block_size)
            
            # 填充最后一块
            if len(block) < block_size:
                block += b'\0' * (block_size - len(block))
            
            # 生成分块份额
            shares = Shamir.split(k, n, block, random_id=random_id)
            
            for idx, share_data in shares:
                share_files[random_id.index(idx)+1].write(share_data)

    # 关闭所有真实份额文件
    for f in share_files.values():
        f.close()
    
    fake_indices = []
    for i in range(1,fake_count + 1):
        x = random.randint(1,tot)
        while (x in random_id)or(x in fake_indices):
            x = random.randint(1,tot)
        fake_indices.append(x)
    #print(fake_indices)

    for i in range(1, fake_count + 1):
        fake_index = fake_indices[i-1]
        
        # 使用新的输出目录
        share_path = os.path.join(output_dir, f'share_{fake_index}.bin')
        with open(share_path, 'wb') as fake_file:
            # 关键改进：使用相同的文件大小元数据！
            fake_file.write(struct.pack('>Q', file_size))  # 与真文件相同
            fake_file.write(struct.pack('>I', fake_index))
            
            # 写入相同数量的随机块
            for _ in range(num_blocks):
                fake_file.write(get_random_bytes(16))

    # 返回所有生成的文件索引（真实和假）
    return random_id, fake_indices  # 修改返回值以区分真实和假份额


def combine_files(share_paths, output_path):
    # 读取元数据和初始化
    file_size = None
    block_size = 16
    share_handles = []
    indices = []
    
    for path in share_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"The share file {path} does not exist.")
        f = open(path, 'rb')
        # 读取元数据
        curr_file_size = struct.unpack('>Q', f.read(8))[0]
        curr_index = struct.unpack('>I', f.read(4))[0]
    
        # 输出当前处理的份额信息（可选）
        # print(f"Processing share: {path}, Size: {curr_file_size}, Index: {curr_index}")
        
        # 验证文件大小一致性
        if file_size is None:
            file_size = curr_file_size
        elif file_size != curr_file_size:
            f.close()
            raise ValueError("Inconsistent file size in share files")
        share_handles.append(f)
        indices.append(curr_index)
    
    # 输出参与恢复的份额索引（可选）
    # print(f"Combining shares with indices: {indices}")
    
    # 计算块数
    num_blocks = (file_size + block_size - 1) // block_size
    
    # 恢复文件
    with open(output_path, 'wb') as out_file:
        for _ in range(num_blocks):
            shares = []
            for idx, f in zip(indices, share_handles):
                share_data = f.read(16)
                if len(share_data) != 16:
                    raise ValueError("Unexpected end of share file")
                shares.append((idx, share_data))
            
            # 恢复数据块
            block = Shamir.combine(shares)
            # 处理最后一块的填充
            if out_file.tell() + len(block) > file_size:
                block = block[:file_size - out_file.tell()]
            out_file.write(block)
    
    # 关闭所有份额文件
    for f in share_handles:
        f.close()

if __name__ == "__main__":
    # 定义要测试的tot值列表
    tot_values = [80, 90, 100, 110,120,130,140,150]
    # 定义要测试的n值列表
    n_values = [40, 44, 48, 52, 56, 60]
    input_file = '/root/home/secret/Sharefile/test.txt'  # 输入文件路径
    base_output_dir = '/root/home/secret/Share'  # 基础输出目录
    
    # 遍历所有tot值
    for tot in tot_values:
        # 遍历所有n值
        for n in n_values:
            # 跳过无效参数组合（n不能大于tot）
            if n > tot:
                continue
                
            random_id = []
            k = n  # 门限值
            fk = tot - n  # 假份额数量
            
            # 创建以"tot-n"命名的输出目录
            output_dir_name = f"{tot}-{n}"
            output_dir = os.path.join(base_output_dir, output_dir_name)
            
            # 输出当前测试参数
            print(f"\n{'='*50}")
            print(f"开始测试: n = {n}, tot = {tot}, k = {k}, fk = {fk}")
            print(f"输出目录: {output_dir}")
            print(f"{'='*50}")
            
            # 记录开始时间
            t1 = time.time()

            # 分割文件
            try:
                # 生成随机ID
                for i in range(0, n):
                    x = random.randint(1, tot)
                    while x in random_id:
                        x = random.randint(1, tot)
                    random_id.append(x)
                print(f"随机ID: {random_id}")

                # 调用分割函数，传入新的输出目录
                real_shares, fake_shares = split_file(input_file, tot, n, k, output_dir, fk)
                
            except (FileNotFoundError, ValueError) as e:
                print(f"分割文件时出错: {e}")
                continue  # 出错时跳过后续恢复步骤
            
            # 计算并输出分割时间
            t2 = time.time()
            elapsed_split = t2 - t1
            print(f"分割时间: {elapsed_split:.4f}秒")
            
            # ====== 新增的恢复功能 ======
            # 构建真实份额文件路径列表
            share_paths = [os.path.join(output_dir, f'share_{id}.bin') for id in real_shares]
            recovered_file = os.path.join(output_dir, 'recovered.txt')
            
            # 记录恢复开始时间
            t1_recover = time.time()
            
            try:
                print(f"开始恢复文件，使用份额索引: {real_shares}")
                combine_files(share_paths, recovered_file)
            except (FileNotFoundError, ValueError) as e:
                print(f"恢复文件时出错: {e}")
            else:
                # 计算并输出恢复时间
                t2_recover = time.time()
                elapsed_recover = t2_recover - t1_recover
                print(f"恢复时间: {elapsed_recover:.4f}秒")
                
                # 验证恢复文件
                if os.path.exists(recovered_file):
                    original_size = os.path.getsize(input_file)
                    recovered_size = os.path.getsize(recovered_file)
                    
                    if original_size == recovered_size:
                        print("恢复成功: 文件大小一致")
                        # 可选：进一步验证文件内容
                        # with open(input_file, 'rb') as f1, open(recovered_file, 'rb') as f2:
                        #     if f1.read() == f2.read():
                        #         print("文件内容完全一致")
                        #     else:
                        #         print("警告: 文件内容不一致")
                    else:
                        print(f"警告: 文件大小不一致 (原始: {original_size}, 恢复: {recovered_size})")
                else:
                    print("错误: 恢复文件未创建")