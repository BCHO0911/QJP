"""
Add figure numbers (图1, 图2...) to all image captions
"""
import sys, re, os
SKILL_ROOT = r"C:\Users\全佳鹏\.claude\skills\word-document-processor"
sys.path.insert(0, SKILL_ROOT)
from scripts.document import Document

UNPACKED = r"d:\GIT\public\数模\_unpacked_final"
doc = Document(UNPACKED)
editor = doc["word/document.xml"]
NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def C(tag): return f'w:{tag}'
def get_text(p):
    parts = []
    for t in p.getElementsByTagName(C('t')):
        for cn in t.childNodes:
            if cn.nodeValue:
                parts.append(cn.nodeValue)
    import html
    return html.unescape(''.join(parts)).strip()

def set_text(p, text):
    """Replace text content of a paragraph, preserving formatting of first run."""
    runs = p.getElementsByTagName(C('r'))
    if runs:
        # Clear all t elements in first run
        first_run = runs[0]
        t_elements = first_run.getElementsByTagName(C('t'))
        if t_elements:
            # Clear all but first
            for t in t_elements[1:]:
                first_run.removeChild(t)
            # Update first t content
            t_elements[0].firstChild.nodeValue = text
            # Remove remaining runs
            for r in runs[1:]:
                p.removeChild(r)
            return True
    return False

body = editor.dom.getElementsByTagName(C('body'))[0]
paras = body.getElementsByTagName(C('p'))

# ============================================================
# 1. Assign figure numbers to all image captions
# ============================================================
print("[1/2] Adding figure numbers to image captions...")

# Find image paragraphs and their captions
img_count = 0
for i in range(len(paras)):
    p = paras[i]
    # Check if this paragraph contains an image
    has_image = False
    for child in p.getElementsByTagName('*'):
        tag = child.tagName.split('}')[-1]
        if tag == 'drawing':
            has_image = True
            break
        if tag in ['imagedata', 'blip']:
            has_image = True
            break

    if has_image:
        img_count += 1
        # The caption should be in a nearby paragraph
        # Check next paragraph
        if i + 1 < len(paras):
            next_p = paras[i + 1]
            caption_text = get_text(next_p)

            if caption_text and len(caption_text) > 5:
                # Check if it already has a figure number
                if not re.match(r'图\d', caption_text):
                    # Add figure number
                    new_caption = f'图{img_count}  {caption_text.strip()}'
                    # Update the paragraph text
                    runs = next_p.getElementsByTagName(C('r'))
                    if runs:
                        # Find or create t element
                        t_elems = runs[0].getElementsByTagName(C('t'))
                        if t_elems:
                            t_elems[0].firstChild.nodeValue = new_caption
                            # Remove extra runs
                            for r in runs[1:]:
                                next_p.removeChild(r)
                            print(f'  图{img_count}: {caption_text[:40]}')

print(f'\n  Total images: {img_count}')

# ============================================================
# 2. Add appendix code files
# ============================================================
print("[2/2] Adding appendix code (4 files)...")

code_dir = r"d:\GIT\public\数模\附录_代码_精简版"
code_files = [
    ('A.1', '数据加载与预处理模块', 'A1_data_loader.py'),
    ('A.2', '关键指标筛选与体质贡献度分析', 'A2_q1_feature_selection.py'),
    ('A.3', '多维度风险预警模型', 'A3_q2_risk_warning.py'),
    ('A.4', '6个月干预方案优化模型', 'A4_q3_optimization.py'),
]

def create_elem(tag): return editor.dom.createElement(tag if ':' in tag else f'w:{tag}')
def set_w(elem, attr, val): elem.setAttribute(f'w:{attr}', val)

