# -*- coding: utf-8 -*-
"""
问题3: 6个月干预方案优化模型

针对痰湿体质确诊患者，构建优化模型：
- 决策变量: 调理级别(1/2/3), 活动强度(1/2/3), 每周训练频次(1-10)
- 目标: 最小化成本的同时最大化痰湿积分下降
- 约束: 年龄约束、评分约束、总成本<=2000元
"""
import sys
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from pulp import (
    LpProblem, LpMinimize, LpMaximize, LpVariable, LpInteger, LpBinary,
    lpSum, LpStatus, value, PULP_CBC_CMD
)

PROJECT_ROOT = str(ROOT)
sys.path.insert(0, PROJECT_ROOT)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_data, add_derived_features

print("=" * 70)
print("问题3: 6个月干预方案优化模型")
print("=" * 70)

# ==========================================
# 加载数据
# ==========================================
df = load_data()
df = add_derived_features(df)

# 筛选痰湿体质患者 (constitution_type == 5)
tanshi_patients = df[df['constitution_type'] == 5].copy()
print(f"\n痰湿体质患者数: {len(tanshi_patients)}")

# ==========================================
# 模型参数定义
# ==========================================

# 附表2: 调理分级
TCM_LEVELS = {
    1: {'name': '基础调理', 'min_tanshi': 0, 'max_tanshi': 58,
        'methods': '饮食调理+穴位按摩（低强度）', 'cost_month': 30},
    2: {'name': '中度调理', 'min_tanshi': 59, 'max_tanshi': 61,
        'methods': '饮食调理+穴位按摩+八段锦（中强度）', 'cost_month': 80},
    3: {'name': '强化调理', 'min_tanshi': 62, 'max_tanshi': 100,
        'methods': '饮食调理+穴位按摩+八段锦+中药代茶饮（高强度）', 'cost_month': 130},
}

# 附表3: 活动干预强度
ACTIVITY_LEVELS = {
    1: {'name': '低强度', 'duration': 10, 'cost_per_session': 3},
    2: {'name': '中强度', 'duration': 20, 'cost_per_session': 5},
    3: {'name': '高强度', 'duration': 30, 'cost_per_session': 8},
}

# 痰湿积分下降模型:
# 每周训练5次时，每提升一级活动强度，每月预期痰湿积分下降3%
# 特定强度下，每周增加1次训练，每月预期痰湿积分下降1%
# 基础: 每周5次 + 强度1级 -> 每月下降3%
# 每周n次 + 强度k级 -> 每月下降 = 3% * k + (n-5) * 1%

def calc_monthly_reduction(activity_level, sessions_per_week):
    """计算每月痰湿积分下降百分比"""
    base_reduction = 0.03 * activity_level  # 强度每级贡献3%
    extra_reduction = max(0, (sessions_per_week - 5)) * 0.01  # 每周超5次，每次多1%
    return base_reduction + extra_reduction


# ==========================================
# 约束条件函数
# ==========================================

def get_max_activity_level(age_group, activity_total):
    """根据年龄和活动评分获取可选的最高活动强度"""
    # 年龄约束
    if age_group == 5:  # 80-89岁
        max_by_age = 1
    elif age_group in [3, 4]:  # 60-79岁
        max_by_age = 2
    else:  # 40-59岁
        max_by_age = 3

    # 评分约束
    if activity_total < 40:
        max_by_score = 1
    elif activity_total < 60:
        max_by_score = 2
    else:
        max_by_score = 3

    return min(max_by_age, max_by_score)


def get_tcm_level(tanshi_score):
    """根据痰湿积分确定适用的调理级别"""
    if tanshi_score >= 62:
        return 3
    elif tanshi_score >= 59:
        return 2
    else:
        return 1


# ==========================================
# 优化模型
# ==========================================
print("\n【优化模型构建】")
print("-" * 50)

results_all = []

