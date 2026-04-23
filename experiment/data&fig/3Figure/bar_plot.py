import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LogFormatterSciNotation

# Custom formatter to display 10^0 as 1 but keep others in scientific notation
class CustomLogFormatter(LogFormatterSciNotation):
    def __call__(self, x, pos=None):
        if round(x) == 1:  # Only modify 10^0 case
            return '1'
        return super().__call__(x, pos)  # Keep default for others

# Set the style parameters
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 27
plt.rcParams['axes.linewidth'] = 2
plt.rcParams['axes.axisbelow'] = True

# Data sizes and protocol names (in new order)
data_sizes = ['100 KB', '500 KB', '1 MB', '5 MB', '10 MB', '50 MB']
protocols = ['EcoTrade', 'FairSwap', 'NRDT']  # Reordered protocol names with correct capitalization

# Data for each protocol (converted to milliseconds) - reordered to match new protocol order
# Assuming we have multiple measurements for each protocol to calculate error bars
SECRETrade_data = np.array([
    [0.00011301, 7.84397E-05, 8.51154E-05, 7.82013E-05, 8.24928E-05, 8.10623E-05],
    [0.00011500, 7.85397E-05, 8.52154E-05, 7.83013E-05, 8.25928E-05, 8.11623E-05],
    [0.00011201, 7.83397E-05, 8.50154E-05, 7.81013E-05, 8.23928E-05, 8.09623E-05]
]) * 1000

fairswap_data = np.array([
    [6.696939468 * 0.001, 34.01827812 * 0.001, 69.67568398 * 0.001, 473.1936455 * 0.001, 1226.964474 * 0.001, 26557.57236 * 0.001],
    [6.706939468 * 0.001, 34.02827812 * 0.001, 69.68568398 * 0.001, 473.2036455 * 0.001, 1226.974474 * 0.001, 26557.58236 * 0.001],
    [6.686939468 * 0.001, 34.00827812 * 0.001, 69.66568398 * 0.001, 473.1836455 * 0.001, 1226.954474 * 0.001, 26557.56236 * 0.001]
]) * 1000

infocom_data = np.array([
    [0.001781463623046875, 0.0031890869140625, 0.01001882553100586, 0.03231620788574219, 0.06871604919433594, 0.3513190746307373],
    [0.001791463623046875, 0.0031990869140625, 0.01002882553100586, 0.03232620788574219, 0.06872604919433594, 0.3513290746307373],
    [0.001771463623046875, 0.0031790869140625, 0.01000882553100586, 0.03230620788574219, 0.06870604919433594, 0.3513090746307373]
]) * 1000

# Calculate means and standard deviations for error bars
SECRETrade_mean = np.mean(SECRETrade_data, axis=0)
SECRETrade_std = np.std(SECRETrade_data, axis=0)

fairswap_mean = np.mean(fairswap_data, axis=0)
fairswap_std = np.std(fairswap_data, axis=0)

infocom_mean = np.mean(infocom_data, axis=0)
infocom_std = np.std(infocom_data, axis=0)

# Combine all data in new order
all_means = [SECRETrade_mean, fairswap_mean, infocom_mean]
all_stds = [SECRETrade_std, fairswap_std, infocom_std]

# Create figure with adjusted size
fig, ax = plt.subplots(figsize=(12, 8))

# Set bar parameters
bar_width = 0.3
index = np.arange(len(data_sizes))
colors = ['#2C7ACD', '#D45A00', '#4BA97A']  # Original color order maintained
# h = ['-', '+', '|']

# Create bars for each protocol with error bars and thicker borders
for i, protocol in enumerate(protocols):
    bars = ax.bar(index + i * bar_width, all_means[i], bar_width,
                 label=protocol, color=colors[i], edgecolor='black',
                 linewidth=4,  # Thicker border
                 yerr=all_stds[i],  # Add error bars
                 capsize=5)  # Add caps to error bars

# Set labels and ticks
ax.set_xlabel('Source Data Size', fontweight='bold', fontsize=27)
ax.set_ylabel('Time (ms)', fontweight='bold', fontsize=27)
ax.set_xticks(index + bar_width)
ax.set_xticklabels(data_sizes, fontweight='normal', fontsize=20)

# Set logarithmic scale for y-axis with adjusted range
ax.set_yscale('log')
ax.set_ylim(1e-2, 1e5)  # Adjusted range for milliseconds

# Apply custom formatter to y-axis
ax.yaxis.set_major_formatter(CustomLogFormatter())

# Customize grid - only horizontal lines
ax.grid(True, which="major", axis='y', ls="--", alpha=0.3)
ax.tick_params(axis='both', which='major', width=1.5, length=4, labelsize=27)

# Create legend with proper formatting
legend = ax.legend(loc='upper left', bbox_to_anchor=(0, 1),
                  ncol=1, prop={'family': 'Times New Roman',
                               'size': 27,
                               'weight': 'bold'},
                  framealpha=1, edgecolor='black')

# Adjust layout to prevent clipping
plt.tight_layout()

# Save
plt.savefig('bold-bar-0801.svg',
            bbox_inches='tight', dpi=300, transparent=True)
# plt.savefig('protocol_comparison_with_error_bars.pdf',
#             bbox_inches='tight', dpi=300, transparent=True)
plt.show()