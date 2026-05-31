# -*- coding: utf-8 -*-
"""
可视化脚本：为三个问题生成论文级图表
"""
import sys
import os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import rcParams

PROJECT_ROOT = r"d:\GIT\private\数模"
sys.path.insert(0, PROJECT_ROOT)

# 中文字体设置
rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

from src.data_loader import load_data, add_derived_features

FIG_DIR = os.path.join(PROJECT_ROOT, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

print("生成可视化图表...")

# 加载数据
df = load_data()
df = add_derived_features(df)
df_risk = pd.read_csv(os.path.join(PROJECT_ROOT, 'output', 'data_with_risk.csv'))

# ==========================================
# 图1: 体质类型分布
# ==========================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 1a: 体质类型分布
const_counts = df['constitution_type'].value_counts().sort_index()
const_names_map = {1:'平和质',2:'气虚质',3:'阳虚质',4:'阴虚质',5:'痰湿质',6:'湿热质',7:'血瘀质',8:'气郁质',9:'特禀质'}
colors = ['#4CAF50','#FF9800','#2196F3','#9C27B0','#F44336','#FF5722','#795548','#607D8B','#E91E63']
bars = axes[0].bar([const_names_map[k] for k in const_counts.index], const_counts.values, color=colors, edgecolor='white', linewidth=0.5)
for bar, val in zip(bars, const_counts.values):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3, str(val), ha='center', va='bottom', fontsize=10, fontweight='bold')
axes[0].set_title('九种体质类型分布', fontsize=14, fontweight='bold')
axes[0].set_ylabel('人数')
axes[0].tick_params(axis='x', rotation=30)

# 1b: 各体质高血脂发病率
hyper_rates = df.groupby('constitution_type')['hyperlipidemia'].mean()
bars2 = axes[1].bar([const_names_map[k] for k in hyper_rates.index], hyper_rates.values, color='#FF7043', edgecolor='white', linewidth=0.5)
for bar, val in zip(bars2, hyper_rates.values):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, f'{val:.1%}', ha='center', va='bottom', fontsize=10, fontweight='bold')
axes[1].set_title('各体质类型高血脂发病率', fontsize=14, fontweight='bold')
axes[1].set_ylabel('发病率')
axes[1].set_ylim(0, 1.0)
axes[1].tick_params(axis='x', rotation=30)

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'q1_constitution_distribution.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: q1_constitution_distribution.png")

# ==========================================
# 图2: 高血脂预警指标特征重要性
# ==========================================
# 从高到低排列
features_top = ['abnormal_count', 'tg', 'non_hdl', 'uric_acid', 'tc', 'tc_hdl_ratio',
                'tg_abnormal', 'tc_abnormal', 'hdl_c', 'ldl_c']
importances = [0.2515, 0.1316, 0.1289, 0.0536, 0.1019, 0.0700, 0.1148, 0.0400, 0.0148, 0.0293]
sorted_pairs = sorted(zip(importances, features_top), reverse=True)

feature_names_cn = {
    'abnormal_count': '血脂异常项数', 'tg': '甘油三酯(TG)', 'non_hdl': '非HDL胆固醇',
    'uric_acid': '血尿酸', 'tc': '总胆固醇(TC)', 'tc_hdl_ratio': 'TC/HDL比值',
    'tg_abnormal': 'TG异常标志', 'tc_abnormal': 'TC异常标志', 'hdl_c': 'HDL-C', 'ldl_c': 'LDL-C'
}

fig, ax = plt.subplots(figsize=(10, 5))
names = [feature_names_cn.get(f, f) for _, f in sorted_pairs]
vals = [v for v, _ in sorted_pairs]
colors2 = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(vals)))
bars = ax.barh(range(len(vals)), vals, color=colors2, edgecolor='white')
ax.set_yticks(range(len(vals)))
ax.set_yticklabels(names, fontsize=11)
ax.set_xlabel('特征重要性', fontsize=12)
ax.set_title('高血脂风险预警指标重要性排序 (Random Forest)', fontsize=14, fontweight='bold')
for i, v in enumerate(vals):
    ax.text(v + 0.003, i, f'{v:.3f}', va='center', fontsize=10)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'q2_feature_importance.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: q2_feature_importance.png")

