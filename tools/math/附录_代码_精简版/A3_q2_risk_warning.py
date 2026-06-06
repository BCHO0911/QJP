# -*- coding: utf-8 -*-
"""
附录A.3  问题二：多维度风险预警模型 (精简版)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import cross_val_score, StratifiedKFold

# ==================== 1. 三级风险评分模型 ====================

def compute_risk_score(row):
    """
    综合风险评分公式:
    Score = 10N_abn + 40(T/100) + 20((100-A)/100) + 5I(G>6.1) + 5I(UA>428) + 5I(BMI>23.9)
    """
    score = 0
    # 血脂异常项数 (每项10分, 最高40分)
    lipid_abnormal = (1 if row['tc'] < 3.1 or row['tc'] > 6.2 else 0) + \
                     (1 if row['tg'] < 0.56 or row['tg'] > 1.7 else 0) + \
                     (1 if row['ldl_c'] < 2.07 or row['ldl_c'] > 3.1 else 0) + \
                     (1 if row['hdl_c'] < 1.04 or row['hdl_c'] > 1.55 else 0)
    score += lipid_abnormal * 10

    # 痰湿积分归一化 (最高40分)
    score += (row['tanshi'] / 100) * 40

    # 活动能力反向得分 (最高20分)
    score += ((100 - row['activity_total']) / 100) * 20

    # 其他代谢异常 (各5分)
    if row['glucose'] > 6.1:  score += 5
    if row['uric_acid'] > 428: score += 5
    if row['bmi'] > 23.9:     score += 5

    # 三级分类
    if score >= 55:      return 2  # 高风险
    elif score >= 35:    return 1  # 中风险
    else:                return 0  # 低风险


# ==================== 2. 六分类模型对比 ====================

def compare_models(X, y):
    """5折交叉验证对比6种分类模型"""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    models = {
        'GradientBoosting': GradientBoostingClassifier(
            n_estimators=150, max_depth=5, random_state=42),
        'LogisticRegression': LogisticRegression(max_iter=5000, random_state=42),
        'SVM': SVC(kernel='rbf', C=10, gamma='scale', probability=True,
                   random_state=42),
        'RandomForest': RandomForestClassifier(
            n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
        'DecisionTree': DecisionTreeClassifier(max_depth=6, random_state=42),
        'KNN': KNeighborsClassifier(n_neighbors=15, weights='distance'),
    }

    results = {}
    for name, model in models.items():
        acc = cross_val_score(model, X, y, cv=cv, scoring='accuracy').mean()
        f1  = cross_val_score(model, X, y, cv=cv, scoring='f1_macro').mean()
        results[name] = {'Accuracy': f'{acc:.4f}', 'F1(macro)': f'{f1:.4f}'}

    return pd.DataFrame(results).T


# ==================== 3. 消融实验 ====================

def ablation_study(df, feature_cols, target):
    """
    消融实验：验证中医体质维度的贡献
    比较：全特征 vs 去中医体质 vs 纯西医指标
    """
    from sklearn.model_selection import cross_val_score

    groups = {
        '全特征(中西医结合)': feature_cols,
        '去掉中医体质': [f for f in feature_cols if f not in
                       ['pinghe','qixu','yangxu','yinxu','tanshi',
                        'shire','xueyu','qiyu','tebing']],
        '仅西医指标': ['tc','tg','ldl_c','hdl_c','glucose','uric_acid','bmi'],
    }

    results = {}
    for name, feats in groups.items():
        X = df[feats].values
        model = GradientBoostingClassifier(n_estimators=150, max_depth=5, random_state=42)
        f1 = cross_val_score(model, X, target, cv=5, scoring='f1_macro').mean()
        results[name] = f1

    return results


# ==================== 4. 决策树规则提取 ====================

def extract_tree_rules(X, y, feature_names, max_depth=5):
    """训练可解释决策树并导出if-then规则"""
    dt = DecisionTreeClassifier(max_depth=max_depth, min_samples_leaf=20,
                                random_state=42)
    dt.fit(X, y)
    rules = export_text(dt, feature_names=feature_names, max_depth=max_depth)
    importance = pd.DataFrame({
        'feature': feature_names,
        'importance': dt.feature_importances_
    }).sort_values('importance', ascending=False)
    return rules, importance