def add_para(text, font='宋体', sz=21, bold=False, jc='left', spacing=240):
    p = create_elem('p')
    pPr = create_elem('pPr')
    if jc:
        jc_e = create_elem('jc')
        set_w(jc_e, 'val', jc)
        pPr.appendChild(jc_e)
    sp = create_elem('spacing')
    set_w(sp, 'line', str(spacing))
    set_w(sp, 'lineRule', 'auto')
    set_w(sp, 'before', '0')
    set_w(sp, 'after', '0')
    pPr.appendChild(sp)
    p.appendChild(pPr)

    r = create_elem('r')
    rPr = create_elem('rPr')
    rf = create_elem('rFonts')
    set_w(rf, 'ascii', font)
    set_w(rf, 'hAnsi', font)
    set_w(rf, 'eastAsia', font)
    set_w(rf, 'cs', font)
    rPr.appendChild(rf)
    sz_e = create_elem('sz')
    set_w(sz_e, 'val', str(sz))
    rPr.appendChild(sz_e)
    szcs = create_elem('szCs')
    set_w(szcs, 'val', str(sz))
    rPr.appendChild(szcs)
    if bold:
        rPr.appendChild(create_elem('b'))
    r.appendChild(rPr)
    t = create_elem('t')
    t.appendChild(editor.dom.createTextNode(text))
    r.appendChild(t)
    p.appendChild(r)
    return p

def add_code_line(line):
    """Add a single code line as a paragraph (Courier New, 8pt)."""
    p = create_elem('p')
    pPr = create_elem('pPr')
    sp = create_elem('spacing')
    set_w(sp, 'line', '240')
    set_w(sp, 'lineRule', 'auto')
    set_w(sp, 'before', '0')
    set_w(sp, 'after', '0')
    pPr.appendChild(sp)
    p.appendChild(pPr)

    r = create_elem('r')
    rPr = create_elem('rPr')
    rf = create_elem('rFonts')
    set_w(rf, 'ascii', 'Courier New')
    set_w(rf, 'hAnsi', 'Courier New')
    rPr.appendChild(rf)
    sz_e = create_elem('sz')
    set_w(sz_e, 'val', '16')
    rPr.appendChild(sz_e)
    r.appendChild(rPr)
    t = create_elem('t')
    t.appendChild(editor.dom.createTextNode(line if line else ' '))
    r.appendChild(t)
    p.appendChild(r)
    return p

# Find position to insert (after the last child)
last_child = body.lastChild
while last_child and last_child.nodeType != last_child.ELEMENT_NODE:
    last_child = last_child.previousSibling

insert_after = last_child

# Add page break before appendix
pb = create_elem('p')
pb_pPr = create_elem('pPr')
pb_r = create_elem('r')
pb_br = create_elem('br')
pb_br.setAttribute('w:type', 'page')
pb_r.appendChild(pb_br)
pb.appendChild(pb_pPr)
pb.appendChild(pb_r)
body.appendChild(pb)

# Main heading
h = add_para('附录A  支撑材料代码清单', font='黑体', sz=28, bold=True, jc='center', spacing=240)
body.appendChild(h)

note = add_para('（以下代码为论文中三个问题建模与求解的核心实现，完整代码见支撑材料文件）',
                font='宋体', sz=21, jc='center', spacing=240)
body.appendChild(note)

for sec_id, desc, fname in code_files:
    fpath = os.path.join(code_dir, fname)
    if not os.path.exists(fpath):
        print(f'  WARNING: {fpath} not found')
        continue

    # Section heading
    sec_h = add_para(f'附录{sec_id}  {desc}', font='黑体', sz=24, bold=True, jc='left', spacing=240)
    body.appendChild(sec_h)

    # Code lines
    with open(fpath, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            # Remove trailing newline
            clean_line = line.rstrip('\n').rstrip('\r')
            p_code = add_code_line(clean_line)
            body.appendChild(p_code)

    # Spacing between sections
    spacer = add_para('', font='宋体', sz=16, spacing=120)
    body.appendChild(spacer)
    print(f'  Added {sec_id}: {desc}')

print('\nSaving...')
doc.save(validate=False)
print('Done!')
