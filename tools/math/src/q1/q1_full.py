# -*- coding: utf-8 -*-
"""
问题1: 关键指标筛选与体质贡献度分析

1. 从血常规和活动量表中筛选能有效表征痰湿体质严重程度的关键指标
2. 筛选能预警高血脂发病风险的关键指标
3. 研究九种体质对发病风险的贡献度差异
"""
import sys
import os
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = r"d:\GIT\private\数模"
sys.path.insert(0, PROJECT_ROOT)
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

import numpy as np
import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from scipy import stats
from scipy.stats import spearmanr, f_oneway, kruskal
import json

from src.data_loader import load_data, add_derived_features

RESULTS = {}

# ==========================================
# 加载数据
# ==========================================
df = load_data()
df = add_derived_features(df)

# 特征分组
blood_features = ['tc', 'tg', 'ldl_c', 'hdl_c', 'glucose', 'uric_acid', 'bmi']
adl_features = ['adl_item1', 'adl_item2', 'adl_item3', 'adl_item4', 'adl_item5']
iadl_features = ['iadl_item1', 'iadl_item2', 'iadl_item3', 'iadl_item4', 'iadl_item5']
activity_features = ['adl_total', 'iadl_total', 'activity_total']
lifestyle_features = ['age_group', 'gender', 'smoking', 'drinking']
abnormal_features = ['tc_abnormal', 'tg_abnormal', 'ldl_abnormal', 'hdl_abnormal', 'glucose_abnormal', 'bmi_abnormal', 'abnormal_count']
derived_features = ['tc_hdl_ratio', 'non_hdl']
constitution_scores = ['pinghe', 'qixu', 'yangxu', 'yinxu', 'tanshi', 'shire', 'xueyu', 'qiyu', 'tebing']

candidate_features = (blood_features + adl_features + iadl_features +
                      activity_features + lifestyle_features + abnormal_features + derived_features)

print("=" * 70)
print("问题1: 关键指标筛选与体质贡献度分析")
print("=" * 70)

# ==========================================
# 第一部分: 表征痰湿体质严重程度的关键指标
# ==========================================
print("\n【第一部分】表征痰湿体质严重程度的关键指标筛选")
print("-" * 50)

# 方法1: Spearman相关性
print("\n1. Spearman相关性分析 (目标: 痰湿质积分)")
spearman_results = []
for feat in candidate_features:
    rho, pval = spearmanr(df[feat], df['tanshi'])
    spearman_results.append({'feature': feat, 'rho': rho, 'p_value': pval})

spearman_df = pd.DataFrame(spearman_results).sort_values('rho', key=abs, ascending=False)
for _, row in spearman_df.head(10).iterrows():
    print(f"  {row['feature']:20s}: rho={row['rho']:+.4f}, p={row['p_value']:.2e}")

# 方法2: Lasso回归 (以痰湿质积分为因变量)
print("\n2. LASSO回归 (目标: 痰湿质积分)")
X = df[candidate_features].values
y_tanshi = df['tanshi'].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

lasso = Lasso(alpha=0.05, max_iter=5000)
lasso.fit(X_scaled, y_tanshi)
lasso_coefs = pd.DataFrame({
    'feature': candidate_features,
    'coefficient': lasso.coef_
}).sort_values('coefficient', key=abs, ascending=False)
selected_lasso_tanshi = lasso_coefs[lasso_coefs['coefficient'] != 0]
print(f"  非零系数特征数: {len(selected_lasso_tanshi)}")
for _, row in selected_lasso_tanshi.iterrows():
    print(f"  {row['feature']:20s}: coef={row['coefficient']:+.4f}")

# 方法3: 随机森林特征重要性
print("\n3. 随机森林特征重要性 (目标: 痰湿质积分)")
rf_reg = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
rf_reg.fit(X_scaled, y_tanshi)
rf_imp_tanshi = pd.DataFrame({
    'feature': candidate_features,
    'importance': rf_reg.feature_importances_
}).sort_values('importance', ascending=False)
for _, row in rf_imp_tanshi.head(10).iterrows():
    print(f"  {row['feature']:20s}: importance={row['importance']:.4f}")

