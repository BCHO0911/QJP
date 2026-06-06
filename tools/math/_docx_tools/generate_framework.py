"""
Generate high-quality framework diagram for the paper
Using matplotlib with Chinese font support
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Chinese font setup
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

fig = plt.figure(figsize=(14, 10), dpi=200)
ax = fig.add_subplot(111)
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# Color scheme (academic, low saturation)
COLORS = {
    'bg': '#F5F7FA',
    'title_bg': '#2C3E50',
    'layer1': '#3498DB',      # Data preprocessing - blue
    'layer2': '#2980B9',
    'layer1_text': '#FFFFFF',
    'layer2_bg': '#27AE60',    # Feature selection - green
    'layer2_text': '#FFFFFF',
    'layer3_bg': '#E67E22',    # Risk warning - orange
    'layer3_text': '#FFFFFF',
    'layer4_bg': '#8E44AD',    # Intervention optimization - purple
    'layer4_text': '#FFFFFF',
    'box_fill': '#FFFFFF',
    'box_edge': '#BDC3C7',
    'box_text': '#2C3E50',
    'arrow': '#7F8C8D',
    'highlight': '#E74C3C',
    'subtitle': '#34495E',
}

def add_box(ax, x, y, w, h, text, color='#FFFFFF', edge='#2980B9',
            text_color='#2C3E50', fontsize=9, bold=False, roundness=0.03,
            alpha=1.0, ha='center', va='center'):
    """Add a rounded rectangle box with text."""
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0.05,rounding_size={roundness}",
                         facecolor=color, edgecolor=edge, linewidth=1.5,
                         alpha=alpha)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w/2, y + h/2, text, ha=ha, va=va, fontsize=fontsize,
            fontweight=weight, color=text_color, zorder=5)

def add_arrow(ax, x1, y1, x2, y2, color='#7F8C8D', lw=2, style='->',
              connection='arc3,rad=0'):
    """Add an arrow between two points."""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, connectionstyle=connection),
                zorder=4)

def add_text(ax, x, y, text, fontsize=10, color='#2C3E50', bold=False, ha='center'):
    """Add text at a position."""
    ax.text(x, y, text, ha=ha, va='center', fontsize=fontsize,
            fontweight='bold' if bold else 'normal', color=color, zorder=5)

def add_layer_label(ax, x, y, text, color):
    """Add layer label at left side."""
    ax.text(x, y, text, ha='center', va='center', fontsize=11,
            fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=color,
                     edgecolor='none', alpha=0.2))

# ============================================================
# TITLE
# ============================================================
title_box = FancyBboxPatch((3.5, 9.3), 7, 0.6,
                           boxstyle="round,pad=0.1",
                           facecolor=COLORS['title_bg'], edgecolor='none')
ax.add_patch(title_box)
ax.text(7, 9.6, "中老年人群高血脂症风险预警及干预方案优化 — 整体建模框架",
        ha='center', va='center', fontsize=14, fontweight='bold', color='#FFFFFF')

# ============================================================
# LAYER 0: DATA INPUT
# ============================================================
y0 = 8.2
# Data source box
add_box(ax, 0.5, y0, 3, 0.7, "原始数据输入\n1000例样本 · 37维特征 · 9种体质标签",
        color='#ECF0F1', edge='#95A5A6', text_color='#2C3E50', fontsize=8.5)
add_box(ax, 4, y0, 3, 0.7, "数据预处理\n列名校正 → 缺失值检查 → 衍生特征构造 → Z-score标准化",
        color='#ECF0F1', edge='#95A5A6', text_color='#2C3E50', fontsize=8.5)
add_box(ax, 7.5, y0, 3, 0.7, "探索性数据分析\n描述性统计 · 异常值检测 · 相关性分析 · PCA降维",
        color='#ECF0F1', edge='#95A5A6', text_color='#2C3E50', fontsize=8.5)

add_arrow(ax, 3.5, y0+0.35, 4, y0+0.35)
add_arrow(ax, 7, y0+0.35, 7.5, y0+0.35)

# Down arrow from data to problem 1
add_arrow(ax, 9, y0-0.1, 9, y0-0.6, lw=2.5, color=COLORS['layer2_bg'])

# ============================================================
# LAYER 1: PROBLEM 1 - FEATURE SELECTION
# ============================================================
y1 = 6.8
# Layer label
add_layer_label(ax, 13, y1+0.5, "问题一\n特征筛选", COLORS['layer2_bg'])

# Main model box
add_box(ax, 0.5, y1, 5.5, 1.4,
        "问题一：关键指标筛选模型",
        color=COLORS['layer2_bg'], edge=COLORS['layer2_bg'],
        text_color='#FFFFFF', fontsize=10, bold=True)

# Sub-methods
add_box(ax, 0.7, y1+0.15, 2.3, 0.45, "LASSO回归 ($L_1$正则化)",
        color='#FFFFFF', edge='#27AE60', text_color='#2C3E50', fontsize=8)
add_box(ax, 3.2, y1+0.15, 2.6, 0.45, "随机森林特征重要性 (Gini不纯度)",
        color='#FFFFFF', edge='#27AE60', text_color='#2C3E50', fontsize=8)
add_box(ax, 0.7, y1-0.3, 2.3, 0.45, "Spearman秩相关系数",
        color='#FFFFFF', edge='#27AE60', text_color='#2C3E50', fontsize=8)
add_box(ax, 3.2, y1-0.3, 2.6, 0.45, "互信息法 (MI)",
        color='#FFFFFF', edge='#27AE60', text_color='#2C3E50', fontsize=8)

# Method cross mark in center
add_text(ax, 6.45, y1+0.35, "四法交叉\n验证投票", fontsize=8, bold=True, color=COLORS['highlight'])

# Results box
add_box(ax, 7.5, y1+0.35, 3, 0.5, "14项痰湿严重程度关键指标\n10项血脂预警关键指标",
        color='#E8F8F5', edge='#27AE60', text_color='#2C3E50', fontsize=8.5)

add_box(ax, 7.5, y1-0.3, 3, 0.5, "体质贡献度：Logistic回归OR值\n阳虚质OR=1.197(最高) | 血瘀质OR=0.849(保护)",
        color='#E8F8F5', edge='#27AE60', text_color='#2C3E50', fontsize=8.5)

add_arrow(ax, 6, y1+0.35, 6.3, y1+0.35)
add_arrow(ax, 6, y1+0.35, 6.3, y1+0.35)

# Arrows from methods to results
add_arrow(ax, 3.8, y1-0.1, 7.5, y1+0.6, lw=1.5, color='#27AE60', connection='arc3,rad=0.2')
add_arrow(ax, 3.8, y1-0.5, 7.5, y1-0.05, lw=1.5, color='#27AE60', connection='arc3,rad=-0.2')

# Down arrow P1 -> P2
add_arrow(ax, 3.25, y1-0.7, 3.25, y1-1.3, lw=2.5, color=COLORS['layer3_bg'])
add_text(ax, 4.5, y1-0.95, "关键指标 → 分类模型输入特征", fontsize=7.5, color='#7F8C8D')

# ============================================================
# LAYER 2: PROBLEM 2 - RISK WARNING
# ============================================================
y2 = 4.8
add_layer_label(ax, 13, y2+0.6, "问题二\n风险预警", COLORS['layer3_bg'])

add_box(ax, 0.5, y2, 5.5, 1.5,
        "问题二：多维度风险预警模型",
        color=COLORS['layer3_bg'], edge=COLORS['layer3_bg'],
        text_color='#FFFFFF', fontsize=10, bold=True)

# Risk scoring
add_box(ax, 0.7, y2+0.2, 2.3, 0.45,
        "风险评分公式\nS = 10N+40T/100+20(100-A)/100+...",
        color='#FFFFFF', edge='#E67E22', text_color='#2C3E50', fontsize=7.5)
add_box(ax, 3.2, y2+0.2, 2.6, 0.45,
        "三级风险分层\n低(23.2%) | 中(54.0%) | 高(22.8%)",
        color='#FFFFFF', edge='#E67E22', text_color='#2C3E50', fontsize=8)

# Model comparison
add_box(ax, 0.7, y2-0.3, 2.3, 0.45,
        "6分类模型对比(5折CV)\nGBDT最优: Acc=90.80%, F1=0.9034",
        color='#FEF5E7', edge='#E67E22', text_color='#2C3E50', fontsize=8)
add_box(ax, 3.2, y2-0.3, 2.6, 0.45,
        "消融实验验证\n中医体质贡献31.8% | 中西医结合+49.1%",
        color='#FEF5E7', edge='#E67E22', text_color='#2C3E50', fontsize=8)

# Explainability box
add_box(ax, 7, y2+0.1, 3.5, 1.1,
        "可解释性分析\n"
        "- 决策树规则提取 (Top3特征)\n"
        "- SHAP特征贡献分析\n"
        "- 三级风险特征分层阈值\n"
        "- Apriori关联规则 (支持11.5%, 置信88.9%)",
        color='#FEF5E7', edge='#E67E22', text_color='#2C3E50', fontsize=7.5, ha='left')
ax.text(7.15, y2+1.0, "可解释性分析", fontsize=8.5, fontweight='bold', color=COLORS['layer3_bg'])

add_arrow(ax, 6, y2+0.35, 7, y2+0.5, lw=1.5, color='#E67E22')
add_arrow(ax, 6, y2-0.1, 7, y2-0.1, lw=1.5, color='#E67E22')

# Core feature combination box
add_box(ax, 7, y2-0.6, 3.5, 0.5,
        "核心特征组合\n\"痰湿重度+低活动量+TC/TG异常\"",
        color='#FADBD8', edge='#E74C3C', text_color='#C0392B', fontsize=8.5, bold=True)

# Down arrow P2 -> P3
add_arrow(ax, 3.25, y2-0.75, 3.25, y2-1.3, lw=2.5, color=COLORS['layer4_bg'])
add_text(ax, 4.5, y2-1.0, "风险分层 + 特征组合 → 干预目标人群", fontsize=7.5, color='#7F8C8D')

# ============================================================
# LAYER 3: PROBLEM 3 - INTERVENTION OPTIMIZATION
# ============================================================
y3 = 2.9
add_layer_label(ax, 13, y3+0.7, "问题三\n干预优化", COLORS['layer4_bg'])

add_box(ax, 0.5, y3, 5.5, 1.6,
        "问题三：6个月干预方案优化模型",
        color=COLORS['layer4_bg'], edge=COLORS['layer4_bg'],
        text_color='#FFFFFF', fontsize=10, bold=True)

# MILP
add_box(ax, 0.7, y3+0.2, 2.3, 0.5,
        "MILP混合整数规划\n决策变量: L∈{1,2,3} K∈{1,2,3} n∈[1,10]",
        color='#FFFFFF', edge='#8E44AD', text_color='#2C3E50', fontsize=7.5)
add_box(ax, 3.2, y3+0.2, 2.6, 0.5,
        "四重约束条件\n调理分级 | 活动强度 | 经济成本 | 频率限制",
        color='#FFFFFF', edge='#8E44AD', text_color='#2C3E50', fontsize=7.5)

# Solution method
add_box(ax, 0.7, y3-0.35, 2.3, 0.5,
        "枚举法求解 -> 1838个Pareto最优解\n痰湿积分下降模型: T_final = T0(1-r)^6",
        color='#F4ECF7', edge='#8E44AD', text_color='#2C3E50', fontsize=7.5)
add_box(ax, 3.2, y3-0.35, 2.6, 0.5,
        "多目标优化 + AHP层次分析\n效果53.9% > 耐受29.7% > 成本16.4%",
        color='#F4ECF7', edge='#8E44AD', text_color='#2C3E50', fontsize=7.5)

# Results
add_box(ax, 7, y3-0.1, 3.5, 1.2,
        "三套推荐方案（每样本）\n"
        "- A-最省钱: 成本最小化\n"
        "- B-性价比最优: lambda平衡\n"
        "- C-效果优先: ΔT最大化\n\n"
        "278例患者: 平均成本724元 | 平均下降19.3分",
        color='#F4ECF7', edge='#8E44AD', text_color='#2C3E50', fontsize=7.5, ha='left')
ax.text(7.15, y3+0.85, "个性化疗方案推荐", fontsize=8.5, fontweight='bold', color=COLORS['layer4_bg'])

add_arrow(ax, 6, y3+0.1, 7, y3+0.3, lw=1.5, color='#8E44AD')

# ============================================================
# VALIDATION & SENSITIVITY (bottom section)
# ============================================================
y4 = 1.5
add_box(ax, 0.5, y4, 10, 0.8,
        "模型检验与灵敏度分析\n"
        "参数扰动(λ∈[10,30]成本变化<2%) | 特征扰动(去Top3特征F1↓20.1%) | "
        "灰色GM(1,1)预测验证 | Monte Carlo依从性模拟 | Sigmoid平台期模型",
        color='#EBF5FB', edge='#3498DB', text_color='#2C3E50', fontsize=8)

add_arrow(ax, 3.25, y3-0.75, 3.25, y4+0.8, lw=2, color='#3498DB')

# ============================================================
# LEGENDS AND ANNOTATIONS
# ============================================================
# Problem connection arrows on the left
add_text(ax, 0.15, 7.5, "特\n征\n筛\n选", fontsize=7, color='#7F8C8D')
add_text(ax, 0.15, 5.5, "风\n险\n分\n层", fontsize=7, color='#7F8C8D')
add_text(ax, 0.15, 3.6, "干\n预\n优\n化", fontsize=7, color='#7F8C8D')

# Data flow labels
add_text(ax, 1.5, 1.2, "数据流方向：数据预处理 → 特征筛选 → 风险预警 → 干预优化 → 模型检验",
         fontsize=7.5, color='#95A5A6')
add_text(ax, 11.8, 9.2, "图例", fontsize=9, bold=True, color='#2C3E50')
add_box(ax, 11.5, 8.8, 0.3, 0.2, "", color=COLORS['layer2_bg'], edge=COLORS['layer2_bg'])
add_text(ax, 12, 8.9, "特征筛选层", fontsize=7.5, color='#2C3E50', ha='left')
add_box(ax, 11.5, 8.5, 0.3, 0.2, "", color=COLORS['layer3_bg'], edge=COLORS['layer3_bg'])
add_text(ax, 12, 8.6, "风险预警层", fontsize=7.5, color='#2C3E50', ha='left')
add_box(ax, 11.5, 8.2, 0.3, 0.2, "", color=COLORS['layer4_bg'], edge=COLORS['layer4_bg'])
add_text(ax, 12, 8.3, "干预优化层", fontsize=7.5, color='#2C3E50', ha='left')

# ============================================================
# CONCEPTUAL CONNECTION (right side)
# ============================================================
# "治未病" concept box
add_box(ax, 11.2, 5.8, 2.2, 0.8,
        "核心创新\n'治未病'中西医结合\n体质辨识→风险预警\n→干预优化",
        color='#FADBD8', edge='#E74C3C', text_color='#C0392B', fontsize=8, bold=True)

add_arrow(ax, 10.5, 7.2, 11.2, 6.6, lw=1.5, color='#E74C3C', connection='arc3,rad=0.3')

plt.tight_layout()
plt.savefig('d:/framework_diagram.png', dpi=200, bbox_inches='tight',
            facecolor='white', pad_inches=0.3)
print(f"Saved framework_diagram.png")