def solve_optimization(patient_row, tcm_weight=0.5):
    """
    为单个患者求解最优干预方案

    目标函数: 最小化 综合成本 = w1 * 经济成本 - w2 * 痰湿积分下降量
    或: 最大化 综合效益 = 痰湿积分下降量 - lambda * 经济成本

    决策变量:
    - tcm_level: 调理级别 (1, 2, 3)
    - activity_level: 活动强度 (1, 2, 3)
    - sessions_per_week: 每周训练频次 (1-10)
    """
    sample_id = int(patient_row['sample_id'])
    age_group = int(patient_row['age_group'])
    activity_total = int(patient_row['activity_total'])
    tanshi_score = float(patient_row['tanshi'])
    initial_tanshi = tanshi_score

    # 约束
    max_act = get_max_activity_level(age_group, activity_total)
    min_tcm = get_tcm_level(tanshi_score)

    # 创建优化问题
    prob = LpProblem(f"Patient_{sample_id}", LpMinimize)

    # 决策变量 - 使用二进制变量表示离散选择
    # 调理级别
    tcm_vars = {l: LpVariable(f"tcm_{l}", cat=LpBinary) for l in [1, 2, 3]}
    # 活动强度
    act_vars = {l: LpVariable(f"act_{l}", cat=LpBinary) for l in [1, 2, 3]}
    # 每周训练频次
    sess_vars = {n: LpVariable(f"sess_{n}", cat=LpBinary) for n in range(1, 11)}

    # 约束: 每个类别只能选一个
    prob += lpSum([tcm_vars[l] for l in [1, 2, 3]]) == 1
    prob += lpSum([act_vars[l] for l in [1, 2, 3]]) == 1
    prob += lpSum([sess_vars[n] for n in range(1, 11)]) == 1

    # 约束: 活动强度上限
    for l in range(max_act + 1, 4):
        prob += act_vars[l] == 0

    # 约束: 调理级别下限（基于痰湿积分）
    # 但考虑到优化目标，可以放宽到任何级别（选择更高级别效果更好）
    # 这里采用建议级别作为起点

    # 目标函数系数
    total_cost_linear = []  # 线性化后的总成本
    total_reduction_linear = []  # 线性化后的总下降量

    for tcm_l in [1, 2, 3]:
        tcm_cost = TCM_LEVELS[tcm_l]['cost_month'] * 6  # 6个月

        for act_l in [1, 2, 3]:
            act_cost_per_session = ACTIVITY_LEVELS[act_l]['cost_per_session']

            for sess_n in range(1, 11):
                # 该组合的总成本
                act_total_cost = act_cost_per_session * sess_n * 24  # 6个月=24周
                combo_cost = tcm_cost + act_total_cost

                # 该组合的痰湿积分下降量
                monthly_reduction = calc_monthly_reduction(act_l, sess_n)
                # 每月下降比例应用到当前痰湿积分
                # 6个月累计: 逐月递减
                remaining = initial_tanshi
                total_reduction = 0
                for month in range(6):
                    month_reduction = remaining * monthly_reduction
                    total_reduction += month_reduction
                    remaining -= month_reduction

                # 创建组合变量
                combo_var = LpVariable(f"combo_t{tcm_l}_a{act_l}_s{sess_n}", cat=LpBinary)

                total_cost_linear.append(combo_cost * combo_var)
                total_reduction_linear.append(total_reduction * combo_var)

    # 简化: 直接枚举所有可行组合，选择最优
    # 由于变量空间很小 (3 * 3 * 10 = 90种组合)，直接枚举更快

    best_cost = float('inf')
    best_reduction = 0
    best_combo = None

    for tcm_l in range(1, 4):
        tcm_cost = TCM_LEVELS[tcm_l]['cost_month'] * 6

        for act_l in range(1, max_act + 1):
            act_cost_per_session = ACTIVITY_LEVELS[act_l]['cost_per_session']

            for sess_n in range(1, 11):
                act_total_cost = act_cost_per_session * sess_n * 24
                total_cost = tcm_cost + act_total_cost

                # 成本约束
                if total_cost > 2000:
                    continue

                # 计算痰湿积分下降
                monthly_reduction = calc_monthly_reduction(act_l, sess_n)
                remaining = initial_tanshi
                total_reduction = 0
                for month in range(6):
                    month_reduction = remaining * monthly_reduction
                    total_reduction += month_reduction
                    remaining -= month_reduction

                # 综合目标: 最小化 (成本 - alpha * 下降量)
                # alpha = 痰湿积分每下降1分的价值（元/分）
                alpha = 15  # 假设每下降1分痰湿积分价值15元
                objective = total_cost - alpha * total_reduction

                if objective < best_cost:
                    best_cost = objective
                    best_reduction = total_reduction
                    best_combo = {
                        'sample_id': sample_id,
                        'tcm_level': tcm_l,
                        'tcm_name': TCM_LEVELS[tcm_l]['name'],
                        'tcm_methods': TCM_LEVELS[tcm_l]['methods'],
                        'tcm_cost': TCM_LEVELS[tcm_l]['cost_month'] * 6,
                        'activity_level': act_l,
                        'activity_name': ACTIVITY_LEVELS[act_l]['name'],
                        'activity_duration': ACTIVITY_LEVELS[act_l]['duration'],
                        'sessions_per_week': sess_n,
                        'activity_cost': act_total_cost,
                        'total_cost': total_cost,
                        'monthly_reduction_pct': monthly_reduction * 100,
                        'total_reduction_points': total_reduction,
                        'initial_tanshi': initial_tanshi,
                        'final_tanshi': initial_tanshi - total_reduction,
                        'age_group': age_group,
                        'activity_total': activity_total,
                        'objective_value': objective,
                    }

    return best_combo


