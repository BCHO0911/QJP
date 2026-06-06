import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_LINE_SPACING, WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from tools.docx.docx_helpers import set_chinese_font


def add_page_number_footer(doc):
    section = doc.sections[0]
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    # Add PAGE field
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), 'PAGE')
    p._p.append(fld)


def format_docx(input_path, out_path):
    doc = Document(input_path)

    # Clean out CSS/HTML remnants produced by doc->docx conversion
    bad_markers = ['@font-face', 'MicrosoftInternetExplorer', 'mso-', 'p.Mso', 'div.Section0', '{', '}', 'Normal0', 'MsoNormal']
    paras_to_remove = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        low = text
        if any(marker in low for marker in bad_markers):
            paras_to_remove.append(p)
        # also remove long CSS lines or very long single-line code
        if len(text) > 300 and (';' in text or ':' in text):
            paras_to_remove.append(p)

    # remove identified paragraphs
    for p in paras_to_remove:
        try:
            p._p.getparent().remove(p._p)
        except Exception:
            pass

    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if i == 0:
            # Title: 黑体 小二 加粗 -> use size 18
            for r in p.runs:
                set_chinese_font(r, name='黑体', size=18, bold=True)
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        elif text.startswith('作者：') or text.startswith('作者'):
            for r in p.runs:
                set_chinese_font(r, name='宋体', size=10.5)
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        elif text.startswith('摘 要') or text.startswith('关键词') or text == '参考文献':
            # headings for these
            for r in p.runs:
                set_chinese_font(r, name='宋体', size=10.5, bold=True)
        elif text.startswith(('一、', '二、', '三、', '四、')) or (p.style.name.startswith('Heading')):
            # 一级标题 assume
            for r in p.runs:
                set_chinese_font(r, name='宋体', size=12, bold=True)
            # 一级标题：段前、段后单倍行距
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        else:
            # Body text
            for r in p.runs:
                set_chinese_font(r, name='宋体', size=10.5)
            # 正文：首行缩进2字符约等于21磅（模板使用21pt）
            p.paragraph_format.first_line_indent = Pt(21)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            p.paragraph_format.line_spacing = Pt(19)

    # References formatting: ensure each reference is small font
    # Find '参考文献' paragraph index
    for idx, p in enumerate(doc.paragraphs):
        if p.text.strip() == '参考文献':
            start = idx + 1
            break
    else:
        start = None

    if start is not None:
        for p in doc.paragraphs[start:]:
            if not p.text.strip():
                continue
            for r in p.runs:
                # 参考文献 9 磅，行距单倍
                set_chinese_font(r, name='Times New Roman', size=9)
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

    add_page_number_footer(doc)
    # If output exists, try to remove to avoid permission issues
    try:
        if os.path.exists(out_path):
            os.remove(out_path)
    except Exception:
        pass
    doc.save(out_path)
    return out_path


if __name__ == '__main__':
    in_doc = os.path.join('output', '摩尔定律_终结与体系结构_最终.docx')
    out_doc = os.path.join('output', '摩尔定律_终结与体系结构_格式化_v2.docx')
    print('格式化：', in_doc)
    formatted = format_docx(in_doc, out_doc)
    print('保存为：', formatted)
    # Convert to PDF
    try:
        from docx2pdf import convert
        out_pdf = os.path.join('output', '摩尔定律_终结与体系结构_格式化_v2.pdf')
        convert(formatted, out_pdf)
        print('已生成 PDF：', out_pdf)
    except Exception as e:
        print('PDF 转换失败：', e)
