import matplotlib.pyplot as plt
import numpy as np
from datas import n, N, g_1_spl, g_1_rec, g_2_spl, g_2_rec, g_3_spl, g_3_rec, g_4_spl, g_4_rec, g_5_spl, g_5_rec
from matplotlib.lines import Line2D

# Set global style
plt.rcParams.update({
    'pdf.fonttype': 42,
    'font.family': 'Times New Roman',
    'font.size': 27,
    'mathtext.fontset': 'custom',  # 使用自定义数学字体
    'mathtext.rm': 'Times New Roman',  # 常规字体
    'axes.linewidth': 2.0,
    'axes.axisbelow': True,
    'lines.linewidth': 2.8,
    'grid.alpha': 0.3,
    'lines.markersize': 12,
    'lines.markeredgewidth': 1.2,
    'xtick.labelsize': 27,
    'ytick.labelsize': 27,
    'axes.labelsize': 27,
    'legend.fontsize': 24,  # Slightly smaller font for legend
})

# Create flatter subplots (REC on top, SPL at bottom)
fig, (ax2, ax1) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
plt.subplots_adjust(hspace=0.05)

# Select only N=100,120,140 (indices 2,4,6)
selected_n_indices = [2, 4, 6]
selected_N = [N[i] for i in selected_n_indices]

def convert_to_ms(data):
    return [[x * 1000 for x in row] for row in data]

groups_spl = [convert_to_ms(g) for g in [g_1_spl, g_2_spl, g_3_spl, g_4_spl, g_5_spl]]
groups_rec = [convert_to_ms(g) for g in [g_1_rec, g_2_rec, g_3_rec, g_4_rec, g_5_rec]]

def calculate_ranges(groups, n_indices):
    min_data = []; max_data = []; avg_data = []
    for n_idx in n_indices:
        point_min = []; point_max = []; point_avg = []
        for point_idx in range(len(n)):
            values = [group[point_idx][n_idx] for group in groups]
            point_min.append(min(values))
            point_max.append(max(values))
            point_avg.append(sum(values) / len(groups))
        min_data.append(point_min)
        max_data.append(point_max)
        avg_data.append(point_avg)
    return min_data, max_data, avg_data

min_spl, max_spl, avg_spl = calculate_ranges(groups_spl, selected_n_indices)
min_rec, max_rec, avg_rec = calculate_ranges(groups_rec, selected_n_indices)

# Calculate tight y-axis limits
def get_tight_limits(values, padding=0.05):
    vmin, vmax = min(values), max(values)
    span = vmax - vmin
    return max(0, vmin - padding * span), vmax + padding * span

y_min_spl, y_max_spl = get_tight_limits(np.concatenate(min_spl + max_spl))
y_min_rec, y_max_rec = get_tight_limits(np.concatenate(min_rec + max_rec))

x_ticks = n
x_tick_labels = [str(x) for x in n]

# Calculate x-axis limits with padding
x_padding = (max(n) - min(n)) * 0.05  # 5% padding on each side
x_min = min(n) - x_padding
x_max = max(n) + x_padding

# Plotting settings (3 groups only)
colors = ['#ff7f0e', '#2ca02c', '#d62728']  # Orange, Green, Red
markers = ['s', '^', 'D']  # Square, Triangle, Diamond

# Plot REC data (TOP PLOT)
lines = []
for i, (rec_avg, rec_min, rec_max) in enumerate(zip(avg_rec, min_rec, max_rec)):
    line, = ax2.plot(x_ticks, rec_avg,
                     linestyle='--', color=colors[i], alpha=0.9,
                     marker=markers[i], markevery=1, markersize=12,
                     markeredgecolor='k', markeredgewidth=1.2)
    lines.append(line)
    ax2.fill_between(x_ticks, rec_min, rec_max, color=colors[i], alpha=0.15)

# Plot SPL data (BOTTOM PLOT)
for i, (spl_avg, spl_min, spl_max) in enumerate(zip(avg_spl, min_spl, max_spl)):
    ax1.plot(x_ticks, spl_avg,
             linestyle='-', color=colors[i], alpha=0.9,
             marker=markers[i], markevery=1, markersize=12,
             markeredgecolor='k', markeredgewidth=1.2)
    ax1.fill_between(x_ticks, spl_min, spl_max, color=colors[i], alpha=0.15)

# Configure axes
for ax in [ax1, ax2]:
    ax.set_xlim(x_min, x_max)  # Set x-limits with padding
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_tick_labels)
    ax.grid(True, which='major', linestyle='--', linewidth=0.8)
    ax.grid(True, which='minor', linestyle=':', linewidth=0.5, alpha=0.3)
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(2.0)

# Set y-axis limits
ax2.set_ylim(y_min_rec, y_max_rec)
ax1.set_ylim(y_min_spl, y_max_spl)

# Modify y-axis ticks (show /1000)
for ax in [ax1, ax2]:
    yticks = ax.get_yticks()
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"{int(y / 1000)}" if y >= 1000 else f"{y / 1000:.1f}" for y in yticks])

# Add combined ylabel
fig.text(0, 0.5, 'Time (ms)', va='center', rotation='vertical', fontweight='bold')

# Remove individual ylabels
ax1.set_ylabel('')
ax2.set_ylabel('')

# Set xlabel
ax1.set_xlabel('Number of genuine shares', fontweight='bold', labelpad=10)

# Add ×10³ ONLY to top plot (REC)
ax2.text(0.02, 1.02, r'$\times10^3$', transform=ax2.transAxes,
         fontsize=27, va='bottom', ha='left', font='Times New Roman')

legend_elements = [
    Line2D([0], [0], linestyle='-', color=colors[0], lw=2.8, marker=markers[0],
           markeredgecolor='k', markersize=12, label=f'N={selected_N[0]}'),
    Line2D([0], [0], linestyle='-', color=colors[1], lw=2.8, marker=markers[1],
           markeredgecolor='k', markersize=12, label=f'N={selected_N[1]}'),
    Line2D([0], [0], linestyle='-', color=colors[2], lw=2.8, marker=markers[2],
           markeredgecolor='k', markersize=12, label=f'N={selected_N[2]}'),

    Line2D([0], [0], linestyle='-', color='black', lw=2.8,
           markeredgecolor='k', markersize=12, label=f'Split & Obfuscate'),
    Line2D([0], [0], linestyle='--', color='black', lw=2.8,
           markeredgecolor='k', markersize=12, label=f'Reconstruct')
]

# Create legend in top-left corner of ax2
legend = ax2.legend(handles=legend_elements,
                    loc='upper left',
                    ncol=2,
                    frameon=False,
                    bbox_to_anchor=(0.02, 1.02),
                    handlelength=2.0,
                    columnspacing=1.0,
                    handletextpad=0.5,
                    prop={'weight': 'bold'})

plt.tight_layout()
plt.savefig('time_comparison_split_final.svg', bbox_inches='tight', dpi=300, transparent=True)
plt.savefig('time_comparison_split_final.pdf', bbox_inches='tight', dpi=300, transparent=True)

plt.show()