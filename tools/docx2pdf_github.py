#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx → GitHub可预览PDF 转换工具
用法:  python tools/docx2pdf_github.py

依赖: pip install fpdf2 python-docx
原理: 嵌入 Windows 中文字体，GitHub 浏览器能正常渲染
"""

import os, sys

# 字体配置
FONT_DIR = 'C:/Windows/Fonts'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def convert(docx_path, pdf_path, title='', body_font='FangSong', title_font='SimHei',
            body_size=12, title_size=16):
    """
    将 docx 转换为嵌入中文字体的 PDF
    """
    from docx import Document
    from fpdf import FPDF

    doc = Document(docx_path)
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margin(20)
    pdf.add_page()

    # 注册字体
    for name, fname in [('SimSun', 'simsun.ttc'), ('SimHei', 'simhei.ttf'),
                         ('FangSong', 'simfang.ttf'), ('SimKai', 'simkai.ttf')]:
        fp = os.path.join(FONT_DIR, fname)
        if os.path.exists(fp):
            pdf.add_font(name, '', fp)

    W = 170  # 可用宽度

    # 标题
    pdf.set_font(title_font, '', title_size)
    pdf.multi_cell(W, 10, title, align='C')
    pdf.ln(5)

    # 正文
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            pdf.ln(3)
            continue
        if text == title:
            continue
        # 检测一级标题（"一、" "二、" "前言" "结语"）
        is_heading = (text.startswith(('一、', '二、', '三、', '四、', '五、'))
                      or text in ('前言', '结语', '参考文献')
                      or text.endswith('：'))
        # 检测小标题（（一）等）
        is_subheading = text.startswith('（') and text.endswith('）')

        if is_heading:
            pdf.set_font('SimHei', '', 13)
            pdf.multi_cell(W, 8, text, align='L')
        elif is_subheading:
            pdf.set_font('SimHei', '', 12)
            pdf.multi_cell(W, 7, text, align='L')
        else:
            pdf.set_font(body_font, '', body_size)
            # 首行缩进2字符
            pdf.set_x(20 + 7)
            pdf.multi_cell(W - 7, 7, text, align='L')

    pdf.output(pdf_path)
    return os.path.getsize(pdf_path)


def find_docx(dir_path):
    """在目录中找docx文件（排除临时文件）"""
    if not os.path.exists(dir_path):
        return None
    for f in os.listdir(dir_path):
        if f.endswith('.docx') and not f.startswith('~'):
            return os.path.join(dir_path, f)
    return None


def main():
    # ====== 需要转换的论文 ======
    papers = [
        {
            'dir': '马原论文',
            'title': '特朗普访华商界代表团的马克思主义解读',
            'body_font': 'FangSong',
            'title_font': 'SimHei',
            'body_size': 12,
            'title_size': 16,
        },
        {
            'dir': '形势与政策论文',
            'title1': '科技强国视域下的大国担当\n——从中国科技崛起到计科学子的时代使命',
            'title2': '关于大学生AI工具使用情况的调查与分析',
        },
    ]

    for paper in papers:
        dir_path = os.path.join(BASE, paper['dir'])
        docx_path = find_docx(dir_path)
        if not docx_path:
            print(f'⚠ 未找到docx文件: {dir_path}')
            continue

        if paper['dir'] == '形势与政策论文':
            # 有2篇论文，需要分别处理
            pdf_dir = dir_path

            # 第一篇：结课论文（宋体正文，黑体标题）
            for t, name in [(paper['title1'], '结课论文'), (paper['title2'], '实践报告')]:
                pdf_path = os.path.join(pdf_dir, f'全佳鹏_计科2402_220241090221_{name}.pdf')
                # 对实践报告用临时副本
                size = convert(docx_path, pdf_path,
                               title=t, body_font='SimSun', title_font='SimHei',
                               body_size=12, title_size=16)
                print(f'✅ {name}: {pdf_path} ({size/1024:.0f}KB)')
        else:
            pdf_path = os.path.join(dir_path, '53全佳鹏_github.pdf')
            size = convert(docx_path, pdf_path,
                           title=paper['title'],
                           body_font=paper['body_font'],
                           title_font=paper['title_font'],
                           body_size=paper['body_size'],
                           title_size=paper['title_size'])
            print(f'✅ {paper[\"dir\"]}: {pdf_path} ({size/1024:.0f}KB)')

    print('\n🎉 全部转换完成！推送到 GitHub 后刷新即可查看。')


if __name__ == '__main__':
    main()