# ==========================================
# 图3: 三级风险分布与特征对比
# ==========================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

risk_names = {0: '低风险', 1: '中风险', 2: '高风险'}
risk_colors = ['#4CAF50', '#FF9800', '#F44336']

# 3a: 风险等级饼图
risk_counts = df_risk['risk_level'].value_counts().sort_index()
axes[0, 0].pie(risk_counts.values, labels=[risk_names[k] for k in risk_counts.index],
               autopct='%1.1f%%', colors=risk_colors, textprops={'fontsize': 12})
axes[0, 0].set_title('三级风险等级分布', fontsize=14, fontweight='bold')

# 3b: 痰湿积分箱线图
for level in [0, 1, 2]:
    axes[0, 1].boxplot(df_risk[df_risk['risk_level']==level]['tanshi'],
                       positions=[level], widths=0.5, patch_artist=True,
                       boxprops=dict(facecolor=risk_colors[level], alpha=0.7))
axes[0, 1].set_xticks([0, 1, 2])
axes[0, 1].set_xticklabels(['低风险', '中风险', '高风险'])
axes[0, 1].set_title('各风险等级痰湿积分分布', fontsize=14, fontweight='bold')
axes[0, 1].set_ylabel('痰湿积分')

# 3c: TC箱线图
for level in [0, 1, 2]:
    axes[1, 0].boxplot(df_risk[df_risk['risk_level']==level]['tc'],
                       positions=[level], widths=0.5, patch_artist=True,
                       boxprops=dict(facecolor=risk_colors[level], alpha=0.7))
axes[1, 0].set_xticks([0, 1, 2])
axes[1, 0].set_xticklabels(['低风险', '中风险', '高风险'])
axes[1, 0].set_title('各风险等级总胆固醇(TC)分布', fontsize=14, fontweight='bold')
axes[1, 0].set_ylabel('TC (mmol/L)')

# 3d: 血脂异常数分布
for level in [0, 1, 2]:
    axes[1, 1].hist(df_risk[df_risk['risk_level']==level]['abnormal_count'],
                    bins=range(0, 6), alpha=0.6, label=risk_names[level], color=risk_colors[level])
axes[1, 1].set_xlabel('血脂异常项数')
axes[1, 1].set_ylabel('人数')
axes[1, 1].set_title('各风险等级血脂异常项数分布', fontsize=14, fontweight='bold')
axes[1, 1].legend()
axes[1, 1].set_xticks(range(0, 5))

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'q2_risk_analysis.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: q2_risk_analysis.png")

# ==========================================
# 图4: 决策树规则可视化(简化版)
# ==========================================
fig, ax = plt.subplots(figsize=(12, 6))

# 阈值规则总结
thresholds_data = [
    ['痰湿积分', '< 27', '27-45', '> 45'],
    ['血脂异常数', '≤ 1', '1-2', '≥ 2'],
    ['活动量表总分', '> 52', '42-52', '< 42'],
    ['TC (mmol/L)', '< 5.0', '5.0-6.1', '> 6.1'],
    ['TG (mmol/L)', '< 1.3', '1.3-1.8', '> 1.8'],
    ['TC/HDL比值', '< 3.8', '3.8-4.6', '> 4.6'],
]

col_labels = ['特征', '低风险阈值', '中风险阈值', '高风险阈值']
cell_colors = [['#E8F5E9' for _ in range(4)] for _ in range(len(thresholds_data))]

table = ax.table(cellText=thresholds_data, colLabels=col_labels,
                 cellLoc='center', loc='center',
                 cellColours=cell_colors)
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 1.8)

# Header color
for j in range(4):
    table[0, j].set_facecolor('#1565C0')
    table[0, j].set_text_props(color='white', fontweight='bold')

ax.set_title('三级风险特征分层阈值', fontsize=16, fontweight='bold', pad=20)
ax.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'q2_threshold_table.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: q2_threshold_table.png")

