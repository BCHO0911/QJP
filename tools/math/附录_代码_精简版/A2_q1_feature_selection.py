# -*- coding: utf-8 -*-
"""
附录A.2  问题一：关键指标筛选与体质贡献度分析 (精简版)
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.feature_selection import mutual_info_regression, mutual_info_classif
from scipy.stats import spearmanr, kruskal

# ==================== 1. 四种方法交叉筛选 ====================

def select_key_features(df, candidate_features, target_name):
    """
    使用Spearman相关、LASSO、随机森林、互信息四种方法
    交叉验证筛选关键指标，返回被>=2种方法选中的特征列表
    """
    y = df['tanshi'] if target_name == 'tanshi' else df['hyperlipidemia']
    X = df[candidate_features].values
    is_classification = (target_name == 'hyperlipidemia')

    # 方法1: Spearman秩相关系数
    spearman_selected = set()
    for feat in candidate_features:
        rho, pval = spearmanr(df[feat], y)
        if abs(rho) > 0.05 and pval < 0.05:
            spearman_selected.add(feat)

    # 方法2: LASSO回归 (L1正则化自动特征筛选)
    if is_classification:
        model = LogisticRegression(penalty='l1', solver='liblinear', C=0.1)
    else:
        model = Lasso(alpha=0.05, max_iter=5000)
    model.fit(X, y)
    coefs = model.coef_ if not is_classification else model.coef_[0]
    lasso_selected = {candidate_features[i] for i, c in enumerate(coefs) if abs(c) > 1e-6}

    # 方法3: 随机森林特征重要性 (基于Gini不纯度)
    if is_classification:
        rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    else:
        rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    rf_imp = pd.DataFrame({'feature': candidate_features,
                           'importance': rf.feature_importances_})
    rf_selected = set(rf_imp.nlargest(10, 'importance')['feature'])

    # 方法4: 互信息法
    mi_func = mutual_info_classif if is_classification else mutual_info_regression
    mi = mi_func(X, y, random_state=42)
    mi_selected = set(pd.DataFrame({'feature': candidate_features, 'mi': mi})
                      .nlargest(10, 'mi')['feature'])

    # 投票机制: 被>=2种方法选中的特征即为关键指标
    methods = {'spearman': spearman_selected, 'lasso': lasso_selected,
               'rf': rf_selected, 'mi': mi_selected}
    all_features = set().union(*methods.values())
    key_features = [f for f in all_features
                    if sum(1 for s in methods.values() if f in s) >= 2]

    return sorted(key_features, key=lambda f: -sum(1 for s in methods.values() if f in s))


# ==================== 2. 体质贡献度分析 ====================

def analyze_constitution_contribution(df):
    """
    多元Logistic回归分析九种体质对高血脂风险的贡献度
    返回各体质的OR值(Odds Ratio)
    """
    from sklearn.preprocessing import StandardScaler

    blood_feats = ['tc', 'tg', 'ldl_c', 'hdl_c', 'glucose', 'uric_acid', 'bmi']
    activity_feats = ['adl_total', 'iadl_total', 'activity_total']
    lifestyle = ['age_group', 'gender', 'smoking', 'drinking']

    X = pd.get_dummies(df['constitution_type'], prefix='const', dtype=int)
    X = pd.concat([X, df[blood_feats + activity_feats + lifestyle]], axis=1)

    model = LogisticRegression(max_iter=5000, random_state=42)
    model.fit(StandardScaler().fit_transform(X), df['hyperlipidemia'])

    results = []
    for i, feat in enumerate(X.columns):
        if feat.startswith('const_'):
            results.append({
                '体质': feat.replace('const_', ''),
                '回归系数': model.coef_[0][i],
                'OR值': np.exp(model.coef_[0][i])
            })
    return pd.DataFrame(results).sort_values('OR值', ascending=False)
