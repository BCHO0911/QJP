#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将三篇论文的docx内容提取为Markdown格式"""

from docx import Document
import os, sys

def docx_to_md(docx_path, title):
    """将docx中的文本提取为markdown格式"""
    doc = Document(docx_path)
    lines = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            lines.append('')
            continue

        # 检测是否是标题/一级标题（黑体加粗通常是一级标题）
        runs = p.runs
        if runs:
            run = runs[0]
            # 检查字体是否是黑体（SimHei）或加粗
            is_bold = run.bold
            font_name = run.font.name
            # 如果段落是居中的，可能是大标题
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            is_center = p.alignment == WD_ALIGN_PARAGRAPH.CENTER

            if is_center and len(text) < 60:
                lines.append(f'# {text}')
                lines.append('')
                continue

            # 一级标题: 黑体加粗且较短
            if is_bold and len(text) < 40 and any(kw in text for kw in ['一、', '二、', '三、', '前言', '结语', '参考文']):
                lines.append(f'## {text}')
                lines.append('')
                continue

            if is_bold and len(text) < 60 and any(kw in text for kw in ['（一）', '（二）', '（三）', '故事简', '故事解', '内容摘', '关键词']):
                lines.append(f'### {text}')
                lines.append('')
                continue

        # 普通正文
        lines.append(text)

    return '\n'.join(lines)

# ============================================================

base_dir = 'd:/GIT/public'
papers = [
    {
        'docx': '形势与政策/全佳鹏 计科2402 220241090221.docx',
        'md': '形势与政策论文/README.md',
        'title': '科技强国视域下的大国担当——从中国科技崛起到计科学子的时代使命'
    },
    {
        'docx': '形势与政策/全佳鹏 计科2402 220241090221-实践报告.docx',
        'md': '形势与政策论文/README.md',
        'title': '关于大学生AI工具使用情况的调查与分析',
        'append': True
    },
    {
        'docx': '马原/53全佳鹏.docx',
        'md': '马原论文/README.md',
        'title': '特朗普访华商界代表团的马克思主义解读'
    }
]

for paper in papers:
    docx_path = os.path.join(base_dir, paper['docx'])
    md_path = os.path.join(base_dir, paper['md'])

    if not os.path.exists(docx_path):
        print(f'跳过，文件不存在: {docx_path}')
        continue

    md_content = docx_to_md(docx_path, paper['title'])

    # 如果是追加模式（形势与政策有两篇），合并到同一个文件
    if paper.get('append') and os.path.exists(md_path):
        existing = open(md_path, 'r', encoding='utf-8').read()
        md_content = existing + '\n\n---\n\n# ' + paper['title'] + '\n\n' + md_content.split('\n', 2)[-1]

    # 写入
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f'已生成: {md_path}')
    print(f'  字数: {len(md_content)} 字符')

print('\n全部完成！')
