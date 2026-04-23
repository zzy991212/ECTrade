import matplotlib.pyplot as plt
import numpy as np
from datas import *

# 设置全局样式
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 27
plt.rcParams['axes.linewidth'] = 2
plt.rcParams['axes.axisbelow'] = True

# 转换为毫秒（乘以1000）
ourplan_5m_ms = [x * 1000 for x in ourplan_5m]
ourplan_500k_ms = [x * 1000 for x in ourplan_500k]
fairswap_5m_ms = [x * 1000 for x in fairswap_5m]
fairswap_500k_ms = [x * 1000 for x in fairswap_500k]
nrdt_5m_ms = [x * 1000 for x in nrdt_5m]
nrdt_500k_ms = [x * 1000 for x in nrdt_500k]

# 创建画布 - 调整为10:6比例
fig, ax = plt.subplots(figsize=(10, 6))

# 创建x轴值（1到100）
x_values = range(1, 101)

color_sercretrade = "#2C7ACD"

color_fairswap = "#D45A00"

color_nrdt = "#4BA97A"


# 绘制其他线条（zorder较低）

line1 = ax.plot(x_values, ourplan_500k_ms,
                label='SECRETrade 500K', linestyle='-', color=color_sercretrade, linewidth=7, zorder=7)
ax.fill_between(x_values, 0, ourplan_500k_ms, color=color_sercretrade, alpha=0.1, zorder=7)

line2 = ax.plot(x_values, ourplan_5m_ms,
                label='SECRETrade 5M', linestyle='dotted', color=color_sercretrade, linewidth=7, zorder=8)
ax.fill_between(x_values, 0, ourplan_5m_ms, color=color_sercretrade, alpha=0.1, zorder=8)
line3 = ax.plot(x_values, fairswap_500k_ms,
                label='FairSwap 500K', linestyle='-', color=color_fairswap, linewidth=5, zorder=3)
ax.fill_between(x_values, 0, fairswap_500k_ms, color=color_fairswap, alpha=0.1, zorder=3)

line4 = ax.plot(x_values, fairswap_5m_ms,
                label='FairSwap 5M', linestyle='dotted', color=color_fairswap, linewidth=5, zorder=4)
ax.fill_between(x_values, 0, fairswap_5m_ms, color=color_fairswap, alpha=0.1, zorder=4)

line5 = ax.plot(x_values, nrdt_500k_ms,
                label='NRDT 500K', linestyle='-', color=color_nrdt, linewidth=5, zorder=5)
ax.fill_between(x_values, 0, nrdt_500k_ms, color=color_nrdt, alpha=0.1, zorder=5)

line6 = ax.plot(x_values, nrdt_5m_ms,
                label='NRDT 5M', linestyle='dotted', color=color_nrdt, linewidth=5, zorder=6)
ax.fill_between(x_values, 0, nrdt_5m_ms, color=color_nrdt, alpha=0.1, zorder=6)

# 添加标签
ax.set_xlabel('Number of Trades', fontsize=27, fontweight="bold")
ax.set_ylabel('Time (ms)', fontsize=27, fontweight="bold")

# 设置对数坐标轴并包含0
ax.set_yscale('log')

# 设置y轴范围（对数坐标不能直接包含0，所以设置一个很小的值代替0）
min_nonzero = min([min(lst) for lst in [ourplan_5m_ms, ourplan_500k_ms, fairswap_5m_ms,
                                      fairswap_500k_ms, nrdt_5m_ms, nrdt_500k_ms] if min(lst) > 0])
ax.set_ylim(min_nonzero, max([max(lst)*1.8 for lst in [ourplan_5m_ms, ourplan_500k_ms, fairswap_5m_ms,
                                                       fairswap_500k_ms, nrdt_5m_ms, nrdt_500k_ms]]))

# 自定义对数刻度
from matplotlib.ticker import LogFormatterSciNotation
class CustomLogFormatter(LogFormatterSciNotation):
    def __call__(self, x, pos=None):
        if x < 1e-10:  # 处理接近0的情况
            return '0'
        exponent = int(np.log10(x))
        if exponent == 1:
            return '10'
        elif exponent == 0:
            return '1'
        else:
            return f'10$^\mathdefault{{{exponent}}}$'

formatter = CustomLogFormatter(labelOnlyBase=True)
ax.yaxis.set_major_formatter(formatter)

# 设置刻度位置为10^1, 10^2, 10^3,...
from matplotlib.ticker import LogLocator
ax.yaxis.set_major_locator(LogLocator(base=10, numticks=15))

# 设置图例（调整位置和列数）
# legend = ax.legend(fontsize=16.6, framealpha=1, loc='upper center',
#                   bbox_to_anchor=(0.6, 1.22),
#                   ncol=3,
#                   facecolor='white',
#                   edgecolor='black')

# 加粗图例中的线条宽度
# for line in legend.get_lines():
#     line.set_linewidth(4)

# # 设置图例字体加粗
# for text in legend.get_texts():
#     text.set_fontweight('bold')

# 调整x轴范围 - 精确从1到100
ax.set_xlim(1, 100)

# 网格线
ax.grid(True, linestyle='--', alpha=0.6, which='major', axis='both')

# 调整x轴刻度（从0到100，步长为10）
ax.set_xticks([1] + list(np.arange(10, 101, 10)))

# 保存为PDF（矢量图）
plt.savefig(f'v2-{LorW}.pdf', bbox_inches='tight', dpi=300)
plt.savefig(f'Bold-{LorW}.svg', bbox_inches='tight', dpi=300)

# 显示图形
plt.tight_layout()
# plt.show()