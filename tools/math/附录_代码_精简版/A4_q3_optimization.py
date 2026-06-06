# -*- coding: utf-8 -*-
"""
附录A.4  问题三：6个月干预方案优化模型 (精简版)
"""

import numpy as np
import pandas as pd

# ==================== 参数定义 ====================

TCM_LEVELS = {
    1: {'name': '基础调理', 'cost_month': 30,
        'methods': '饮食调理+穴位按摩'},
    2: {'name': '中度调理', 'cost_month': 80,
        'methods': '饮食调理+穴位按摩+八段锦'},
    3: {'name': '强化调理', 'cost_month': 130,
        'methods': '饮食调理+穴位按摩+八段锦+中药代茶饮'},
}

ACTIVITY_LEVELS = {
    1: {'name': '低强度', 'duration': 10, 'cost_per_session': 3},
    2: {'name': '中强度', 'duration': 20, 'cost_per_session': 5},
    3: {'name': '高强度', 'duration': 30, 'cost_per_session': 8},
}

# ==================== 核心函数 ====================

def calc_monthly_reduction(activity_level, sessions_per_week):
    """
    痰湿积分下降模型:
    每月下降率 = 3% × K + max(0, n-5) × 1%
    其中K为活动强度级别, n为每周训练频次
    """
    base = 0.03 * activity_level
    extra = max(0, (sessions_per_week - 5)) * 0.01
    return base + extra


def get_constraints(age_group, activity_total, tanshi_score):
    """
    确定患者的多重约束条件:
    - 调理级别: 由痰湿积分决定 (附表2)
    - 活动强度上限: 由年龄和活动评分共同决定 (附表3)
    - 总成本上限: 2000元
    """
    # 调理级别约束
    if tanshi_score >= 62:    tcm_level = 3
    elif tanshi_score >= 59:  tcm_level = 2
    else:                     tcm_level = 1

    # 年龄约束
    if age_group == 5:        max_act_by_age = 1
    elif age_group in [3,4]:  max_act_by_age = 2
    else:                     max_act_by_age = 3

    # 评分约束
    if activity_total < 40:        max_act_by_score = 1
    elif activity_total < 60:      max_act_by_score = 2
    else:                          max_act_by_score = 3

    max_activity = min(max_act_by_age, max_act_by_score)
    return tcm_level, max_activity


def solve_single_patient(initial_tanshi, age_group, activity_total,
                         lambda_param=15, max_cost=2000):
    """
    为单个患者求解最优干预方案。
    枚举全部可行组合(≤90种)，提取Pareto最优解。

    参数:
        initial_tanshi: 初始痰湿积分
        lambda_param: 成本-效果权衡参数 (元/分)
        max_cost:      6个月总成本上限

    返回:
        Pareto最优解集 (三种推荐方案: 最省钱/性价比/效果优先)
    """
    tcm_level, max_act = get_constraints(age_group, activity_total, initial_tanshi)

    solutions = []
    for tcm_l in range(tcm_level, 4):          # 调理级别
        tcm_cost = TCM_LEVELS[tcm_l]['cost_month'] * 6
        for act_l in range(1, max_act + 1):     # 活动强度
            act_cps = ACTIVITY_LEVELS[act_l]['cost_per_session']
            for sess_n in range(1, 11):          # 周频次 1-10
                act_cost = act_cps * sess_n * 24
                total_cost = tcm_cost + act_cost
                if total_cost > max_cost:
                    continue

                # 计算痰湿积分下降 (逐月递减模型)
                mr = calc_monthly_reduction(act_l, sess_n)
                remaining = initial_tanshi
                total_reduction = 0
                for _ in range(6):
                    red = remaining * mr
                    total_reduction += red
                    remaining -= red

                # 综合目标: 最小化 成本 - lambda × 下降量
                obj = total_cost - lambda_param * total_reduction
                solutions.append({
                    'tcm_level': tcm_l, 'act_level': act_l,
                    'sessions': sess_n, 'cost': total_cost,
                    'reduction': total_reduction, 'objective': obj
                })

    # 提取三套推荐方案
    result = {'cheapest': None, 'balanced': None, 'best_effect': None}

    # A-最省钱: 成本最低
    cheapest = min(solutions, key=lambda s: s['cost'])
    result['cheapest'] = cheapest

    # C-效果优先: 下降量最大
    best_effect = max(solutions, key=lambda s: s['reduction'])
    result['best_effect'] = best_effect

    # B-性价比最优: 目标函数最优 (λ平衡)
    balanced = min(solutions, key=lambda s: s['objective'])
    result['balanced'] = balanced

    return result


def analyze_all_patients(df_tanshi_patients):
    """
    对全部痰湿体质患者求解，统计各年龄组方案偏好
    """
    all_results = []
    for _, patient in df_tanshi_patients.iterrows():
        sol = solve_single_patient(
            patient['tanshi'], patient['age_group'], patient['activity_total'])
        sol['sample_id'] = patient['sample_id']
        all_results.append(sol)

    results_df = pd.DataFrame(all_results)

    # 各年龄组统计
    stats = {}
    for ag in sorted(results_df['age_group'].unique()):
        sub = results_df[results_df['age_group'] == ag]
        stats[f'年龄组{ag}'] = {
            '人数': len(sub),
            '平均成本': sub['balanced'].apply(lambda x: x['cost']).mean(),
            '平均下降': sub['balanced'].apply(lambda x: x['reduction']).mean(),
        }
    return stats


# ==================== 辅助分析函数 ====================

def sensitivity_analysis(df_tanshi_patients, lambda_range=(10, 30)):
    """
    灵敏度分析: 评估λ参数在10-30范围内变化时
    最优方案的成本和下降量变化幅度
    """
    for lam in range(lambda_range[0], lambda_range[1] + 1, 5):
        costs, reductions = [], []
        for _, patient in df_tanshi_patients.head(100).iterrows():
            sol = solve_single_patient(
                patient['tanshi'], patient['age_group'],
                patient['activity_total'], lambda_param=lam)
            costs.append(sol['balanced']['cost'])
            reductions.append(sol['balanced']['reduction'])
        print(f"  lambda={lam:2d}: 平均成本={np.mean(costs):.1f}元, "
              f"平均下降={np.mean(reductions):.1f}分")
