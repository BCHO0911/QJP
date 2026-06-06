import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docx import Document
from docx.shared import Inches
from tools.docx.docx_helpers import set_chinese_font


def build_docx_from_json(json_path, out_path=None):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    manuscript = data.get('manuscript', '')
    references = data.get('references', [])

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # Title (first line of manuscript)
    title_line = manuscript.splitlines()[0] if manuscript else '论文'
    title = doc.add_heading('', level=0)
    run = title.add_run(title_line)
    set_chinese_font(run, name='宋体', size=16)
    run.bold = True

    # Body: remaining lines
    body_lines = manuscript.splitlines()[1:]
    for line in body_lines:
        if not line.strip():
            doc.add_paragraph()
            continue
        # If line starts with Chinese section marker like 一、 or 1., make heading
        if line.strip().startswith(('一、', '二、', '三、')) or line.strip().endswith('：'):
            h = doc.add_heading(line.strip(), level=1)
            set_chinese_font(h.runs[0], name='宋体', size=12)
        else:
            p = doc.add_paragraph()
            r = p.add_run(line.strip())
            set_chinese_font(r, name='宋体', size=11)

    # References
    doc.add_page_break()
    doc.add_heading('参考文献', level=1)
    for ref in references:
        idx = ref.get('id')
        raw = ref.get('raw') or ''
        p = doc.add_paragraph(f'[{idx}] {raw}')
        set_chinese_font(p.runs[0], name='宋体', size=10)

    out_dir = ROOT / 'output'
    out_dir.mkdir(parents=True, exist_ok=True)
    if not out_path:
        out_path = str(out_dir / '摩尔定律_终结与体系结构_最终.docx')
    doc.save(out_path)
    return out_path


if __name__ == '__main__':
    json_path = os.path.join(os.getcwd(), 'manuscript.json')
    print('读取：', json_path)
    out = build_docx_from_json(json_path)
    print('已生成：', out)
