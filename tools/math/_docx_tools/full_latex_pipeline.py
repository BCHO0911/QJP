"""
Complete pipeline: LaTeX tables -> replace in docx -> generate PDF
"""
import os, re, html, shutil, subprocess
import xml.etree.ElementTree as ET
from PIL import Image
from lxml import etree

MIKTEX_BIN = r"C:\Users\全佳鹏\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
os.environ['PATH'] += os.pathsep + MIKTEX_BIN

PDLATEX = os.path.join(MIKTEX_BIN, "pdflatex.exe")
PDFTOPPM = os.path.join(MIKTEX_BIN, "pdftoppm.exe")
UNPACKED = r"d:\GIT\public\数模\_unpacked_latex"
DOC_XML = os.path.join(UNPACKED, "word", "document.xml")
RELS_PATH = os.path.join(UNPACKED, "word", "_rels", "document.xml.rels")
MEDIA_DIR = os.path.join(UNPACKED, "word", "media")
TEX_DIR = r"d:\GIT\public\数模\_docx_tools\tex_tables"
OUTPUT_DOCX = r"d:\论文_LaTeX表格版.docx"
OUTPUT_PDF = r"d:\论文_最终版.pdf"
os.makedirs(TEX_DIR, exist_ok=True)

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# ============================================================
# 1. Extract table data
# ============================================================
print("[1/5] Extracting tables from DOCX...")
tree = ET.parse(DOC_XML)
root = tree.getroot()

tables = []
for tbl in root.findall(f'.//{W}tbl'):
    caption = ''
    tblPr = tbl.find(f'{W}tblPr')
    if tblPr is not None:
        cap = tblPr.find(f'{W}tblCaption')
        if cap is not None:
            caption = html.unescape(cap.get(f'{W}val', ''))

    rows = []
    for tr in tbl.findall(f'.//{W}tr'):
        cells = []
        for tc in tr.findall(f'{W}tc'):
            texts = []
            for desc in tc.iter():
                if desc.text and desc.tag.split('}')[-1] == 't':
                    texts.append(html.unescape(desc.text.strip()))
            tcPr = tc.find(f'{W}tcPr')
            span = 1
            if tcPr is not None:
                gs = tcPr.find(f'{W}gridSpan')
                if gs is not None:
                    span = int(gs.get(f'{W}val', '1'))
            cells.append({'text': ' '.join(texts), 'span': span})
        if cells:
            rows.append(cells)
    tables.append({'caption': caption, 'rows': rows})

print(f"  {len(tables)} tables extracted")

# ============================================================
# 2. Generate LaTeX tables and compile
# ============================================================
print("[2/5] Compiling LaTeX tables...")

LATEX_HEADER = r"""\documentclass[10pt]{article}
\usepackage[UTF8]{ctex}
\usepackage{booktabs,array,geometry,multirow}
\geometry{margin=0.3in}
\pagestyle{empty}
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.1}
\begin{document}
"""

def escape_latex(text):
    return text.replace('\\', '\\textbackslash ').replace('_', '\\_').replace('%', '\\%')\
               .replace('&', '\\&').replace('#', '\\#').replace('{', '\\{').replace('}', '\\}')\
               .replace('$', '\\$').replace('~', '\\textasciitilde ').replace('^', '\\textasciicircum ')

