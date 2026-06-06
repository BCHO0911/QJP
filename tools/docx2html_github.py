#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx → GitHub可预览HTML 转换工具
用法:  python tools/docx2html_github.py
"""

import os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def docx_to_html(docx_path, title):
    """将 docx 论文内容转换为美观的 HTML"""
    import sys
    # 移除 tools 目录避免与 python-docx 包冲突
    sys.path = [p for p in sys.path if 'tools' not in p.replace('\\\\', '/').replace('\\\\', '/')]
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document(docx_path)

    # 构建 HTML 正文内容
    body_html = ''
    is_title_skipped = False

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            body_html += '<p class="empty">&nbsp;</p>\n'
            continue

        # 跳过封面的大标题（已在HTML标题中）
        if not is_title_skipped and (text == title
                                     or ('科技强国视域' in text and len(text) > 15)
                                     or ('关于大学生AI' in text and len(text) > 15)
                                     or ('特朗普访华' in text and len(text) > 15)):
            is_title_skipped = True
            continue

        # 判断对齐方式
        is_center = p.alignment == WD_ALIGN_PARAGRAPH.CENTER

        # 判断段落类型
        is_main_heading = (text in ('前言', '结语', '参考文献')
                           or any(text.startswith(x) for x in ('一、', '二、', '三、', '四、', '五、')))
        is_sub_heading = (text.startswith('（') and '）' in text and len(text) < 40)
        is_section_label = text.endswith('：') and len(text) < 30
        is_keywords = text.startswith('关键词')
        is_abstract = text.startswith('内容摘要')
        is_ref = text.startswith('[')

        if is_main_heading:
            body_html += f'<h2>{text}</h2>\n'
        elif is_sub_heading or is_section_label:
            body_html += f'<h3>{text}</h3>\n'
        elif is_keywords or is_abstract:
            body_html += f'<p class="abstract">{text}</p>\n'
        elif is_ref:
            body_html += f'<p class="ref">{text}</p>\n'
        elif is_center:
            body_html += f'<p class="center">{text}</p>\n'
        else:
            body_html += f'<p>{text}</p>\n'

    # 完整 HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #e8e8e8;
    font-family: "宋体", "SimSun", "Noto Serif CJK SC", serif;
    padding: 30px 20px;
  }}
  .paper {{
    max-width: 800px;
    margin: 0 auto;
    background: #fff;
    padding: 60px 70px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
    line-height: 1.8;
    font-size: 14px;
    color: #222;
  }}
  h1 {{
    font-family: "黑体", "SimHei", "Noto Sans CJK SC", sans-serif;
    font-size: 22px;
    text-align: center;
    margin-bottom: 25px;
    font-weight: bold;
  }}
  h2 {{
    font-family: "黑体", "SimHei", "Noto Sans CJK SC", sans-serif;
    font-size: 16px;
    margin: 20px 0 10px 0;
    font-weight: bold;
  }}
  h3 {{
    font-family: "黑体", "SimHei", "Noto Sans CJK SC", sans-serif;
    font-size: 14px;
    margin: 12px 0 6px 0;
    font-weight: bold;
  }}
  p {{
    text-indent: 28px;
    margin-bottom: 6px;
    text-align: justify;
  }}
  p.empty {{
    text-indent: 0;
    height: 10px;
  }}
  p.center {{
    text-indent: 0;
    text-align: center;
    font-weight: bold;
  }}
  p.abstract {{
    text-indent: 28px;
    margin-bottom: 6px;
  }}
  p.ref {{
    text-indent: -28px;
    padding-left: 28px;
    margin-bottom: 4px;
    font-size: 13px;
  }}
  .footer {{
    text-align: center;
    color: #888;
    font-size: 12px;
    margin-top: 30px;
    padding-top: 15px;
    border-top: 1px solid #ddd;
  }}
  @media (max-width: 600px) {{
    .paper {{ padding: 30px 25px; }}
    h1 {{ font-size: 18px; }}
  }}
</style>
</head>
<body>
<div class="paper">
<h1>{title}</h1>
{body_html}
<div class="footer">全佳鹏 · 计科2402 · 220241090221</div>
</div>
</body>
</html>'''
    return html


def find_docx(dir_path):
    if not os.path.exists(dir_path):
        return None
    result = []
    for f in sorted(os.listdir(dir_path)):
        if f.endswith('.docx') and not f.startswith('~'):
            result.append(os.path.join(dir_path, f))
    return result if result else None


def main():
    papers_config = [
        {
            'dir': '形势与政策论文',
            'docs': [
                ('全佳鹏 计科2402 220241090221.docx',
                 '科技强国视域下的大国担当<br>——从中国科技崛起到计科学子的时代使命',
                 '结课论文'),
                ('全佳鹏 计科2402 220241090221-实践报告.docx',
                 '关于大学生AI工具使用情况的调查与分析',
                 '实践报告'),
            ],
            'html_name': 'index.html',
        },
        {
            'dir': '马原论文',
            'docs': [
                ('53全佳鹏.docx',
                 '特朗普访华商界代表团的马克思主义解读',
                 None),
            ],
            'html_name': 'index.html',
        },
    ]

    for cfg in papers_config:
        dir_path = os.path.join(BASE, cfg['dir'])
        if not os.path.exists(dir_path):
            print(f'⚠ 目录不存在: {dir_path}')
            continue

        all_html = ''
        for docx_name, title, label in cfg['docs']:
            docx_path = os.path.join(dir_path, docx_name)
            if not os.path.exists(docx_path):
                print(f'⚠ 文件不存在: {docx_path}')
                continue
            html = docx_to_html(docx_path, title)
            all_html += html if not all_html else html
            print(f'✅ {label or "论文"}: {docx_name}')

        if all_html:
            html_path = os.path.join(dir_path, cfg['html_name'])
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(all_html)
            print(f'📄 HTML已生成: {html_path}')

    print('\n🎉 全部完成！推送到 GitHub 后刷新即可查看。')


if __name__ == '__main__':
    main()
