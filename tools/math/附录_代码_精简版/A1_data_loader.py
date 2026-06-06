# -*- coding: utf-8 -*-
"""
附录A.1  数据加载与预处理模块 (精简版)
"""

import pandas as pd
import numpy as np

# ==================== 列名定义 ====================
ENGLISH_COLUMNS = [
    'sample_id', 'constitution_type',           # 样本ID, 体质类型
    'pinghe', 'qixu', 'yangxu', 'yinxu',       # 9种体质积分
    'tanshi', 'shire', 'xueyu', 'qiyu', 'tebing',
    'adl_item1', 'adl_item2', 'adl_item3',      # ADL(穿衣/进食/步行)
    'adl_item4', 'adl_item5', 'adl_total',      # ADL(如厕/洗澡/总分)
    'iadl_item1', 'iadl_item2', 'iadl_item3',   # IADL(购物/做饭/理财)
    'iadl_item4', 'iadl_item5', 'iadl_total',   # IADL(交通/服药/总分)
    'activity_total',                            # 活动量表总分
    'hdl_c', 'ldl_c', 'tg', 'tc',              # 4项血脂指标
    'glucose', 'uric_acid', 'bmi',             # 代谢指标
    'hyperlipidemia', 'lipid_type',             # 高血脂诊断标签
    'age_group', 'gender', 'smoking', 'drinking' # 人口学信息
]

# ==================== 核心函数 ====================

def load_data(path=None):
    """加载并清洗数据，返回DataFrame"""
    if path is None:
        path = "附件数据.xlsx"
    df = pd.read_excel(path)
    df.columns = ENGLISH_COLUMNS
    int_cols = ['sample_id', 'constitution_type', 'hyperlipidemia',
                'age_group', 'gender', 'smoking', 'drinking',
                'adl_total', 'iadl_total', 'activity_total']
    for c in int_cols:
        df[c] = df[c].astype(int)
    return df


def add_derived_features(df):
    """构造衍生特征：血脂异常标志、TC/HDL比值、非HDL胆固醇"""
    # 血脂异常标志（基于临床参考范围）
    df['tc_abnormal'] = ((df['tc'] < 3.1) | (df['tc'] > 6.2)).astype(int)
    df['tg_abnormal'] = ((df['tg'] < 0.56) | (df['tg'] > 1.7)).astype(int)
    df['ldl_abnormal'] = ((df['ldl_c'] < 2.07) | (df['ldl_c'] > 3.1)).astype(int)
    df['hdl_abnormal'] = ((df['hdl_c'] < 1.04) | (df['hdl_c'] > 1.55)).astype(int)
    df['abnormal_count'] = (df['tc_abnormal'] + df['tg_abnormal'] +
                            df['ldl_abnormal'] + df['hdl_abnormal'])
    df['tc_hdl_ratio'] = df['tc'] / df['hdl_c']      # 心血管风险指标
    df['non_hdl'] = df['tc'] - df['hdl_c']            # 非HDL胆固醇
    df['is_tanshi'] = (df['constitution_type'] == 5).astype(int)
    return df