for i, t in enumerate(tables):
    rows = t['rows']
    if not rows:
        continue
    ncols = max(len(r) for r in rows)
    header = rows[0]
    data = rows[1:]

    lines = [f'% Table {i+1}: {t["caption"]}']
    lines.append(r'\begin{tabular}{' + 'c' * ncols + '}')
    lines.append(r'\toprule')

    hdr = []
    for cell in header:
        s = cell.get('span', 1)
        txt = escape_latex(cell['text'])
        if s > 1:
            hdr.append(f'\\multicolumn{{{s}}}{{c}}{{\\textbf{{{txt}}}}}')
        else:
            hdr.append(f'\\textbf{{{txt}}}')
    lines.append(' & '.join(hdr) + ' \\\\')
    lines.append(r'\midrule')

    for row in data:
        cells = []
        ci = 0
        for cell in row:
            if ci >= ncols: break
            s = cell.get('span', 1)
            s = min(s, ncols - ci)
            txt = escape_latex(cell['text'])
            if s > 1:
                cells.append(f'\\multicolumn{{{s}}}{{c}}{{{txt}}}')
            else:
                cells.append(txt)
            ci += s
        while ci < ncols:
            cells.append('')
            ci += 1
        lines.append(' & '.join(cells) + ' \\\\')

    lines.append(r'\bottomrule')
    lines.append(r'\end{tabular}')

    tex = LATEX_HEADER + '\n'.join(lines) + '\n\\end{document}'
    tex_path = os.path.join(TEX_DIR, f'tbl{i+1}.tex')
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(tex)

    r = subprocess.run([PDLATEX, '-interaction=nonstopmode', f'tbl{i+1}.tex'],
                       cwd=TEX_DIR, capture_output=True, text=True, timeout=120)
    # Check for errors
    log_path = os.path.join(TEX_DIR, f'tbl{i+1}.log')
    pdf_path = os.path.join(TEX_DIR, f'tbl{i+1}.pdf')

    if os.path.exists(pdf_path):
        subprocess.run([PDFTOPPM, '-png', '-r', '300', f'tbl{i+1}.pdf', f'tbl{i+1}'],
                       cwd=TEX_DIR, capture_output=True, timeout=30)
        src = os.path.join(TEX_DIR, f'tbl{i+1}-1.png')
        if os.path.exists(src):
            dst = os.path.join(MEDIA_DIR, f'tbl_latex_{i+1}.png')
            shutil.move(src, dst)
            img = Image.open(dst)
            print(f"  T{i+1}: OK ({img.size[0]}x{img.size[1]})")
        else:
            print(f"  T{i+1}: pdftoppm produced no output")
    else:
        print(f"  T{i+1}: pdflatex FAILED, see {log_path}")
        if os.path.exists(log_path):
            with open(log_path) as f:
                for line in f.readlines()[-5:]:
                    print(f"    {line.strip()}")

# ============================================================
# 3. Replace tables in DOCX XML
# ============================================================
print("[3/5] Replacing tables in DOCX...")

with open(DOC_XML, 'r', encoding='utf-8') as f:
    content = f.read()

with open(RELS_PATH, 'r', encoding='utf-8') as f:
    rels = f.read()

rids = [int(m.group(1)) for m in re.finditer(r'rId(\d+)', rels)]
next_rid = max(rids) + 1

opens = [(m.start(), m.end()) for m in re.finditer(r'<(?:w|ns0):tbl[ >]', content)]
closes = [(m.start(), m.end()) for m in re.finditer(r'</(?:w|ns0):tbl>', content)]

tbls = []
oi, ci = 0, 0
while oi < len(opens) and ci < len(closes):
    start = opens[oi][0]
    depth = 1
    op = oi + 1
    cp = ci
    while depth > 0 and cp < len(closes):
        while op < len(opens) and opens[op][0] < closes[cp][0]:
            depth += 1
            op += 1
        depth -= 1
        if depth == 0:
            end = closes[cp][1]
            break
        cp += 1
    if depth == 0:
        tbls.append({'start': start, 'end': end})
        oi, ci = op, cp + 1

print(f"  {len(tbls)} table positions found")