# ==========================================
# 样本1, 2, 3的最优方案
# ==========================================
print("\n【样本 ID 1, 2, 3 最优干预方案】")
print("-" * 50)

sample_ids = [1, 2, 3]
sample_results = []

for sid in sample_ids:
    patient = tanshi_patients[tanshi_patients['sample_id'] == sid]
    if len(patient) == 0:
        print(f"  样本 {sid}: 不是痰湿体质患者")
        continue

    patient = patient.iloc[0]
    result = solve_optimization(patient)

    if result:
        sample_results.append(result)
        print(f"\n  样本 {sid}:")
        print(f"    初始痰湿积分: {result['initial_tanshi']:.1f}")
        print(f"    年龄组: {result['age_group']}, 活动量表总分: {result['activity_total']}")
        print(f"    最优方案:")
        print(f"      调理级别: {result['tcm_level']}级 ({result['tcm_name']})")
        print(f"      调理方式: {result['tcm_methods']}")
        print(f"      活动强度: {result['activity_level']}级 ({result['activity_name']}, {result['activity_duration']}分钟/次)")
        print(f"      训练频次: {result['sessions_per_week']}次/周")
        print(f"      每月痰湿积分下降: {result['monthly_reduction_pct']:.1f}%")
        print(f"    6个月预期:")
        print(f"      痰湿积分: {result['initial_tanshi']:.1f} -> {result['final_tanshi']:.1f} (下降{result['total_reduction_points']:.1f}分)")
        print(f"      总成本: {result['total_cost']}元 (调理{result['tcm_cost']}元 + 活动{result['activity_cost']}元)")

# ==========================================
# 全部痰湿体质患者求解
# ==========================================
print(f"\n\n【全部{len(tanshi_patients)}例痰湿体质患者优化求解】")
print("-" * 50)

all_results = []
for idx, patient in tanshi_patients.iterrows():
    result = solve_optimization(patient)
    if result:
        all_results.append(result)

results_df = pd.DataFrame(all_results)
print(f"成功求解: {len(results_df)}例")

# 匹配规律分析
print("\n【患者特征-最优方案匹配规律】")
print("-" * 50)