# 方法4: 互信息
print("\n4. 互信息分析 (目标: 痰湿质积分)")
mi_tanshi = mutual_info_regression(X_scaled, y_tanshi, random_state=42)
mi_df_tanshi = pd.DataFrame({
    'feature': candidate_features,
    'mutual_info': mi_tanshi
}).sort_values('mutual_info', ascending=False)
for _, row in mi_df_tanshi.head(10).iterrows():
    print(f"  {row['feature']:20s}: MI={row['mutual_info']:.4f}")

# 综合痰湿质特征选择结果
tanshi_methods = {
    'spearman': set(spearman_df[spearman_df['p_value'] < 0.05]['feature'].head(10)),
    'lasso': set(selected_lasso_tanshi['feature']),
    'rf': set(rf_imp_tanshi.head(10)['feature']),
    'mi': set(mi_df_tanshi.head(10)['feature']),
}

# 投票: 被>=2种方法选中的特征
all_tanshi_features = set()
for s in tanshi_methods.values():
    all_tanshi_features |= s

tanshi_votes = {}
for feat in all_tanshi_features:
    votes = sum(1 for s in tanshi_methods.values() if feat in s)
    tanshi_votes[feat] = votes

tanshi_selected = sorted(tanshi_votes.items(), key=lambda x: -x[1])
print("\n5. 综合筛选结果 (>=2种方法选中):")
for feat, votes in tanshi_selected:
    if votes >= 2:
        print(f"  {feat:20s}: {votes}/4 methods")

RESULTS['tanshi_key_indicators'] = [f for f, v in tanshi_selected if v >= 2]

# ==========================================
# 第二部分: 预警高血脂发病风险的关键指标
# ==========================================
print("\n\n【第二部分】预警高血脂发病风险的关键指标筛选")
print("-" * 50)

y_hyper = df['hyperlipidemia'].values

# 方法1: Spearman相关性
print("\n1. Spearman相关性分析 (目标: 高血脂标签)")
spearman_hyper = []
for feat in candidate_features:
    rho, pval = spearmanr(df[feat], y_hyper)
    spearman_hyper.append({'feature': feat, 'rho': rho, 'p_value': pval})
spearman_hyper_df = pd.DataFrame(spearman_hyper).sort_values('rho', key=abs, ascending=False)
for _, row in spearman_hyper_df.head(10).iterrows():
    print(f"  {row['feature']:20s}: rho={row['rho']:+.4f}, p={row['p_value']:.2e}")

# 方法2: LASSO逻辑回归
print("\n2. LASSO逻辑回归 (目标: 高血脂标签)")
lasso_lr = LogisticRegression(penalty='l1', solver='liblinear', C=0.1, max_iter=5000)
lasso_lr.fit(X_scaled, y_hyper)
lasso_lr_coefs = pd.DataFrame({
    'feature': candidate_features,
    'coefficient': lasso_lr.coef_[0]
}).sort_values('coefficient', key=abs, ascending=False)
selected_lasso_hyper = lasso_lr_coefs[lasso_lr_coefs['coefficient'] != 0]
print(f"  非零系数特征数: {len(selected_lasso_hyper)}")
for _, row in selected_lasso_hyper.iterrows():
    print(f"  {row['feature']:20s}: coef={row['coefficient']:+.4f}")

# 方法3: 随机森林
print("\n3. 随机森林特征重要性 (目标: 高血脂标签)")
rf_clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
rf_clf.fit(X_scaled, y_hyper)
rf_imp_hyper = pd.DataFrame({
    'feature': candidate_features,
    'importance': rf_clf.feature_importances_
}).sort_values('importance', ascending=False)
for _, row in rf_imp_hyper.head(10).iterrows():
    print(f"  {row['feature']:20s}: importance={row['importance']:.4f}")

# 方法4: 互信息
print("\n4. 互信息分析 (目标: 高血脂标签)")
mi_hyper = mutual_info_classif(X_scaled, y_hyper, random_state=42)
mi_df_hyper = pd.DataFrame({
    'feature': candidate_features,
    'mutual_info': mi_hyper
}).sort_values('mutual_info', ascending=False)
for _, row in mi_df_hyper.head(10).iterrows():
    print(f"  {row['feature']:20s}: MI={row['mutual_info']:.4f}")

# 综合高血脂特征选择
hyper_methods = {
    'spearman': set(spearman_hyper_df[spearman_hyper_df['p_value'] < 0.05]['feature'].head(10)),
    'lasso': set(selected_lasso_hyper['feature']),
    'rf': set(rf_imp_hyper.head(10)['feature']),
    'mi': set(mi_df_hyper.head(10)['feature']),
}