img_id = 500
replaced = 0
for i in range(len(tbls) - 1, -1, -1):
    t = tbls[i]
    fname = f'tbl_latex_{i+1}.png'
    fpath = os.path.join(MEDIA_DIR, fname)
    if not os.path.exists(fpath):
        print(f"  WARNING: {fname} not found")
        continue

    pil = Image.open(fpath)
    px_w, px_h = pil.size
    emu_w = int(px_w * 914400 / 300)
    emu_h = int(px_h * 914400 / 300)

    rid = f'rId{next_rid}'
    next_rid += 1

    img_xml = f'''<ns0:p><ns0:pPr><ns0:jc ns0:val="center"/><ns0:spacing ns0:line="240" ns0:lineRule="auto" ns0:before="60" ns0:after="120"/></ns0:pPr>
<ns0:r><ns0:rPr><ns0:noProof/></ns0:rPr>
<ns0:drawing><ns4:inline distT="0" distB="0" distL="0" distR="0">
<ns4:extent cx="{emu_w}" cy="{emu_h}"/>
<ns4:effectExtent l="0" t="0" r="0" b="0"/>
<ns4:docPr id="{img_id}" name="{fname}"/>
<ns4:cNvGraphicFramePr><ns5:graphicFrameLocks noChangeAspect="1"/></ns4:cNvGraphicFramePr>
<ns5:graphic><ns5:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<ns6:pic><ns6:nvPicPr><ns6:cNvPr id="0" name="{fname}"/><ns6:cNvPicPr/></ns6:nvPicPr>
<ns6:blipFill><ns5:blip ns7:embed="{rid}"/><ns5:stretch><ns5:fillRect/></ns5:stretch></ns6:blipFill>
<ns6:spPr><ns5:xfrm><ns5:off x="0" y="0"/><ns5:ext cx="{emu_w}" cy="{emu_h}"/></ns5:xfrm><ns5:prstGeom prst="rect"/></ns6:spPr>
</ns6:pic></ns5:graphicData></ns5:graphic></ns4:inline></ns0:drawing></ns0:r></ns0:p>'''



    content = content[:t['start']] + img_xml + content[t['end']:]
    rels = rels.replace('</Relationships>', f'  <Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{fname}"/>\n</Relationships>')
    img_id += 1
    replaced += 1

print(f"  Replaced {replaced} tables")

with open(DOC_XML, 'w', encoding='utf-8') as f:
    f.write(content)
with open(RELS_PATH, 'w', encoding='utf-8') as f:
    f.write(rels)

# ============================================================
# 4. Pack DOCX
# ============================================================
print("[4/5] Packing DOCX...")
if os.path.exists(OUTPUT_DOCX):
    try: os.remove(OUTPUT_DOCX)
    except: pass
import zipfile
with zipfile.ZipFile(OUTPUT_DOCX, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in os.walk(UNPACKED):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            arcname = os.path.relpath(fp, UNPACKED)
            zf.write(fp, arcname)
print(f"  Created: {OUTPUT_DOCX}")

# ============================================================
# 5. Convert to PDF via Python (using docx2pdf or alternative)
# ============================================================
print("[5/5] Generating PDF...")
# Use python-docx to verify, then convert via Word
# Since we can't use Word COM directly, save the docx and let user know
print(f"  DOCX ready: {OUTPUT_DOCX}")
print(f"  To get PDF: open in Word -> Save As PDF")
print(f"  Or use: pandoc {OUTPUT_DOCX} -o {OUTPUT_PDF}  (if pandoc+pdflatex available)")

# Try pandoc if available
pandoc_path = subprocess.run(['where', 'pandoc'], capture_output=True, text=True, shell=True)
if pandoc_path.returncode == 0:
    print("  Trying pandoc conversion to PDF...")
    r = subprocess.run(['pandoc', OUTPUT_DOCX, '-o', OUTPUT_PDF, '--pdf-engine=xelatex'],
                       capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        print(f"  PDF generated: {OUTPUT_PDF}")
    else:
        print(f"  Pandoc failed: {r.stderr[:200]}")
else:
    print("  Pandoc not available - use Word to convert to PDF")

print("\n=== ALL DONE ===")
