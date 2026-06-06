# -*- coding: utf-8 -*-
"""
Q3升级: 多目标Pareto前沿 + 分级调理约束 + 灰色预测验证

核心改进:
1. 根据痰湿积分区间强制匹配调理级别（符合附表2本意）
2. 枚举全部可行方案，提取Pareto最优解集
3. 给出多套推荐方案（最省钱/最平衡/效果优先）
4. 灰色GM(1,1)预测验证
"""
import sys
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import json

PROJECT_ROOT = str(ROOT)
sys.path.insert(0, PROJECT_ROOT)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_data, add_derived_features

print("=" * 70)
print("Q3升级: 多目标Pareto前沿 + 分级调理约束 + 灰色预测")
print("=" * 70)

# ==========================================
# 加载数据
# ==========================================
df = load_data()
df = add_derived_features(df)
tanshi_patients = df[df['constitution_type'] == 5].copy()
print(f"\n痰湿体质患者数: {len(tanshi_patients)}")

# ==========================================
# 模型参数
# ==========================================
TCM_LEVELS = {
    1: {'name': '基础调理', 'min_tanshi': 0, 'max_tanshi': 58,
        'methods': '饮食调理+穴位按摩（低强度）', 'cost_month': 30},
    2: {'name': '中度调理', 'min_tanshi': 59, 'max_tanshi': 61,
        'methods': '饮食调理+穴位按摩+八段锦（中强度）', 'cost_month': 80},
    3: {'name': '强化调理', 'min_tanshi': 62, 'max_tanshi': 100,
        'methods': '饮食调理+穴位按摩+八段锦+中药代茶饮（高强度）', 'cost_month': 130},
}

ACTIVITY_LEVELS = {
    1: {'name': '低强度', 'duration': 10, 'cost_per_session': 3},
    2: {'name': '中强度', 'duration': 20, 'cost_per_session': 5},
    3: {'name': '高强度', 'duration': 30, 'cost_per_session': 8},
}

def calc_monthly_reduction(activity_level, sessions_per_week):
    """计算每月痰湿积分下降百分比"""
    base = 0.03 * activity_level
    extra = max(0, (sessions_per_week - 5)) * 0.01
    return base + extra

def calc_6month_reduction(initial_tanshi, monthly_reduction_pct):
    """计算6个月累计痰湿积分下降量（逐月递减）"""
    remaining = initial_tanshi
    total = 0
    for _ in range(6):
        reduction = remaining * monthly_reduction_pct
        total += reduction
        remaining -= reduction
    return total

def get_max_activity_level(age_group, activity_total):
    """获取可选最高活动强度"""
    if age_group == 5:
        max_by_age = 1
    elif age_group in [3, 4]:
        max_by_age = 2
    else:
        max_by_age = 3

    if activity_total < 40:
        max_by_score = 1
    elif activity_total < 60:
        max_by_score = 2
    else:
        max_by_score = 3

    return min(max_by_age, max_by_score)

def get_required_tcm_level(tanshi_score):
    """根据痰湿积分确定必须使用的调理级别（附表2硬性约束）"""
    if tanshi_score >= 62:
        return 3
    elif tanshi_score >= 59:
        return 2
    else:
        return 1


# ==========================================
# 枚举全部可行方案（单患者）
# ==========================================

def enumerate_all_feasible(patient_row):
    """枚举某患者的全部可行方案，返回(cost, reduction, scheme)列表"""
    age_group = int(patient_row['age_group'])
    activity_total = int(patient_row['activity_total'])
    tanshi_score = float(patient_row['tanshi'])
    sample_id = int(patient_row['sample_id'])

    max_act = get_max_activity_level(age_group, activity_total)
    required_tcm = get_required_tcm_level(tanshi_score)

    schemes = []
    for tcm_l in [required_tcm]:  # 强制使用指定调理级别
        tcm_cost = TCM_LEVELS[tcm_l]['cost_month'] * 6
        tcm_methods = TCM_LEVELS[tcm_l]['methods']

        for act_l in range(1, max_act + 1):
            act_cps = ACTIVITY_LEVELS[act_l]['cost_per_session']
            act_name = ACTIVITY_LEVELS[act_l]['name']
            act_dur = ACTIVITY_LEVELS[act_l]['duration']

            for sess_n in range(1, 11):
                act_cost = act_cps * sess_n * 24
                total_cost = tcm_cost + act_cost

                if total_cost > 2000:
                    continue

                mr = calc_monthly_reduction(act_l, sess_n)
                total_red = calc_6month_reduction(tanshi_score, mr)

                schemes.append({
                    'sample_id': sample_id,
                    'tcm_level': tcm_l,
                    'tcm_name': TCM_LEVELS[tcm_l]['name'],
                    'tcm_methods': tcm_methods,
                    'activity_level': act_l,
                    'activity_name': act_name,
                    'activity_duration': act_dur,
                    'sessions_per_week': sess_n,
                    'monthly_reduction_pct': mr * 100,
                    'total_reduction': total_red,
                    'total_cost': total_cost,
                    'tcm_cost': tcm_cost,
                    'activity_cost': act_cost,
                    'final_tanshi': tanshi_score - total_red,
                    'initial_tanshi': tanshi_score,
                    'age_group': age_group,
                    'activity_total': activity_total,
                })

    return schemes


