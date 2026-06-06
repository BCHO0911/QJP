# -*- coding: utf-8 -*-
"""
数据加载与预处理模块
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

# 按Excel列位置定义列名（37列）
ENGLISH_COLUMNS = [
    'sample_id',            # 0
    'constitution_type',    # 1
    'pinghe',               # 2  平和质
    'qixu',                 # 3  气虚质
    'yangxu',               # 4  阳虚质
    'yinxu',                # 5  阴虚质
    'tanshi',               # 6  痰湿质
    'shire',                # 7  湿热质
    'xueyu',                # 8  血瘀质
    'qiyu',                 # 9  气郁质
    'tebing',               # 10 特禀质
    'adl_item1',            # 11 ADL穿衣
    'adl_item2',            # 12 ADL进食/吃饭
    'adl_item3',            # 13 ADL步行/行走
    'adl_item4',            # 14 ADL如厕
    'adl_item5',            # 15 ADL洗澡
    'adl_total',            # 16 ADL总分
    'iadl_item1',           # 17 IADL购物
    'iadl_item2',           # 18 IADL做饭
    'iadl_item3',           # 19 IADL理财
    'iadl_item4',           # 20 IADL交通
    'iadl_item5',           # 21 IADL服药
    'iadl_total',           # 22 IADL总分
    'activity_total',       # 23 活动量表总分
    'hdl_c',                # 24 HDL-C
    'ldl_c',                # 25 LDL-C
    'tg',                   # 26 TG
    'tc',                   # 27 TC
    'glucose',              # 28 空腹血糖
    'uric_acid',            # 29 血尿酸
    'bmi',                  # 30 BMI
    'hyperlipidemia',       # 31 高血脂症标签
    'lipid_type',           # 32 血脂异常分型
    'age_group',            # 33 年龄组
    'gender',               # 34 性别
    'smoking',              # 35 吸烟史
    'drinking',             # 36 饮酒史
]

# 中文体质名称
CONSTITUTION_NAMES = {
    1: '平和质', 2: '气虚质', 3: '阳虚质', 4: '阴虚质',
    5: '痰湿质', 6: '湿热质', 7: '血瘀质', 8: '气郁质', 9: '特禀质'
}

# 血脂指标临床参考范围
LIPID_RANGES = {
    'tc': (3.1, 6.2),       # 总胆固醇 mmol/L
    'tg': (0.56, 1.7),       # 甘油三酯 mmol/L
    'ldl_c': (2.07, 3.1),    # 低密度脂蛋白 mmol/L
    'hdl_c': (1.04, 1.55),   # 高密度脂蛋白 mmol/L
    'glucose': (3.9, 6.1),   # 空腹血糖 mmol/L
    'bmi': (18.5, 23.9),     # BMI
}


def load_data(path=None):
    """加载并清洗数据"""
    if path is None:
        candidates = [
            ROOT / '题目和要求' / 'B题' / 'B题-附件.xlsx',
            ROOT / 'tools' / 'math' / '题目和要求' / 'B题' / 'B题-附件.xlsx',
        ]
        for candidate in candidates:
            if candidate.exists():
                path = candidate
                break
        else:
            raise FileNotFoundError(
                'Cannot find B题-附件.xlsx under the repository root. '
                'Expected it at 题目和要求/B题/B题-附件.xlsx.'
            )

    df = pd.read_excel(path)
    df.columns = ENGLISH_COLUMNS

    # 确保整数列
    int_cols = ['sample_id', 'constitution_type', 'hyperlipidemia', 'lipid_type',
                'age_group', 'gender', 'smoking', 'drinking', 'uric_acid',
                'adl_item1', 'adl_item2', 'adl_item3', 'adl_item4', 'adl_item5',
                'adl_total', 'iadl_item1', 'iadl_item2', 'iadl_item3',
                'iadl_item4', 'iadl_item5', 'iadl_total', 'activity_total']
    for c in int_cols:
        df[c] = df[c].astype(int)

    return df


def add_derived_features(df):
    """构造衍生特征"""
    # 血脂异常标志
    df['tc_abnormal'] = ((df['tc'] < LIPID_RANGES['tc'][0]) | (df['tc'] > LIPID_RANGES['tc'][1])).astype(int)
    df['tg_abnormal'] = ((df['tg'] < LIPID_RANGES['tg'][0]) | (df['tg'] > LIPID_RANGES['tg'][1])).astype(int)
    df['ldl_abnormal'] = ((df['ldl_c'] < LIPID_RANGES['ldl_c'][0]) | (df['ldl_c'] > LIPID_RANGES['ldl_c'][1])).astype(int)
    df['hdl_abnormal'] = ((df['hdl_c'] < LIPID_RANGES['hdl_c'][0]) | (df['hdl_c'] > LIPID_RANGES['hdl_c'][1])).astype(int)
    df['glucose_abnormal'] = ((df['glucose'] < LIPID_RANGES['glucose'][0]) | (df['glucose'] > LIPID_RANGES['glucose'][1])).astype(int)
    df['bmi_abnormal'] = ((df['bmi'] < LIPID_RANGES['bmi'][0]) | (df['bmi'] > LIPID_RANGES['bmi'][1])).astype(int)

    # 异常计数
    df['abnormal_count'] = df['tc_abnormal'] + df['tg_abnormal'] + df['ldl_abnormal'] + df['hdl_abnormal']

    # TC/HDL比值 (动脉粥样硬化风险指标)
    df['tc_hdl_ratio'] = df['tc'] / df['hdl_c']

    # 非HDL胆固醇
    df['non_hdl'] = df['tc'] - df['hdl_c']

    # 痰湿体质二元标志
    df['is_tanshi'] = (df['constitution_type'] == 5).astype(int)

    return df


if __name__ == '__main__':
    df = load_data()
    df = add_derived_features(df)
    print(f"Loaded {len(df)} samples, {len(df.columns)} columns")
    print(f"Hyperlipidemia rate: {df['hyperlipidemia'].mean():.2%}")
    print(f"Tanshi constitution count: {df['is_tanshi'].sum()}")
    out_dir = ROOT / 'output'
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / 'data_processed.csv', index=False)
    print('Saved to output/data_processed.csv')
