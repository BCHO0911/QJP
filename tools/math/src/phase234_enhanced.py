# -*- coding: utf-8 -*-
"""
Phase 2+3+4: Q2增强 + 灰色关联 + PCA + AHP + 全部新图表

包含:
- Phase 2: ROC曲线、混淆矩阵、SVM对比、SHAP可解释、聚类验证
- Phase 3: 灰色关联度分析、PCA、AHP层次分析、消融实验
- Phase 4: 10张新图表生成
"""
import sys
import os
import warnings
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
import json

PROJECT_ROOT = r"d:\GIT\private\数模"
sys.path.insert(0, PROJECT_ROOT)

# 中文字体
rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_curve, auc, confusion_matrix, classification_report,
    roc_auc_score, accuracy_score, f1_score, precision_recall_curve
)
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_selection import mutual_info_classif
from scipy import stats
from scipy.stats import spearmanr

from src.data_loader import load_data, add_derived_features

FIG_DIR = os.path.join(PROJECT_ROOT, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

print("=" * 70)
print("Phase 2+3+4: Q2增强 + 灰色关联 + PCA + AHP + 新图表")
print("=" * 70)

# ==========================================
# 加载数据
# ==========================================
df = load_data()
df = add_derived_features(df)
df_risk = pd.read_csv(os.path.join(PROJECT_ROOT, 'output', 'data_with_risk.csv'))

# 特征集
feature_cols = (
    ['tanshi', 'pinghe', 'qixu', 'yangxu', 'yinxu', 'shire', 'xueyu', 'qiyu', 'tebing'] +
    ['tc', 'tg', 'ldl_c', 'hdl_c', 'glucose', 'uric_acid', 'bmi'] +
    ['adl_total', 'iadl_total', 'activity_total'] +
    ['age_group', 'gender', 'smoking', 'drinking'] +
    ['tc_abnormal', 'tg_abnormal', 'ldl_abnormal', 'hdl_abnormal', 'abnormal_count'] +
    ['tc_hdl_ratio', 'non_hdl'] +
    ['tanshi_x_activity', 'tanshi_x_tc', 'tanshi_x_tg']
)

# 确保衍生特征存在
if 'tanshi_x_activity' not in df.columns:
    df_risk['tanshi_x_activity'] = df_risk['tanshi'] * (100 - df_risk['activity_total']) / 100
if 'tanshi_x_tc' not in df.columns:
    df_risk['tanshi_x_tc'] = df_risk['tanshi'] * df_risk['tc']
if 'tanshi_x_tg' not in df.columns:
    df_risk['tanshi_x_tg'] = df_risk['tanshi'] * df['tg']

X_all = df_risk[feature_cols].values
scaler = StandardScaler()
X_all_scaled = scaler.fit_transform(X_all)

y_hyper = df_risk['hyperlipidemia'].values
y_risk = df_risk['risk_level'].values


# ==========================================
# PHASE 2: Q2增强
# ==========================================
print("\n【Phase 2: Q2模型增强】")
print("-" * 50)

# 2.1 扩展模型对比 (6模型)
print("\n2.1 六模型对比 (5折交叉验证, 三级风险分类):")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

models_phase2 = {
    'GradientBoosting': GradientBoostingClassifier(n_estimators=150, max_depth=5, random_state=42),
    'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
    'DecisionTree': DecisionTreeClassifier(max_depth=6, random_state=42),
    'SVM': SVC(kernel='rbf', C=10, gamma='scale', probability=True, random_state=42),
    'KNN': KNeighborsClassifier(n_neighbors=15, weights='distance', n_jobs=-1),
    'LogisticRegression': LogisticRegression(max_iter=5000, random_state=42, multi_class='multinomial'),
}

model_results = {}
for name, model in models_phase2.items():
    acc = cross_val_score(model, X_all_scaled, y_risk, cv=cv, scoring='accuracy').mean()
    f1 = cross_val_score(model, X_all_scaled, y_risk, cv=cv, scoring='f1_macro').mean()
    model_results[name] = {'accuracy': acc, 'f1_macro': f1}
    print(f"  {name:20s}: Accuracy={acc:.4f}, F1={f1:.4f}")

best_model_name = max(model_results, key=lambda k: model_results[k]['f1_macro'])
print(f"\n  最优: {best_model_name} (F1={model_results[best_model_name]['f1_macro']:.4f})")

# 2.2 训练最优模型用于后续分析
best_model = models_phase2[best_model_name]
best_model.fit(X_all_scaled, y_risk)

# 2.3 ROC曲线 (将三级风险转为二分类: 高风险 vs 非高)
print("\n2.2 ROC曲线分析:")
y_binary = (y_risk == 2).astype(int)  # 高风险=1, 其他=0

# 获取概率
y_proba = best_model.predict_proba(X_all_scaled)[:, 2]  # 高风险概率
fpr, tpr, thresholds = roc_curve(y_binary, y_proba)
roc_auc = auc(fpr, tpr)
print(f"  ROC-AUC (高风险检测): {roc_auc:.4f}")

# 2.4 混淆矩阵
print("\n2.3 混淆矩阵:")
y_pred = best_model.predict(X_all_scaled)
cm = confusion_matrix(y_risk, y_pred)
print(f"  [[{cm[0,0]:3d}, {cm[0,1]:3d}, {cm[0,2]:3d}]  低]")
print(f"   [{cm[1,0]:3d}, {cm[1,1]:3d}, {cm[1,2]:3d}]  中")
print(f"   [{cm[2,0]:3d}, {cm[2,1]:3d}, {cm[2,2]:3d}]] 高")

# 2.5 消融实验
print("\n2.4 消融实验 (去掉中医维度):")
feature_cols_no_tcm = [c for c in feature_cols if c not in
    ['tanshi', 'pinghe', 'qixu', 'yangxu', 'yinxu', 'shire', 'xueyu', 'qiyu', 'tebing',
     'tanshi_x_activity', 'tanshi_x_tc', 'tanshi_x_tg']]

X_no_tcm = df_risk[feature_cols_no_tcm].values
X_no_tcm_scaled = StandardScaler().fit_transform(X_no_tcm)

gb_no_tcm = GradientBoostingClassifier(n_estimators=150, max_depth=5, random_state=42)
acc_full = cross_val_score(best_model, X_all_scaled, y_risk, cv=cv, scoring='accuracy').mean()
acc_no_tcm = cross_val_score(gb_no_tcm, X_no_tcm_scaled, y_risk, cv=cv, scoring='accuracy').mean()
print(f"  全特征(含中医体质): Accuracy={acc_full:.4f}")
print(f"  去中医体质特征:     Accuracy={acc_no_tcm:.4f}")
print(f"  性能下降:           {acc_full - acc_no_tcm:.4f} ({(acc_full-acc_no_tcm)/acc_full*100:.1f}%)")

# 2.6 西医 vs 中西医结合对比
print("\n2.5 纯西医指标 vs 中西医结合:")
feature_cols_western = ['tc', 'tg', 'ldl_c', 'hdl_c', 'glucose', 'uric_acid', 'bmi',
                        'tc_abnormal', 'tg_abnormal', 'ldl_abnormal', 'hdl_abnormal',
                        'abnormal_count', 'tc_hdl_ratio', 'non_hdl']
X_western = df_risk[feature_cols_western].values
X_western_scaled = StandardScaler().fit_transform(X_western)

gb_western = GradientBoostingClassifier(n_estimators=150, max_depth=5, random_state=42)
acc_western = cross_val_score(gb_western, X_western_scaled, y_risk, cv=cv, scoring='accuracy').mean()
print(f"  纯西医指标:          Accuracy={acc_western:.4f}")
print(f"  中西医结合:          Accuracy={acc_full:.4f}")
print(f"  中西医结合提升:      {acc_full - acc_western:.4f} ({(acc_full-acc_western)/acc_western*100:.1f}%)")


# ==========================================
# PHASE 3: 灰色关联 + PCA + AHP
# ==========================================
print("\n\n【Phase 3: 灰色关联 + PCA + AHP】")
print("-" * 50)

# 3.1 灰色关联度分析
print("\n3.1 灰色关联度分析 (各指标 vs 痰湿质积分):")

def grey_relational_grade(reference, comparison):
    """计算单个指标的灰色关联度"""
    ref = np.array(reference, dtype=float)
    comp = np.array(comparison, dtype=float)

    # 标准化 (初值化)
    ref_norm = ref / ref[0] if ref[0] != 0 else ref - ref.min() + 1
    comp_norm = comp / comp[0] if comp[0] != 0 else comp - comp.min() + 1

    # 差序列
    diff = np.abs(ref_norm - comp_norm)
    max_diff = diff.max()
    min_diff = diff.min()

    # 关联系数 (ρ=0.5)
    rho = 0.5
    ksi = (min_diff + rho * max_diff) / (diff + rho * max_diff)

    return ksi.mean()

grey_features = ['tc', 'tg', 'ldl_c', 'hdl_c', 'glucose', 'uric_acid', 'bmi',
                 'activity_total', 'adl_total', 'iadl_total', 'age_group', 'gender']

grey_results = []
for feat in grey_features:
    # 将数据排序后计算(灰色系统通常用于序列)
    # 这里我们用全体样本的平均关联度
    ref = df_risk['tanshi'].values
    comp = df[feat].values
    grade = grey_relational_grade(ref, comp)
    grey_results.append({'feature': feat, 'grade': grade})

grey_df = pd.DataFrame(grey_results).sort_values('grade', ascending=False)
for _, row in grey_df.iterrows():
    print(f"  {row['feature']:20s}: 关联度={row['grade']:.4f}")

# 3.2 PCA
print("\n3.2 主成分分析(PCA) - 血脂+代谢指标:")
pca_features = ['tc', 'tg', 'ldl_c', 'hdl_c', 'glucose', 'uric_acid', 'bmi']
X_pca = df_risk[pca_features].values
X_pca_scaled = StandardScaler().fit_transform(X_pca)

pca = PCA()
pca.fit(X_pca_scaled)
pca_components = pca.components_
pca_explained = pca.explained_variance_ratio_

print("  方差解释比:")
for i, ev in enumerate(pca_explained):
    print(f"    PC{i+1}: {ev:.4f} (累计: {pca_explained[:i+1].sum():.4f})")

print("\n  主成分载荷矩阵:")
for i, feat in enumerate(pca_features):
    print(f"    {feat:15s}: PC1={pca_components[0,i]:+.3f}, PC2={pca_components[1,i]:+.3f}")

# 3.3 AHP层次分析 - 确定Q3优化目标权重
print("\n3.3 AHP层次分析法 - 确定成本-效果权重:")

# 判断矩阵 (成本 vs 效果)
# 专家判断: 效果比成本稍微重要 (3)
ahp_matrix = np.array([
    [1, 1/3],  # 成本 vs 效果
    [3, 1],    # 效果 vs 成本
])

criteria = ['经济成本', '痰湿下降效果']

# 计算权重
col_sums = ahp_matrix.sum(axis=0)
normalized = ahp_matrix / col_sums
weights = normalized.mean(axis=1)

print("  判断矩阵:")
for i, c1 in enumerate(criteria):
    row_str = f"    {c1}: "
    for j, c2 in enumerate(criteria):
        row_str += f"{ahp_matrix[i,j]:.1f}  "
    print(row_str)

print(f"  权重: 经济成本={weights[0]:.3f}, 痰湿下降效果={weights[1]:.3f}")

# 一致性检验
lambda_max = (ahp_matrix @ weights / weights).mean()
CI = (lambda_max - len(criteria)) / (len(criteria) - 1)
RI_2 = 0.00  # n=2时RI=0
CR = CI / RI_2 if RI_2 > 0 else 0
print(f"  一致性检验: λ_max={lambda_max:.4f}, CI={CI:.4f}, CR={CR:.4f} (CR<0.1通过)")

# 增加第三维度: 患者耐受度
ahp_3 = np.array([
    [1, 1/3, 1/2],   # 成本
    [3, 1, 2],       # 效果
    [2, 1/2, 1],     # 耐受度
])
criteria_3 = ['经济成本', '痰湿下降效果', '患者耐受度']

col_sums_3 = ahp_3.sum(axis=0)
normalized_3 = ahp_3 / col_sums_3
weights_3 = normalized_3.mean(axis=1)

lambda_max_3 = (ahp_3 @ weights_3 / weights_3).mean()
CI_3 = (lambda_max_3 - 3) / 2
RI_3 = 0.58
CR_3 = CI_3 / RI_3

print(f"\n  三维判断矩阵:")
print(f"  权重: 经济成本={weights_3[0]:.3f}, 效果={weights_3[1]:.3f}, 耐受度={weights_3[2]:.3f}")
print(f"  一致性: λ_max={lambda_max_3:.4f}, CI={CI_3:.4f}, CR={CR_3:.4f} {'通过' if CR_3 < 0.1 else '未通过'}")


# ==========================================
# PHASE 4: 生成全部新图表
# ==========================================
print("\n\n【Phase 4: 生成新图表】")
print("-" * 50)

# 图8: ROC曲线
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(fpr, tpr, color='#FF6B6B', lw=2.5, label=f'ROC-AUC = {roc_auc:.4f}')
ax.plot([0, 1], [0, 1], color='gray', lw=1, linestyle='--', label='随机分类器')
ax.fill_between(fpr, tpr, alpha=0.15, color='#FF6B6B')
ax.set_xlim([0, 1])
ax.set_ylim([0, 1.05])
ax.set_xlabel('假阳性率 (FPR)', fontsize=13)
ax.set_ylabel('真阳性率 (TPR)', fontsize=13)
ax.set_title('高风险检测ROC曲线', fontsize=15, fontweight='bold')
ax.legend(loc='lower right', fontsize=12)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'roc_curve.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: roc_curve.png")

# 图9: 混淆矩阵热图
fig, ax = plt.subplots(figsize=(7, 5.5))
im = ax.imshow(cm, cmap='Blues', aspect='auto')
risk_labels_display = ['低风险', '中风险', '高风险']
ax.set_xticks(range(3))
ax.set_yticks(range(3))
ax.set_xticklabels(risk_labels_display, fontsize=12)
ax.set_yticklabels(risk_labels_display, fontsize=12)
ax.set_xlabel('预测标签', fontsize=13)
ax.set_ylabel('真实标签', fontsize=13)
ax.set_title('风险分级混淆矩阵', fontsize=15, fontweight='bold')

for i in range(3):
    for j in range(3):
        color = 'white' if cm[i, j] > cm.max() / 2 else 'black'
        ax.text(j, i, str(cm[i, j]), ha='center', va='center', fontsize=14,
                fontweight='bold', color=color)

# 添加准确率
acc_overall = accuracy_score(y_risk, y_pred)
ax.text(0.5, -0.15, f'总体准确率: {acc_overall:.1%}', ha='center', transform=ax.transAxes,
        fontsize=13, fontweight='bold', color='#1565C0')

plt.colorbar(im, ax=ax, label='人数')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'confusion_matrix.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: confusion_matrix.png")

# 图10: SHAP-like 特征贡献图（基于GB feature_importances）
gb_full = GradientBoostingClassifier(n_estimators=150, max_depth=5, random_state=42)
gb_full.fit(X_all_scaled, y_risk)

# 平均特征重要性
avg_importance = gb_full.feature_importances_
imp_df = pd.DataFrame({'feature': feature_cols, 'importance': avg_importance}).sort_values('importance', ascending=True)

# Top 15
imp_top15 = imp_df.tail(15)

feature_names_cn_map = {
    'tanshi_x_activity': '痰湿×活动交互', 'abnormal_count': '血脂异常项数',
    'tanshi_x_tc': '痰湿×TC交互', 'tanshi': '痰湿质积分', 'tanshi_x_tg': '痰湿×TG交互',
    'tc': '总胆固醇(TC)', 'tg': '甘油三酯(TG)', 'non_hdl': '非HDL胆固醇',
    'tc_hdl_ratio': 'TC/HDL比值', 'uric_acid': '血尿酸', 'bmi': 'BMI',
    'ldl_c': 'LDL-C', 'hdl_c': 'HDL-C', 'glucose': '空腹血糖',
    'activity_total': '活动量表总分', 'adl_total': 'ADL总分', 'iadl_total': 'IADL总分',
    'tc_abnormal': 'TC异常标志', 'tg_abnormal': 'TG异常标志', 'ldl_abnormal': 'LDL异常',
    'hdl_abnormal': 'HDL异常', 'age_group': '年龄组', 'gender': '性别',
    'smoking': '吸烟史', 'drinking': '饮酒史',
    'pinghe': '平和质', 'qixu': '气虚质', 'yangxu': '阳虚质', 'yinxu': '阴虚质',
    'shire': '湿热质', 'xueyu': '血瘀质', 'qiyu': '气郁质', 'tebing': '特禀质',
}

fig, ax = plt.subplots(figsize=(10, 6))
names_cn = [feature_names_cn_map.get(f, f) for f in imp_top15['feature'].values]
colors_shap = plt.cm.viridis(np.linspace(0.3, 0.9, len(names_cn)))
ax.barh(range(len(names_cn)), imp_top15['importance'].values, color=colors_shap, edgecolor='white')
ax.set_yticks(range(len(names_cn)))
ax.set_yticklabels(names_cn, fontsize=11)
ax.set_xlabel('特征重要性 (GradientBoosting)', fontsize=12)
ax.set_title('特征贡献排序 (SHAP替代)', fontsize=14, fontweight='bold')
for i, v in enumerate(imp_top15['importance'].values):
    ax.text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'shap_feature_importance.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: shap_feature_importance.png")

# 图11: Pareto前沿散点图 (样本1为例)
pareto_data = pd.read_csv(os.path.join(PROJECT_ROOT, 'output', 'q3_pareto_data.csv'))
sample1_pareto = pareto_data[pareto_data['sample_id'] == 1]

fig, ax = plt.subplots(figsize=(9, 6))
# 全部可行方案(散点)
sample1_all = pd.read_csv(os.path.join(PROJECT_ROOT, 'output', 'q3_upgraded_solutions.csv'))
# 对于样本1的全部方案 - 需要从原始枚举中提取
# 简化: 用pareto数据展示
all_sids = pareto_data['sample_id'].unique()

# 绘制所有患者的Pareto点
for sid in [1, 2, 3]:
    sub = pareto_data[pareto_data['sample_id'] == sid]
    if len(sub) > 0:
        ax.scatter(sub['total_cost'], sub['total_reduction'],
                   s=40, alpha=0.7, label=f'样本{sid} Pareto前沿',
                   edgecolors='white', linewidth=0.5)
        # 连线
        ax.plot(sub['total_cost'], sub['total_reduction'], alpha=0.3, linewidth=1)

ax.set_xlabel('6个月总成本 (元)', fontsize=13)
ax.set_ylabel('痰湿积分下降量 (分)', fontsize=13)
ax.set_title('多目标Pareto前沿 (样本1/2/3)', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
ax.axvline(x=2000, color='red', linestyle='--', alpha=0.5, label='成本上限')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'pareto_frontier.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: pareto_frontier.png")

# 图12: PCA降维聚类散点图
pca_2d = PCA(n_components=2).fit_transform(X_pca_scaled)

fig, ax = plt.subplots(figsize=(8, 6))
kmeans = KMeans(n_clusters=3, random_state=42)
clusters = kmeans.fit_predict(X_pca_scaled)

for c in range(3):
    mask = clusters == c
    ax.scatter(pca_2d[mask, 0], pca_2d[mask, 1], s=30, alpha=0.6,
               label=f'聚类{c+1} (n={mask.sum()})')

ax.set_xlabel(f'PC1 ({pca_explained[0]*100:.1f}%)', fontsize=12)
ax.set_ylabel(f'PC2 ({pca_explained[1]*100:.1f}%)', fontsize=12)
ax.set_title('血脂代谢指标PCA+KMeans聚类', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'pca_clustering.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: pca_clustering.png")

# 图13: 干预方案时序变化图 (样本1,2,3)
fig, ax = plt.subplots(figsize=(10, 5))

for sid, color in zip([1, 2, 3], ['#FF6B6B', '#4ECDC4', '#45B7D1']):
    if sid not in [1, 2, 3]:
        continue
    # 从Q3结果获取
    q3_out = json.load(open(os.path.join(PROJECT_ROOT, 'output', 'q3_upgraded_results.json'), encoding='utf-8'))
    if str(sid) in q3_out.get('sample_recommendations', {}):
        recs = q3_out['sample_recommendations'][str(sid)]['recommendations']
        if recs:
            rec = recs[0]  # 取第一个推荐
            # 用 final_tanshi + total_reduction 计算初始值
            t0 = rec['final_tanshi'] + rec['total_reduction']
            mr = rec['monthly_reduction_pct'] / 100
            months = list(range(7))
            vals = [t0]
            current = t0
            for _ in range(6):
                current = current * (1 - mr)
                vals.append(current)
            ax.plot(months, vals, 'o-', linewidth=2.5, markersize=8,
                   color=color, label=f'样本{sid} (月下降{mr*100:.1f}%)')

ax.set_xlabel('月份', fontsize=13)
ax.set_ylabel('痰湿积分', fontsize=13)
ax.set_title('6个月干预痰湿积分变化趋势', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(alpha=0.3)
ax.set_xticks(range(7))
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'intervention_timeline.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: intervention_timeline.png")

# 图14: 模型对比柱状图
fig, ax = plt.subplots(figsize=(10, 5))
model_names = list(model_results.keys())
accs = [model_results[m]['accuracy'] for m in model_names]
f1s = [model_results[m]['f1_macro'] for m in model_names]

x = np.arange(len(model_names))
width = 0.35
bars1 = ax.bar(x - width/2, accs, width, label='Accuracy', color='#4CAF50', edgecolor='white')
bars2 = ax.bar(x + width/2, f1s, width, label='F1(macro)', color='#2196F3', edgecolor='white')

ax.set_xticks(x)
ax.set_xticklabels(model_names, rotation=15, ha='right', fontsize=10)
ax.set_ylabel('评分', fontsize=12)
ax.set_title('六模型交叉验证对比', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.set_ylim(0.7, 1.0)

for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=9)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'model_comparison.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: model_comparison.png")

# 图15: 消融实验对比
fig, ax = plt.subplots(figsize=(8, 5))
exp_names = ['全特征\n(中西医结合)', '去中医体质', '纯西医指标']
exp_accs = [acc_full, acc_no_tcm, acc_western]
colors_exp = ['#4CAF50', '#FF9800', '#F44336']
bars = ax.bar(exp_names, exp_accs, color=colors_exp, edgecolor='white', width=0.5)
for bar, val in zip(bars, exp_accs):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f'{val:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
ax.set_ylabel('交叉验证准确率', fontsize=12)
ax.set_title('消融实验: 中医体质维度贡献', fontsize=14, fontweight='bold')
ax.set_ylim(0.80, 0.95)
ax.axhline(y=acc_full, color='gray', linestyle='--', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'ablation_study.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: ablation_study.png")

# 图16: 灰色关联度排名
fig, ax = plt.subplots(figsize=(9, 5))
grey_sorted = grey_df.sort_values('grade', ascending=True)
grey_names = [feature_names_cn_map.get(f, f) for f in grey_sorted['feature'].values]
colors_grey = plt.cm.YlOrRd(np.linspace(0.3, 0.8, len(grey_names)))
ax.barh(range(len(grey_names)), grey_sorted['grade'].values, color=colors_grey, edgecolor='white')
ax.set_yticks(range(len(grey_names)))
ax.set_yticklabels(grey_names, fontsize=11)
ax.set_xlabel('灰色关联度', fontsize=12)
ax.set_title('各指标与痰湿质积分的灰色关联度', fontsize=14, fontweight='bold')
for i, v in enumerate(grey_sorted['grade'].values):
    ax.text(v + 0.001, i, f'{v:.4f}', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'grey_relational_grade.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: grey_relational_grade.png")

# 图17: PCA碎石图
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(range(1, len(pca_explained)+1), pca_explained, 'o-', linewidth=2.5, markersize=8, color='#2196F3')
ax.fill_between(range(1, len(pca_explained)+1), pca_explained, alpha=0.2, color='#2196F3')
ax.axhline(y=1/len(pca_explained), color='red', linestyle='--', alpha=0.5, label='平均方差线')
ax.set_xlabel('主成分序号', fontsize=12)
ax.set_ylabel('方差解释比', fontsize=12)
ax.set_title('PCA碎石图', fontsize=14, fontweight='bold')
ax.legend()
ax.set_xticks(range(1, len(pca_explained)+1))
ax.grid(alpha=0.3)
for i, v in enumerate(pca_explained):
    ax.text(i+1, v + 0.005, f'{v:.3f}', ha='center', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'pca_scree.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: pca_scree.png")

# 图18: AHP权重饼图
fig, ax = plt.subplots(figsize=(7, 5))
ahp_colors = ['#4CAF50', '#FF6B6B', '#45B7D1']
wedges, texts, autotexts = ax.pie(weights_3, labels=criteria_3, autopct='%1.1f%%',
                                    colors=ahp_colors, textprops={'fontsize': 12},
                                    startangle=90, explode=(0.05, 0.05, 0.05))
for t in autotexts:
    t.set_fontweight('bold')
ax.set_title('AHP层次分析: 优化目标权重\n(CR=0.008 < 0.1, 一致性通过)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'ahp_weights.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: ahp_weights.png")

# 图19: 分级调理方案统计
q3_upgraded = pd.read_csv(os.path.join(PROJECT_ROOT, 'output', 'q3_upgraded_solutions.csv'))

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

# 调理级别
tcm_dist = q3_upgraded['tcm_level'].value_counts().sort_index()
tcm_names_map = {1: '1级基础调理', 2: '2级中度调理', 3: '3级强化调理'}
bars1 = axes[0].bar([tcm_names_map[k] for k in tcm_dist.index], tcm_dist.values,
                     color=['#4CAF50', '#FF9800', '#F44336'], edgecolor='white')
for bar, val in zip(bars1, tcm_dist.values):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, str(val),
                 ha='center', va='bottom', fontsize=11, fontweight='bold')
axes[0].set_title('调理级别分布', fontsize=13, fontweight='bold')
axes[0].set_ylabel('人数')

# 活动强度
act_dist = q3_upgraded['activity_level'].value_counts().sort_index()
act_names_map = {1: '1级低强度', 2: '2级中强度', 3: '3级高强度'}
bars2 = axes[1].bar([act_names_map[k] for k in act_dist.index], act_dist.values,
                     color=['#4CAF50', '#FF9800', '#F44336'], edgecolor='white')
for bar, val in zip(bars2, act_dist.values):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, str(val),
                 ha='center', va='bottom', fontsize=11, fontweight='bold')
axes[1].set_title('活动强度分布', fontsize=13, fontweight='bold')
axes[1].set_ylabel('人数')

# 成本分布
axes[2].hist(q3_upgraded['total_cost'], bins=20, color='#2196F3', edgecolor='white', alpha=0.8)
axes[2].axvline(x=2000, color='red', linestyle='--', alpha=0.7, label='上限2000元')
axes[2].set_xlabel('6个月总成本 (元)')
axes[2].set_ylabel('人数')
axes[2].set_title('方案成本分布', fontsize=13, fontweight='bold')
axes[2].legend()

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'q3_scheme_statistics.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: q3_scheme_statistics.png")

# 图20: 3D风险分层散点图
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

risk_names_map = {0: '低风险', 1: '中风险', 2: '高风险'}
for level, color, marker in zip([0, 1, 2], ['#4CAF50', '#FF9800', '#F44336'], ['o', 's', '^']):
    mask = df_risk['risk_level'] == level
    ax.scatter(df_risk[mask]['tanshi'], df_risk[mask]['tc'],
               df_risk[mask]['activity_total'],
               c=color, marker=marker, s=20, alpha=0.5, label=risk_names_map.get(level, f'Level{level}'))

ax.set_xlabel('痰湿质积分', fontsize=11)
ax.set_ylabel('总胆固醇(TC)', fontsize=11)
ax.set_zlabel('活动量表总分', fontsize=11)
ax.set_title('三维风险分层 (痰湿×TC×活动量)', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'risk_3d_scatter.png'), dpi=200, bbox_inches='tight')
plt.close()
print("  保存: risk_3d_scatter.png")


# ==========================================
# 汇总输出
# ==========================================
enhanced_results = {
    'model_comparison': model_results,
    'roc_auc': float(roc_auc),
    'confusion_matrix': cm.tolist(),
    'overall_accuracy': float(acc_overall),
    'ablation': {
        'full_features': float(acc_full),
        'no_tcm': float(acc_no_tcm),
        'western_only': float(acc_western),
        'drop_no_tcm': float(acc_full - acc_no_tcm),
        'drop_western': float(acc_full - acc_western),
    },
    'grey_relational': grey_df.to_dict('records'),
    'pca_explained_variance': pca_explained.tolist(),
    'pca_loadings': pca_components.tolist(),
    'ahp_weights_3d': weights_3.tolist(),
    'ahp_criteria': criteria_3,
    'ahp_CR': float(CR_3),
}

with open(os.path.join(PROJECT_ROOT, 'output', 'enhanced_results.json'), 'w', encoding='utf-8') as f:
    json.dump(enhanced_results, f, ensure_ascii=False, indent=2, default=str)

print(f"\n\n全部结果已保存到: output/enhanced_results.json")
print(f"\n当前图表总数: {len([f for f in os.listdir(FIG_DIR) if f.endswith('.png')])}张")
