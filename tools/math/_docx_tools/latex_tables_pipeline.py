"""
Generate actual LaTeX-rendered table images using pdflatex,
replace native tables, then convert final docx to PDF.
"""
import os, re, html, subprocess, shutil
import xml.etree.ElementTree as ET
from PIL import Image

UNPACKED = r"d:\GIT\public\数模\_unpacked_latex"
DOC_XML = os.path.join(UNPACKED, "word", "document.xml")
RELS_PATH = os.path.join(UNPACKED, "word", "_rels", "document.xml.rels")
MEDIA_DIR = os.path.join(UNPACKED, "word", "media")
TEX_DIR = r"d:\GIT\public\数模\_docx_tools\tex_tables"
os.makedirs(TEX_DIR, exist_ok=True)

MikTeX_BIN = r"C:\Users\全佳鹏\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
os.environ['PATH'] += os.pathsep + MikTeX_BIN

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# ============================================================
# 1. Extract tables
# ============================================================
print("[1/5] Extracting table data...")
tree = ET.parse(DOC_XML)
root = tree.getroot()

tables = []
for tbl in root.findall('.//w:tbl', NS):
    caption = ''
    tblPr = tbl.find(f'{W}tblPr')
    if tblPr is not None:
        cap = tblPr.find(f'{W}tblCaption')
        if cap is not None:
            caption = html.unescape(cap.get(f'{W}val', ''))

    rows = []
    for tr in tbl.findall(f'.//{W}tr', NS):
        cells = []
        for tc in tr.findall(f'{W}tc'):
            texts = [html.unescape(t.text or '').strip() for t in tc.findall(f'.//{W}t')]
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
# 2. Generate LaTeX code and compile
# ============================================================
print("[2/5] Compiling LaTeX tables...")

LATEX_PREAMBLE = r"""
\documentclass[12pt]{article}
\usepackage[UTF8]{ctex}
\usepackage{booktabs, array, geometry, multirow}
\geometry{margin=0.5in}
\pagestyle{empty}
\setlength{\tabcolsep}{6pt}
\renewcommand{\arraystretch}{1.2}
\begin{document}
"""

for i, t in enumerate(tables):
    rows = t['rows']
    if not rows:
        continue
    ncols = max(len(r) for r in rows)

    # Determine header row
    header = rows[0]
    data = rows[1:]

    latex_lines = []
    latex_lines.append(f'% Table {i+1}')
    latex_lines.append(r'\begin{tabular}{' + 'c' * ncols + '}')
    latex_lines.append(r'\toprule')

    # Header
    hdr_cells = []
    for cell in header:
        span = cell.get('span', 1)
        text = cell['text'].replace('_', '\\_').replace('%', '\\%').replace('&', '\\&')
        if span > 1:
            hdr_cells.append(f'\\multicolumn{{{span}}}{{c}}{{\\textbf{{{text}}}}}')
        else:
            hdr_cells.append(f'\\textbf{{{text}}}')
    latex_lines.append(' & '.join(hdr_cells) + r' \\')
    latex_lines.append(r'\midrule')

    # Data rows
    for row in data:
        cells = []
        ci = 0
        for cell in row:
            if ci >= ncols:
                break
            span = cell.get('span', 1)
            text = cell['text'].replace('_', '\\_').replace('%', '\\%').replace('&', '\\&')
            if span > 1:
                cells.append(f'\\multicolumn{{{span}}}{{c}}{{{text}}}')
            else:
                cells.append(text)
            ci += span
        # Fill remaining columns
        while ci < ncols:
            cells.append('')
            ci += 1
        latex_lines.append(' & '.join(cells) + r' \\')

    latex_lines.append(r'\bottomrule')
    latex_lines.append(r'\end{tabular}')

    # Write standalone LaTeX file
    tex_content = LATEX_PREAMBLE + '\n'.join(latex_lines) + '\n\\end{document}'
    tex_path = os.path.join(TEX_DIR, f'table_{i+1}.tex')
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(tex_content)

    # Compile with pdflatex
    result = subprocess.run(
        ['pdflatex', '-interaction=nonstopmode', f'table_{i+1}.tex'],
        cwd=TEX_DIR, capture_output=True, text=True, timeout=60,
        env={**os.environ}
    )

    pdf_path = os.path.join(TEX_DIR, f'table_{i+1}.pdf')
    png_path = os.path.join(MEDIA_DIR, f'table_latex_{i+1}.png')

    if os.path.exists(pdf_path):
        # Convert to PNG with pdftoppm
        subprocess.run(
            ['pdftoppm', '-png', '-r', '300', f'table_{i+1}.pdf',
             f'table_{i+1}'],
            cwd=TEX_DIR, capture_output=True, timeout=30,
            env={**os.environ}
        )
        # pdftoppm outputs table_{i+1}-1.png
        src_png = os.path.join(TEX_DIR, f'table_{i+1}-1.png')
        if os.path.exists(src_png):
            shutil.move(src_png, png_path)
            # Trim white border and add thin border
            try:
                img = Image.open(png_path)
                img = img.convert('RGB')
                # Crop white margins
                bg = Image.new('RGB', img.size, (255,255,255))
                from PIL import ImageOps
                img = ImageOps.expand(img, border=5, fill=(255,255,255))
                img = ImageOps.expand(img, border=1, fill=(180,180,180))
                img.save(png_path)
                print(f"  T{i+1}: LaTeX table saved ({img.size[0]}x{img.size[1]})")
            except Exception as e:
                print(f"  T{i+1}: Image processing error: {e}")
        else:
            print(f"  T{i+1}: pdftoppm output not found ({src_png})")
    else:
        print(f"  T{i+1}: pdflatex failed, log follows:")
        # Show last 10 lines of log
        log_path = os.path.join(TEX_DIR, f'table_{i+1}.log')
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_lines = f.readlines()
                for line in log_lines[-10:]:
                    print(f"    {line.strip()}")
