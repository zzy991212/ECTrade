def generate_binary_string():
    # 创建一个长度为140的列表，初始值全为0
    binary_list = ['0'] * 140
    # 指定需要设置为1的位（注意列表索引从0开始，所以要减1）
    positions = [1, 2, 7, 9, 11, 13, 14, 15, 16, 20, 26, 27, 30, 31, 32, 33, 35, 43, 44, 47, 48, 49, 52, 54, 55, 59, 60, 63, 66, 68, 69, 71, 77, 83, 87, 90, 95, 98, 100, 103, 104, 107, 118, 120, 121, 122, 126, 129, 135, 137, 139, 140]
    # 将指定位置的元素设置为1
    for pos in positions:
        binary_list[pos - 1] = '1'
    # 将列表转换为字符串
    return ''.join(binary_list)

# 生成并打印结果
binary_str = generate_binary_string()
print("生成的140位01字符串:")
print(binary_str)
print("\n字符串长度:", len(binary_str))