"""
Add code appendix to the paper, following CUMCM-C-01 reference style
"""
import sys, os, html as html_mod
SKILL_ROOT = r"C:\Users\全佳鹏\.claude\skills\word-document-processor"
sys.path.insert(0, SKILL_ROOT)
from scripts.document import Document

UNPACKED = r"d:\GIT\public\数模\_unpacked_final"
if not os.path.exists(UNPACKED):
    import subprocess, zipfile
    result = subprocess.run([
        'python', 'C:/Users/全佳鹏/.claude/skills/word-document-processor/ooxml/scripts/unpack.py',
        'd:/temp_paper.docx', UNPACKED
    ], capture_output=True)
    if result.returncode != 0:
        print(f'Failed to unpack: {result.stderr.decode()}')
        exit(1)

doc = Document(UNPACKED)
editor = doc["word/document.xml"]

def C(tag): return f'w:{tag}'
def create(tag): return editor.dom.createElement(tag if ':' in tag else f'w:{tag}')
def set_w(elem, attr, val): elem.setAttribute(f'w:{attr}', val)

def add_paragraph(text, font='宋体', sz=21, bold=False, jc='left', spacing_line=240, first_line=0):
    """Add a paragraph to the document body."""
    p = create('p')
    pPr = create('pPr')

    # Alignment
    if jc:
        jc_elem = create('jc')
        set_w(jc_elem, 'val', jc)
        pPr.appendChild(jc_elem)

    # Spacing
    sp = create('spacing')
    set_w(sp, 'line', str(spacing_line))
    set_w(sp, 'lineRule', 'auto')
    set_w(sp, 'before', '0')
    set_w(sp, 'after', '0')
    pPr.appendChild(sp)

    # Indent
    if first_line:
        ind = create('ind')
        set_w(ind, 'firstLine', str(first_line))
        pPr.appendChild(ind)

    p.appendChild(pPr)

    # Run with text
    r = create('r')
    rPr = create('rPr')
    rf = create('rFonts')
    set_w(rf, 'ascii', font)
    set_w(rf, 'hAnsi', font)
    set_w(rf, 'eastAsia', font)
    set_w(rf, 'cs', font)
    rPr.appendChild(rf)

    sz_elem = create('sz')
    set_w(sz_elem, 'val', str(sz))
    rPr.appendChild(sz_elem)
    szCs = create('szCs')
    set_w(szCs, 'val', str(sz))
    rPr.appendChild(szCs)

    if bold:
        rPr.appendChild(create('b'))
        rPr.appendChild(create('bCs'))

    r.appendChild(rPr)
    t = create('t')
    # Use XML entity encoding for Chinese text
    t.appendChild(editor.dom.createTextNode(text))
    r.appendChild(t)

    p.appendChild(r)
    return p

def add_code_block(code_lines):
    """Add a code block (monospace font)."""
    p = create('p')
    pPr = create('pPr')
    sp = create('spacing')
    set_w(sp, 'line', '240')
    set_w(sp, 'lineRule', 'auto')
    set_w(sp, 'before', '0')
    set_w(sp, 'after', '0')
    pPr.appendChild(sp)
    p.appendChild(pPr)

    r = create('r')
    rPr = create('rPr')
    rf = create('rFonts')
    set_w(rf, 'ascii', 'Courier New')
    set_w(rf, 'hAnsi', 'Courier New')
    set_w(rf, 'eastAsia', 'Courier New')
    set_w(rf, 'cs', 'Courier New')
    rPr.appendChild(rf)

    sz_elem = create('sz')
    set_w(sz_elem, 'val', '16')  # 8pt
    rPr.appendChild(sz_elem)

    t = create('t')
    t.appendChild(editor.dom.createTextNode(code_lines))
    r.appendChild(t)

    p.appendChild(r)
    return p

# Find the body element
body = editor.dom.getElementsByTagName('w:body')[0]

# Find where to insert - after the last child
# First, check if there's an existing appendix we should append to
# Look for '附录' in existing content
existing_captions = []
for p in body.getElementsByTagName('*'):
    for t in p.getElementsByTagName('w:t'):
        if t.firstChild and t.firstChild.nodeValue and '附录' in t.firstChild.nodeValue:
            existing_captions.append(t.firstChild.nodeValue)

print(f'Existing appendix captions: {existing_captions}')

# Get the last paragraph in the body
children = body.childNodes
last_child = None
for i in range(len(children) - 1, -1, -1):
    if children[i].nodeType == children[i].ELEMENT_NODE:
        last_child = children[i]
        break

print('Adding appendix content...')

# Find the position to insert - after the last paragraph
# If there's already an AI tools appendix, insert after it
insert_after = last_child

# Source code files to include
code_files = {
    'A.1': ('数据加载与预处理模块 — data_loader.py', 'src/data_loader.py'),
    'A.2': ('问题一：关键指标筛选与体质贡献度分析 — q1_full.py', 'src/q1/q1_full.py'),
    'A.3': ('问题二：多维度风险预警模型 — q2_full.py', 'src/q2/q2_full.py'),
    'A.4': ('问题三：6个月干预方案优化模型 — q3_full.py', 'src/q3/q3_full.py'),
}

base_dir = r'd:\GIT\public\数模'

for section_id, (desc, rel_path) in code_files.items():
    filepath = os.path.join(base_dir, rel_path)
    if not os.path.exists(filepath):
        print(f'  WARNING: {filepath} not found')
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()

    # Add section heading
    heading = f'附录{section_id}  {desc}'
    p_heading = add_paragraph(heading, font='黑体', sz=21, bold=True, jc='center', spacing_line=240)
    body.insertBefore(p_heading, insert_after.nextSibling if insert_after.nextSibling else None)

    # Add code
    code_paragraphs = code.split('\n')
    for line in code_paragraphs:
        if line.strip():
            p_code = add_code_block(line.rstrip())
            body.insertBefore(p_code, insert_after.nextSibling if insert_after.nextSibling else None)
        else:
            # Empty line
            p_empty = add_paragraph('', font='Courier New', sz=16, spacing_line=240)
            body.insertBefore(p_empty, insert_after.nextSibling if insert_after.nextSibling else None)

    print(f'  Added {section_id}: {desc} ({len(code_paragraphs)} lines)')

print('\nSaving...')
doc.save(validate=False)
print('Done! Pack with pack.py')