# ==========================================
# 图5: 优化方案结果可视化
# ==========================================
q3_results = pd.read_csv(os.path.join(PROJECT_ROOT, 'output', 'q3_all_solutions.csv'))

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 5a: 成本-效果散点图
act_level_colors = {1: '#4CAF50', 2: '#FF9800', 3: '#F44336'}
for al in [1, 2, 3]:
    sub = q3_results[q3_results['activity_level'] == al]
    axes[0, 0].scatter(sub['total_cost'], sub['total_reduction_points'],
                       c=act_level_colors[al], label=f'{al}级强度', alpha=0.6, s=30)
axes[0, 0].set_xlabel('6个月总成本 (元)')
axes[0, 0].set_ylabel('痰湿积分下降量 (分)')
axes[0, 0].set_title('成本-效果散点图', fontsize=14, fontweight='bold')
axes[0, 0].axhline(y=0, color='gray', linestyle='--', alpha=0.3)
axes[0, 0].axvline(x=2000, color='red', linestyle='--', alpha=0.3, label='成本上限')
axes[0, 0].legend()

# 5b: 调理级别分布
tcm_counts = q3_results['tcm_level'].value_counts().sort_index()
tcm_names = {1: '基础调理(30元/月)', 2: '中度调理(80元/月)', 3: '强化调理(130元/月)'}
bars = axes[0, 1].bar([tcm_names[k] for k in tcm_counts.index], tcm_counts.values,
                       color=['#4CAF50', '#FF9800', '#F44336'], edgecolor='white')
for bar, val in zip(bars, tcm_counts.values):
    axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, str(val),
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
axes[0, 1].set_title('调理级别分布', fontsize=14, fontweight='bold')
axes[0, 1].set_ylabel('人数')

# 5c: 各年龄组方案对比
age_groups = sorted(q3_results['age_group'].unique())
age_costs = [q3_results[q3_results['age_group']==ag]['total_cost'].mean() for ag in age_groups]
age_reds = [q3_results[q3_results['age_group']==ag]['total_reduction_points'].mean() for ag in age_groups]
x = np.arange(len(age_groups))
width = 0.35
bars1 = axes[1, 0].bar(x - width/2, age_costs, width, label='平均成本(元)', color='#2196F3')
ax2 = axes[1, 0].twinx()
bars2 = ax2.bar(x + width/2, age_reds, width, label='平均下降(分)', color='#FF5722')
axes[1, 0].set_xticks(x)
axes[1, 0].set_xticklabels([f'{ag}组' for ag in age_groups])
axes[1, 0].set_ylabel('平均成本 (元)', color='#2196F3')
ax2.set_ylabel('平均下降 (分)', color='#FF5722')
axes[1, 0].set_title('各年龄组干预方案对比', fontsize=14, fontweight='bold')

# 5d: 活动评分区间方案对比
act_intervals = ['低(<40)', '中(40-59)', '高(>=60)']
act_ranges = [(0, 39), (40, 59), (60, 100)]
act_costs = []
act_reds = []
for low, high in act_ranges:
    sub = q3_results[(q3_results['activity_total'] >= low) & (q3_results['activity_total'] <= high)]
    act_costs.append(sub['total_cost'].mean() if len(sub) > 0 else 0)
    act_reds.append(sub['total_reduction_points'].mean() if len(sub) > 0 else 0)

