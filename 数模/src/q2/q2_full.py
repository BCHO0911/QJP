# -*- coding: utf-8 -*-
"""
问题2: 多维度风险预警模型

1. 构建三级风险标签（低/中/高）
2. 特征工程与分类模型
3. 决策树可解释规则提取
4. 阈值确定与核心特征组合识别
"""
import sys
import os
import warnings
warnings.filterwarnings('ignore')
import json

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from scipy.stats import percentileofscore

PROJECT_ROOT = r"d:\GIT\private\数模"
sys.path.insert(0, PROJECT_ROOT)

from src.data_loader import load_data, add_derived_features

print("=" * 70)
print("问题2: 多维度风险预警模型")
print("=" * 70)

# ==========================================
# 加载数据
# ==========================================
df = load_data()
df = add_derived_features(df)

# ==========================================
# 第一部分: 构建三级风险标签
# ==========================================
print("\n【第一部分】构建三级风险标签")
print("-" * 50)

# 基于题目示例和医学知识构建风险评分
# 高风险参考: 血脂指标异常且痰湿积分>=60，或血脂正常但痰湿积分>=80且活动能力<40
# 综合评分 = 血脂异常程度 + 痰湿严重程度 + 活动能力反向

def compute_risk_level(row):
    """计算风险等级: 0=低, 1=中, 2=高"""
    # 血脂异常计数 (0-4)
    lipid_abnormal = (
        (1 if row['tc'] < 3.1 or row['tc'] > 6.2 else 0) +
        (1 if row['tg'] < 0.56 or row['tg'] > 1.7 else 0) +
        (1 if row['ldl_c'] < 2.07 or row['ldl_c'] > 3.1 else 0) +
        (1 if row['hdl_c'] < 1.04 or row['hdl_c'] > 1.55 else 0)
    )

    tanshi_score = row['tanshi']
    activity_score = row['activity_total']

    # 高血脂症标签
    hyper = row['hyperlipidemia']

    # 风险评分规则
    score = 0

    # 血脂异常贡献 (0-40分)
    score += lipid_abnormal * 10

    # 痰湿积分贡献 (0-40分，按比例)
    score += (tanshi_score / 100) * 40

    # 活动能力反向贡献 (0-20分)
    score += ((100 - activity_score) / 100) * 20

    # 其他代谢异常加分
    if row['glucose'] > 6.1:
        score += 5
    if row['uric_acid'] > 428:
        score += 5
    if row['bmi'] > 23.9:
        score += 5

    # 分级
    if score >= 55:
        return 2  # 高风险
    elif score >= 35:
        return 1  # 中风险
    else:
        return 0  # 低风险

df['risk_level'] = df.apply(compute_risk_level, axis=1)

print("风险等级分布:")
risk_names = {0: '低风险', 1: '中风险', 2: '高风险'}
for level in [0, 1, 2]:
    sub = df[df['risk_level'] == level]
    print(f"  {risk_names[level]}: {len(sub)}人 ({len(sub)/len(df):.1%})")
    print(f"    平均痰湿积分: {sub['tanshi'].mean():.1f}")
    print(f"    平均活动总分: {sub['activity_total'].mean():.1f}")
    print(f"    高血脂确诊率: {sub['hyperlipidemia'].mean():.2%}")
    print(f"    平均血脂异常数: {sub['abnormal_count'].mean():.1f}")

# ==========================================
# 第二部分: 特征工程
# ==========================================
print("\n【第二部分】特征工程")
print("-" * 50)

# 选择建模特征（排除样本ID、标签等）
feature_cols = (
    ['tanshi', 'pinghe', 'qixu', 'yangxu', 'yinxu', 'shire', 'xueyu', 'qiyu', 'tebing'] +
    ['tc', 'tg', 'ldl_c', 'hdl_c', 'glucose', 'uric_acid', 'bmi'] +
    ['adl_total', 'iadl_total', 'activity_total'] +
    ['age_group', 'gender', 'smoking', 'drinking'] +
    ['tc_abnormal', 'tg_abnormal', 'ldl_abnormal', 'hdl_abnormal', 'abnormal_count'] +
    ['tc_hdl_ratio', 'non_hdl']
)

# 交互特征
df['tanshi_x_activity'] = df['tanshi'] * (100 - df['activity_total']) / 100
df['tanshi_x_tc'] = df['tanshi'] * df['tc']
df['tanshi_x_tg'] = df['tanshi'] * df['tg']
feature_cols.extend(['tanshi_x_activity', 'tanshi_x_tc', 'tanshi_x_tg'])

X = df[feature_cols].values
y = df['risk_level'].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"特征数量: {len(feature_cols)}")
print(f"样本数量: {len(df)}")

# ==========================================
# 第三部分: 分类模型对比
# ==========================================
print("\n【第三部分】分类模型对比 (5折交叉验证)")
print("-" * 50)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

models = {
    'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=150, max_depth=5, random_state=42),
    'DecisionTree': DecisionTreeClassifier(max_depth=6, random_state=42),
}

results = {}
for name, model in models.items():
    acc = cross_val_score(model, X_scaled, y, cv=cv, scoring='accuracy').mean()
    f1 = cross_val_score(model, X_scaled, y, cv=cv, scoring='f1_macro').mean()
    results[name] = {'accuracy': acc, 'f1_macro': f1}
    print(f"  {name:20s}: Accuracy={acc:.4f}, F1(macro)={f1:.4f}")

# 选择最优模型
best_model_name = max(results, key=lambda k: results[k]['f1_macro'])
print(f"\n  最优模型: {best_model_name} (F1={results[best_model_name]['f1_macro']:.4f})")