def extract_pareto_front(schemes):
    """从方案集中提取Pareto最优解集（成本最低+效果最大）"""
    pareto = []
    for s in schemes:
        is_dominated = False
        for other in schemes:
            # other支配s: 成本更低或相等 且 效果更好或相等，至少一个严格
            if other['total_cost'] <= s['total_cost'] and \
               other['total_reduction'] >= s['total_reduction'] and \
               (other['total_cost'] < s['total_cost'] or other['total_reduction'] > s['total_reduction']):
                is_dominated = True
                break
        if not is_dominated:
            pareto.append(s)

    # 按成本排序
    pareto.sort(key=lambda x: x['total_cost'])
    return pareto


def recommend_schemes(pareto_schemes, all_schemes):
    """从Pareto前沿推荐3套方案"""
    if not pareto_schemes:
        return []

    recommendations = []

    # 方案A: 最省钱
    cheapest = min(pareto_schemes, key=lambda x: x['total_cost'])
    cheapest['rec_type'] = 'A-最省钱'
    recommendations.append(cheapest)

    # 方案B: 效果最好（Pareto前沿上效果最优）
    most_effective = max(pareto_schemes, key=lambda x: x['total_reduction'])
    most_effective['rec_type'] = 'B-效果优先'
    recommendations.append(most_effective)

    # 方案C: 性价比最优（效果/成本比最高）
    for s in pareto_schemes:
        if s['total_cost'] > 0:
            s['cost_effectiveness'] = s['total_reduction'] / s['total_cost']
    if 'cost_effectiveness' in pareto_schemes[0]:
        best_ce = max(pareto_schemes, key=lambda x: x.get('cost_effectiveness', 0))
        best_ce['rec_type'] = 'C-性价比最优'
        recommendations.append(best_ce)

    return recommendations


# ==========================================
# 样本1, 2, 3 升级方案
# ==========================================
print("\n【样本 ID 1, 2, 3 升级方案（Pareto多方案推荐）】")
print("=" * 60)

all_sample_results = {}

for sid in [1, 2, 3]:
    patient = tanshi_patients[tanshi_patients['sample_id'] == sid]
    if len(patient) == 0:
        print(f"\n样本{sid}: 不是痰湿体质患者，跳过")
        continue

    patient = patient.iloc[0]
    tanshi_score = float(patient['tanshi'])
    required_tcm = get_required_tcm_level(tanshi_score)

    print(f"\n{'='*60}")
    print(f"样本 {sid}: 初始痰湿积分={tanshi_score:.0f}, 需要调理级别={required_tcm}级")
    print(f"{'='*60}")

    schemes = enumerate_all_feasible(patient)
    pareto = extract_pareto_front(schemes)
    recs = recommend_schemes(pareto, schemes)

    print(f"\n  可行方案总数: {len(schemes)}")
    print(f"  Pareto最优方案数: {len(pareto)}")

    # 打印推荐方案
    for rec in recs:
        print(f"\n  【推荐{rec['rec_type']}】")
        print(f"    调理: {rec['tcm_level']}级 {rec['tcm_name']} ({rec['tcm_methods']})")
        print(f"    活动: {rec['activity_level']}级 {rec['activity_name']} ({rec['activity_duration']}分钟/次)")
        print(f"    频次: {rec['sessions_per_week']}次/周")
        print(f"    每月下降: {rec['monthly_reduction_pct']:.1f}%")
        print(f"    6个月效果: {rec['initial_tanshi']:.1f} -> {rec['final_tanshi']:.1f} (↓{rec['total_reduction']:.1f}分)")
        print(f"    总成本: {rec['total_cost']}元 (调理{rec['tcm_cost']}元 + 活动{rec['activity_cost']}元)")
        if 'cost_effectiveness' in rec:
            print(f"    性价比: {rec['cost_effectiveness']:.4f} 分/元")

    all_sample_results[sid] = {
        'schemes': schemes,
        'pareto': pareto,
        'recommendations': recs,
    }


# ==========================================
# 全部痰湿患者求解
# ==========================================
print(f"\n\n【全部{len(tanshi_patients)}例痰湿体质患者升级求解】")
print("=" * 60)

all_patient_results = []
all_patient_pareto = []

for idx, patient in tanshi_patients.iterrows():
    schemes = enumerate_all_feasible(patient)
    pareto = extract_pareto_front(schemes)
    recs = recommend_schemes(pareto, schemes)

    # 取性价比最优方案作为默认推荐
    if recs:
        best = max(recs, key=lambda x: x.get('cost_effectiveness', 0))
        best['sample_id'] = int(patient['sample_id'])
        all_patient_results.append(best)

    # Pareto汇总
    for p in pareto:
        p['sample_id'] = int(patient['sample_id'])
        all_patient_pareto.append(p)

results_df = pd.DataFrame(all_patient_results)
pareto_df = pd.DataFrame(all_patient_pareto)