x2 = np.arange(3)
bars3 = axes[1, 1].bar(x2 - width/2, act_costs, width, label='平均成本(元)', color='#4CAF50')
ax3 = axes[1, 1].twinx()
bars4 = ax3.bar(x2 + width/2, act_reds, width, label='平均下降(分)', color='#E91E63')
axes[1, 1].set_xticks(x2)
axes[1, 1].set_xticklabels(act_intervals)
axes[1, 1].set_ylabel('平均成本 (元)', color='#4CAF50')
ax3.set_ylabel('平均下降 (分)', color='#E91E63')
axes[1, 1].set_title('各活动能力区间干预方案对比', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'q3_optimization_results.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: q3_optimization_results.png")

# ==========================================
# 图6: 样本1,2,3方案详情
# ==========================================
sample_ids = [1, 2, 3]
sample_data = []

for sid in sample_ids:
    row_df = q3_results[q3_results['sample_id'] == sid]
    if len(row_df) > 0:
        row = row_df.iloc[0]
        sample_data.append({
            '样本ID': sid,
            '初始痰湿': row['initial_tanshi'],
            '最终痰湿': row['final_tanshi'],
            '下降量': row['total_reduction_points'],
            '调理级别': f"{int(row['tcm_level'])}级",
            '活动强度': f"{int(row['activity_level'])}级",
            '周频次': int(row['sessions_per_week']),
            '总成本': row['total_cost'],
        })

if sample_data:
    sample_df = pd.DataFrame(sample_data)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # 痰湿积分变化柱状图
    x = np.arange(3)
    width = 0.35
    axes[0].bar(x - width/2, [d['初始痰湿'] for d in sample_data], width, label='初始', color='#FF8A65')
    axes[0].bar(x + width/2, [d['最终痰湿'] for d in sample_data], width, label='6个月后', color='#4DB6AC')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f'样本{d["样本ID"]}' for d in sample_data])
    axes[0].set_ylabel('痰湿积分')
    axes[0].set_title('痰湿积分变化', fontsize=14, fontweight='bold')
    axes[0].legend()

    # 方案对比
    for i, d in enumerate(sample_data):
        axes[1].text(0.1, 0.8 - i*0.25, f"样本{d['样本ID']}: 调理{d['调理级别']}, 活动{d['活动强度']}, {d['周频次']}次/周",
                     transform=axes[1].transAxes, fontsize=12, va='top',
                     bbox=dict(boxstyle='round', facecolor=['#E8F5E9','#E3F2FD','#FFF3E0'][i], alpha=0.7))
    axes[1].set_title('最优干预方案', fontsize=14, fontweight='bold')
    axes[1].axis('off')

    # 成本对比
    costs = [d['总成本'] for d in sample_data]
    bars = axes[2].bar(x, costs, color=['#4CAF50', '#2196F3', '#FF9800'], edgecolor='white')
    for bar, d in zip(bars, sample_data):
        axes[2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                    f"{d['总成本']:.0f}元", ha='center', va='bottom', fontsize=11, fontweight='bold')
    axes[2].set_xticks(x)
    axes[2].set_xticklabels([f'样本{d["样本ID"]}' for d in sample_data])
    axes[2].set_ylabel('6个月总成本 (元)')
    axes[2].set_title('干预方案成本对比', fontsize=14, fontweight='bold')
    axes[2].axhline(y=2000, color='red', linestyle='--', alpha=0.5, label='上限2000元')
    axes[2].legend()

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'q3_sample_solutions.png'), dpi=200, bbox_inches='tight')
    plt.close()
    print("  保存: q3_sample_solutions.png")

# ==========================================
# 图7: 相关性热图
# ==========================================
corr_cols = ['tanshi', 'tc', 'tg', 'ldl_c', 'hdl_c', 'glucose', 'uric_acid', 'bmi',
             'activity_total', 'adl_total', 'iadl_total', 'hyperlipidemia']
corr_df = df[corr_cols].corr()

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr_df.values, cmap='RdBu_r', vmin=-1, vmax=1)

corr_names_cn = {
    'tanshi': '痰湿质', 'tc': 'TC', 'tg': 'TG', 'ldl_c': 'LDL-C',
    'hdl_c': 'HDL-C', 'glucose': '血糖', 'uric_acid': '尿酸', 'bmi': 'BMI',
    'activity_total': '活动总分', 'adl_total': 'ADL总分', 'iadl_total': 'IADL总分',
    'hyperlipidemia': '高血脂'
}
labels = [corr_names_cn.get(c, c) for c in corr_cols]

ax.set_xticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels, fontsize=10)

for i in range(len(labels)):
    for j in range(len(labels)):
        val = corr_df.values[i, j]
        color = 'white' if abs(val) > 0.5 else 'black'
        ax.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=8, color=color)

plt.colorbar(im, ax=ax, label='Pearson相关系数')
ax.set_title('指标相关性热图', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'q1_correlation_heatmap.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: q1_correlation_heatmap.png")

print(f"\n所有图表已保存到: {FIG_DIR}/")
print("生成的图表:")
for f in sorted(os.listdir(FIG_DIR)):
    if f.endswith('.png'):
        print(f"  - {f}")