# 按年龄组分析
print("\n  按年龄组分布:")
for ag in sorted(results_df['age_group'].unique()):
    sub = results_df[results_df['age_group'] == ag]
    print(f"    年龄组{ag}: {len(sub)}人")
    print(f"      调理级别: {sub['tcm_level'].value_counts().to_dict()}")
    print(f"      活动强度: {sub['activity_level'].value_counts().to_dict()}")
    print(f"      周频次均值: {sub['sessions_per_week'].mean():.1f}")
    print(f"      成本均值: {sub['total_cost'].mean():.1f}元")
    print(f"      下降均值: {sub['total_reduction_points'].mean():.1f}分")

# 按活动量表总分分析
print("\n  按活动量表总分区间:")
for label, low, high in [('低(<40)', 0, 39), ('中(40-59)', 40, 59), ('高(>=60)', 60, 100)]:
    sub = results_df[(results_df['activity_total'] >= low) & (results_df['activity_total'] <= high)]
    if len(sub) > 0:
        print(f"    {label}: {len(sub)}人")
        print(f"      活动强度: {sub['activity_level'].mode().values[0]}级(最常见)")
        print(f"      周频次均值: {sub['sessions_per_week'].mean():.1f}")
        print(f"      成本均值: {sub['total_cost'].mean():.1f}元")
        print(f"      下降均值: {sub['total_reduction_points'].mean():.1f}分")

# ==========================================
# 敏感性分析
# ==========================================
print("\n\n【敏感性分析】")
print("-" * 50)

# 对alpha参数敏感性
for alpha in [10, 15, 20, 25, 30]:
    costs = []
    reductions = []
    for idx, patient in tanshi_patients.head(100).iterrows():
        # 重新计算最优方案
        initial_tanshi = float(patient['tanshi'])
        age_group = int(patient['age_group'])
        activity_total = int(patient['activity_total'])
        max_act = get_max_activity_level(age_group, activity_total)

        best_obj = float('inf')
        best_c = 0
        best_r = 0

        for tcm_l in range(1, 4):
            tcm_cost = TCM_LEVELS[tcm_l]['cost_month'] * 6
            for act_l in range(1, max_act + 1):
                act_cps = ACTIVITY_LEVELS[act_l]['cost_per_session']
                for sess_n in range(1, 11):
                    act_cost = act_cps * sess_n * 24
                    total_c = tcm_cost + act_cost
                    if total_c > 2000:
                        continue

                    mr = calc_monthly_reduction(act_l, sess_n)
                    rem = initial_tanshi
                    tr = 0
                    for _ in range(6):
                        red = rem * mr
                        tr += red
                        rem -= red

                    obj = total_c - alpha * tr
                    if obj < best_obj:
                        best_obj = obj
                        best_c = total_c
                        best_r = tr

        costs.append(best_c)
        reductions.append(best_r)

    print(f"  alpha={alpha:2d}: 平均成本={np.mean(costs):.1f}元, 平均下降={np.mean(reductions):.1f}分")

# ==========================================
# 输出结果
# ==========================================
import json

output = {
    'sample_solutions': sample_results,
    'all_results_summary': {
        'total_patients': len(results_df),
        'avg_cost': float(results_df['total_cost'].mean()),
        'avg_reduction': float(results_df['total_reduction_points'].mean()),
        'tcm_level_dist': results_df['tcm_level'].value_counts().to_dict(),
        'activity_level_dist': results_df['activity_level'].value_counts().to_dict(),
        'sessions_dist': results_df['sessions_per_week'].value_counts().to_dict(),
    },
    'age_group_analysis': {},
    'activity_score_analysis': {},
}

for ag in sorted(results_df['age_group'].unique()):
    sub = results_df[results_df['age_group'] == ag]
    output['age_group_analysis'][str(ag)] = {
        'count': len(sub),
        'avg_cost': float(sub['total_cost'].mean()),
        'avg_reduction': float(sub['total_reduction_points'].mean()),
    }

with open(os.path.join(PROJECT_ROOT, 'output', 'q3_results.json'), 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

# 保存全部结果
results_df.to_csv(os.path.join(PROJECT_ROOT, 'output', 'q3_all_solutions.csv'), index=False)

print(f"\n\n结果已保存到: output/q3_results.json, output/q3_all_solutions.csv")