# 训练最优模型
best_model = models[best_model_name]
best_model.fit(X_scaled, y)
df['predicted_risk'] = best_model.predict(X_scaled)

# 分类报告
print(f"\n  {best_model_name} 分类报告:")
print(classification_report(y, df['predicted_risk'], target_names=['低风险', '中风险', '高风险']))

# ==========================================
# 第四部分: 决策树规则提取
# ==========================================
print("\n【第四部分】决策树可解释规则提取")
print("-" * 50)

dt = DecisionTreeClassifier(max_depth=5, min_samples_leaf=20, random_state=42)
dt.fit(X_scaled, y)

# 导出决策规则
tree_text = export_text(dt, feature_names=feature_cols, max_depth=5)
print("决策树规则（前5层）:")
print(tree_text[:2000])

# 特征重要性
dt_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': dt.feature_importances_
}).sort_values('importance', ascending=False)

print("\n决策树特征重要性 Top 15:")
for _, row in dt_importance.head(15).iterrows():
    print(f"  {row['feature']:25s}: {row['importance']:.4f}")

# ==========================================
# 第五部分: 阈值确定
# ==========================================
print("\n【第五部分】三级风险阈值确定")
print("-" * 50)

# 基于各特征在不同风险等级的分位数
for feat in ['tanshi', 'tc', 'tg', 'ldl_c', 'activity_total', 'abnormal_count', 'tc_hdl_ratio', 'non_hdl']:
    vals = {}
    for level in [0, 1, 2]:
        sub = df[df['risk_level'] == level][feat]
        vals[level] = {'mean': sub.mean(), 'q25': sub.quantile(0.25), 'q50': sub.median(), 'q75': sub.quantile(0.75)}

    print(f"\n  {feat}:")
    for level in [0, 1, 2]:
        print(f"    {risk_names[level]}: mean={vals[level]['mean']:.2f}, "
              f"Q25={vals[level]['q25']:.2f}, Q50={vals[level]['q50']:.2f}, Q75={vals[level]['q75']:.2f}")

# 阈值建议
print("\n\n  阈值选取依据:")
tanshi_q50_high = df[df['risk_level']==2]['tanshi'].quantile(0.25)
tanshi_q50_mid = df[df['risk_level']==1]['tanshi'].quantile(0.50)
activity_q50_high = df[df['risk_level']==2]['activity_total'].quantile(0.50)
tc_q50_high = df[df['risk_level']==2]['tc'].quantile(0.25)

print(f"    高风险: 痰湿积分 >= {tanshi_q50_high:.0f} 且 (血脂异常数 >= 2 或 TC >= {tc_q50_high:.2f})")
print(f"    中风险: 痰湿积分 >= {tanshi_q50_mid:.0f} 或 活动量表总分 <= {activity_q50_high:.0f}")
print(f"    低风险: 其余情况")

# ==========================================
# 第六部分: 核心特征组合识别
# ==========================================
print("\n【第六部分】痰湿体质高风险人群核心特征组合")
print("-" * 50)

# 筛选痰湿体质高风险人群
tanshi_high_risk = df[(df['constitution_type'] == 5) & (df['risk_level'] == 2)]
print(f"痰湿体质高风险人数: {len(tanshi_high_risk)}")

# 分析特征组合
if len(tanshi_high_risk) > 0:
    # 统计特征组合频率
    def categorize_feature(row, feat, thresholds):
        if row[feat] >= thresholds[1]:
            return 'high'
        elif row[feat] >= thresholds[0]:
            return 'medium'
        else:
            return 'low'

    # 关键特征分箱
    tanshi_high_risk = tanshi_high_risk.copy()
    tanshi_high_risk['tc_level'] = tanshi_high_risk['tc'].apply(
        lambda x: '异常' if x < 3.1 or x > 6.2 else '正常')
    tanshi_high_risk['tg_level'] = tanshi_high_risk['tg'].apply(
        lambda x: '异常' if x < 0.56 or x > 1.7 else '正常')
    tanshi_high_risk['activity_level'] = tanshi_high_risk['activity_total'].apply(
        lambda x: '低' if x < 40 else ('中' if x < 60 else '高'))
    tanshi_high_risk['tanshi_level'] = tanshi_high_risk['tanshi'].apply(
        lambda x: '重度(>=60)' if x >= 60 else ('中度(40-60)' if x >= 40 else '轻度(<40)'))

    # 常见组合
    combo = tanshi_high_risk.groupby(['tanshi_level', 'activity_level', 'tc_level', 'tg_level']).size().sort_values(ascending=False)
    print("\n  最常见特征组合 Top 10:")
    for combo_idx, (key, count) in enumerate(combo.head(10).items()):
        tanshi_l, act_l, tc_l, tg_l = key
        print(f"    #{combo_idx+1}: 痰湿={tanshi_l}, 活动={act_l}, TC={tc_l}, TG={tg_l} -> {count}人 ({count/len(tanshi_high_risk):.1%})")

# ==========================================
# 输出结果
# ==========================================
output = {
    'risk_distribution': {str(k): int(v) for k, v in df['risk_level'].value_counts().items()},
    'model_results': results,
    'dt_top_features': dt_importance.head(15).to_dict('records'),
    'thresholds': {
        'tanshi_high_threshold': float(tanshi_q50_high),
        'tanshi_mid_threshold': float(tanshi_q50_mid),
        'activity_high_threshold': float(activity_q50_high),
    }
}

with open(os.path.join(PROJECT_ROOT, 'output', 'q2_results.json'), 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

# 保存带风险标签的数据
df.to_csv(os.path.join(PROJECT_ROOT, 'output', 'data_with_risk.csv'), index=False)

print(f"\n\n结果已保存到: output/q2_results.json, output/data_with_risk.csv")
