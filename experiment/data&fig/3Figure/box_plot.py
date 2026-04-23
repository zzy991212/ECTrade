from datas import *
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.offsetbox import AnchoredText

# Set global font to Times New Roman
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["font.size"] = 27
plt.rcParams['axes.linewidth'] = 2
plt.rcParams['axes.axisbelow'] = True

# Data preparation (keep original order)
data = [
    [WAN_ipfs_500k, WAN_ipfs_5m],  # Case 1
    [MultiWAN_ipfs_500k, MultiWAN_ipfs_5m],  # Case 2
        [LAN_500k_ipfs, LAN_5m_ipfs],  # Case 3
    [MultiLAN_ipfs_500k, MultiLAN_ipfs_5m]  # Case 4
]

# Simplified x-axis labels
network_labels = ["Case 1", "Case 2", "Case 3", "Case 4"]

# Explanation text for each case
case_explanations = [
    "Case 1: WAN Cross-Region (Single-Node)",
    "Case 2: WAN Multi-Region (Multi-Node)",
    "Case 3: WAN Same-Region (Single-Node)",
    "Case 4: LAN Same-Region (Multi-Node)"
]

# Unified color scheme with new colors
color_500k = "#2C7ACD"  # Lighter blue for 500K
color_5m = "#D45A00"     # Darker blue for 5M

# Create figure (keep original size)
fig, ax = plt.subplots(figsize=(12, 8))

# Adjust boxplot parameters for compactness
bar_width = 0.1
spacing = 0.01
x_positions = np.arange(len(network_labels)) * (2 * bar_width + spacing)

# Draw boxplots (hide outliers)
for i, network_data in enumerate(data):
    # 500K data (lighter color)
    ax.boxplot(network_data[0],
               positions=[x_positions[i] - bar_width / 2],
               widths=bar_width,
               patch_artist=True,
               showfliers=False,
               boxprops={'linewidth': 3, 'facecolor': color_500k, 'edgecolor': 'black'},
               medianprops={"color": "black", 'linewidth': 2},
               capprops={"color": "black", 'linewidth': 3},
               whiskerprops={"color": "black", 'linewidth': 3})

    # 5M data (darker color)
    ax.boxplot(network_data[1],
               positions=[x_positions[i] + bar_width / 2],
               widths=bar_width,
               patch_artist=True,
               showfliers=False,
               boxprops={'linewidth': 3, 'facecolor': color_5m, 'edgecolor': 'black'},
               medianprops={"color": "black", 'linewidth': 2},
               capprops={"color": "black", 'linewidth': 3},
               whiskerprops={"color": "black", 'linewidth': 3})

# Axis settings
ax.set_xticks(x_positions)
ax.set_xticklabels(network_labels, size=27, fontweight='normal')
ax.set_yscale('log')
plt.yticks(size=27, fontweight='normal')
ax.set_xlabel('Network Condition', size=27, weight='bold')  # Changed from 'Network Type'
ax.set_ylabel('Time (ms)', size=27, weight='bold')

# Add case explanations in upper right
explanation_text = "\n".join(case_explanations)
anchored_text = AnchoredText(explanation_text,
                           loc='upper right',
                           prop={'family': 'Times New Roman', 'size': 27},
                           frameon=True)
anchored_text.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
ax.add_artist(anchored_text)

# Create simplified legend (just showing 500K vs 5M)
legend_elements = [
    Patch(facecolor=color_500k, edgecolor='black', label='500K'),
    Patch(facecolor=color_5m, edgecolor='black', label='5M')
]

# Place legend in lower left
legend = ax.legend(handles=legend_elements,
                   loc='lower left',
                   prop={'family': 'Times New Roman', 'size': 25, 'weight': 'normal'},
                   frameon=True)
for text in legend.get_texts():
    text.set_fontweight('bold')
legend.get_frame().set_linewidth(1.0)
legend.get_frame().set_edgecolor('black')

# Custom grid lines (only horizontal)
ax.grid(True, which="major", axis='y', linestyle='--', alpha=0.3)

# Adjust layout
plt.xlim(min(x_positions) - bar_width*1.2, max(x_positions) + bar_width*1.2)
# plt.ylim(0,50000)
plt.tight_layout()
plt.savefig('box_new.svg', bbox_inches='tight',dpi=300, transparent=True)
plt.show()