all_hyper_features = set()
for s in hyper_methods.values():
    all_hyper_features |= s

hyper_votes = {}
for feat in all_hyper_features:
    votes = sum(1 for s in hyper_methods.values() if feat in s)
    hyper_votes[feat] = votes

hyper_selected = sorted(hyper_votes.items(), key=lambda x: -x[1])
print("\n5. 综合筛选结果 (>=2种方法选中):")
for feat, votes in hyper_selected:
    if votes >= 2:
        print(f"  {feat:20s}: {votes}/4 methods")

RESULTS['hyperlipidemia_key_indicators'] = [f for f, v in hyper_selected if v >= 2]

# ==========================================
# 第三部分: 九种体质对发病风险的贡献度
# ==========================================
print("\n\n【第三部分】九种体质对高血脂发病风险的贡献度分析")
print("-" * 50)

# 方法1: 各体质的高血脂发病率
print("\n1. 各体质类型的高血脂发病率:")
for ctype in range(1, 10):
    sub = df[df['constitution_type'] == ctype]
    rate = sub['hyperlipidemia'].mean()
    n = len(sub)
    print(f"  {ctype}: 样本数={n:3d}, 发病率={rate:.2%}")

# 方法2: Logistic回归OR值 (以体质标签为独热编码)
print("\n2. Logistic回归OR值分析:")
from sklearn.preprocessing import OneHotEncoder

constitution_dummies = pd.get_dummies(df['constitution_type'], prefix='const', dtype=int)
X_const = pd.concat([
    constitution_dummies,
    df[blood_features + activity_features + lifestyle_features]
], axis=1)

X_const_scaled = StandardScaler().fit_transform(X_const)
log_reg = LogisticRegression(max_iter=5000, random_state=42)
log_reg.fit(X_const_scaled, y_hyper)

# OR值 = exp(coef)
or_results = []
for i, feat in enumerate(X_const.columns):
    if feat.startswith('const_'):
        coef = log_reg.coef_[0][i]
        or_val = np.exp(coef)
        or_results.append({
            'constitution': feat,
            'coefficient': coef,
            'OR': or_val,
        })

or_df = pd.DataFrame(or_results).sort_values('OR', ascending=False)
print(f"  {'体质':<15s} {'系数':>8s} {'OR值':>8s}")
for _, row in or_df.iterrows():
    print(f"  {row['constitution']:<15s} {row['coefficient']:>+8.4f} {row['OR']:>8.3f}")

# 方法3: 随机森林中的体质得分重要性
print("\n3. 九种体质积分对高血脂的随机森林重要性:")
X_const_scores = df[constitution_scores + blood_features + activity_features].values
X_const_scores_scaled = StandardScaler().fit_transform(X_const_scores)
rf_const = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
rf_const.fit(X_const_scores_scaled, y_hyper)
const_imp = pd.DataFrame({
    'feature': constitution_scores + blood_features + activity_features,
    'importance': rf_const.feature_importances_
})
const_imp_sorted = const_imp[const_imp['feature'].isin(constitution_scores)].sort_values('importance', ascending=False)
for _, row in const_imp_sorted.iterrows():
    print(f"  {row['feature']:20s}: importance={row['importance']:.4f}")

# 方法4: ANOVA/Kruskal-Wallis检验
print("\n4. 各指标在不同体质间的差异显著性 (Kruskal-Wallis检验):")
for feat in blood_features + activity_features:
    groups = [df[df['constitution_type'] == t][feat].values for t in range(1, 10)]
    stat, pval = kruskal(*groups)
    print(f"  {feat:20s}: H={stat:.2f}, p={pval:.2e}")

# ==========================================
# 输出结果
# ==========================================
RESULTS['constitution_or_values'] = or_df.to_dict('records')
RESULTS['constitution_rf_importance'] = const_imp_sorted.to_dict('records')

output_path = os.path.join(PROJECT_ROOT, 'output', 'q1_results.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2, default=str)

print(f"\n\n结果已保存到: {output_path}")
print("\n【问题1 关键结论汇总】")
print(f"  痰湿体质关键指标: {RESULTS['tanshi_key_indicators']}")
print(f"  高血脂预警指标:   {RESULTS['hyperlipidemia_key_indicators']}")
print(f"  体质贡献度(OR值最高): {or_df.iloc[0]['constitution']} (OR={or_df.iloc[0]['OR']:.3f})")