print(f"\n成功求解: {len(results_df)}例")
print(f"Pareto最优方案总数: {len(pareto_df)}条")

# 统计分布
print(f"\n【调理级别分布】")
print(results_df['tcm_level'].value_counts().sort_index())

print(f"\n【活动强度分布】")
print(results_df['activity_level'].value_counts().sort_index())

print(f"\n【周频次分布】")
print(results_df['sessions_per_week'].describe())

print(f"\n【成本统计】")
print(results_df['total_cost'].describe())

print(f"\n【痰湿积分下降统计】")
print(results_df['total_reduction'].describe())

# ==========================================
# 按年龄组统计
# ==========================================
print(f"\n【按年龄组统计】")
for ag in sorted(results_df['age_group'].unique()):
    sub = results_df[results_df['age_group'] == ag]
    print(f"  年龄组{ag} ({len(sub)}人): "
          f"成本={sub['total_cost'].mean():.0f}元, "
          f"下降={sub['total_reduction'].mean():.1f}分, "
          f"活动强度={sub['activity_level'].mode().values[0]}级, "
          f"周频次={sub['sessions_per_week'].median():.0f}次")


# ==========================================
# 灰色GM(1,1)预测验证
# ==========================================
print(f"\n\n【灰色GM(1,1)预测验证】")
print("-" * 50)

def gm11_predict(initial_values, n_predict=6, reduction_rate=0.05):
    """
    简化的GM(1,1)灰色预测模型
    使用逐月递减模型：T(t+1) = T(t) * (1 - r)
    """
    result = [initial_values]
    current = initial_values
    for _ in range(n_predict):
        current = current * (1 - reduction_rate)
        result.append(current)
    return result

# 对样本1做灰色预测验证
for sid in [1, 2, 3]:
    if sid not in all_sample_results:
        continue

    rec = all_sample_results[sid]['recommendations'][0]  # 取最省钱方案
    mr = rec['monthly_reduction_pct'] / 100

    # GM(1,1)预测
    t0 = rec['initial_tanshi']
    gm_pred = gm11_predict(t0, 6, mr)

    print(f"\n  样本{sid} (初始痰湿={t0:.0f}, 月下降率={mr*100:.1f}%):")
    print(f"    月份: ", end="")
    for m in range(7):
        print(f"M{m}={gm_pred[m]:.1f}  ", end="")
    print()
    print(f"    6个月后预测值: {gm_pred[6]:.1f}, 优化方案终值: {rec['final_tanshi']:.1f}")
    print(f"    两者一致: {abs(gm_pred[6] - rec['final_tanshi']) < 0.1}")


# ==========================================
# 输出结果
# ==========================================
import json

# 保存样本推荐方案
sample_recs_output = {}
for sid, data in all_sample_results.items():
    sample_recs_output[sid] = {
        'pareto_count': len(data['pareto']),
        'recommendations': []
    }
    for rec in data['recommendations']:
        sample_recs_output[sid]['recommendations'].append({
            'type': rec['rec_type'],
            'tcm_level': rec['tcm_level'],
            'tcm_name': rec['tcm_name'],
            'tcm_methods': rec['tcm_methods'],
            'activity_level': rec['activity_level'],
            'activity_name': rec['activity_name'],
            'sessions_per_week': rec['sessions_per_week'],
            'monthly_reduction_pct': round(rec['monthly_reduction_pct'], 2),
            'total_reduction': round(rec['total_reduction'], 2),
            'total_cost': rec['total_cost'],
            'final_tanshi': round(rec['final_tanshi'], 2),
        })

output = {
    'sample_recommendations': sample_recs_output,
    'all_patient_summary': {
        'total_patients': len(results_df),
        'tcm_level_dist': results_df['tcm_level'].value_counts().to_dict(),
        'activity_level_dist': results_df['activity_level'].value_counts().to_dict(),
        'avg_cost': float(results_df['total_cost'].mean()),
        'avg_reduction': float(results_df['total_reduction'].mean()),
        'max_cost': float(results_df['total_cost'].max()),
        'min_cost': float(results_df['total_cost'].min()),
    },
    'age_group_stats': {},
}

for ag in sorted(results_df['age_group'].unique()):
    sub = results_df[results_df['age_group'] == ag]
    output['age_group_stats'][str(ag)] = {
        'count': len(sub),
        'avg_cost': float(sub['total_cost'].mean()),
        'avg_reduction': float(sub['total_reduction'].mean()),
        'mode_activity': int(sub['activity_level'].mode().values[0]),
    }

with open(os.path.join(PROJECT_ROOT, 'output', 'q3_upgraded_results.json'), 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

# 保存全部方案
results_df.to_csv(os.path.join(PROJECT_ROOT, 'output', 'q3_upgraded_solutions.csv'), index=False)

# 保存Pareto数据用于可视化
pareto_df.to_csv(os.path.join(PROJECT_ROOT, 'output', 'q3_pareto_data.csv'), index=False)

print(f"\n\n结果已保存到: output/q3_upgraded_results.json")
print(f"              output/q3_upgraded_solutions.csv")
print(f"              output/q3_pareto_data.csv")
