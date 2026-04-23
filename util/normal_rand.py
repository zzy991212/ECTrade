import random
import math

def main():
    # 获取用户输入的随机数数量
    x = int(input("请输入要生成的随机数数量: "))
    
    # 生成x个标准正态分布的随机数
    random_numbers = []
    for _ in range(x):
        # 使用Box-Muller变换生成标准正态分布随机数
        u1 = random.random()
        u2 = random.random()
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        random_numbers.append(z0)
    
    # 统计落在(-1, 1)区间之外的数字
    count_outside = 0
    for num in random_numbers:
        if abs(num) >= 1:  # 绝对值大于等于1表示在68%区间外
            count_outside += 1
    
    # 计算实际比例
    actual_percentage = (count_outside / x) * 100
    
    # 打印结果
    print(f"生成的随机数总数: {x}")
    print(f"落在±1标准差区间外的数字数量: {count_outside}")
    print(f"理论比例应为32%，实际比例: {actual_percentage:.2f}%")

if __name__ == "__main__":
    main()