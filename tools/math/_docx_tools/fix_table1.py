"""
Fix Table 1: correctly extract math symbols and regenerate LaTeX image
"""
import os, subprocess, shutil, html as html_mod
from PIL import Image
import xml.etree.ElementTree as ET

MIKTEX_BIN = r"C:\Users\全佳鹏\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
os.environ['PATH'] += os.pathsep + MIKTEX_BIN
PDLATEX = os.path.join(MIKTEX_BIN, "pdflatex.exe")
PDFTOPPM = os.path.join(MIKTEX_BIN, "pdftoppm.exe")

UNPACKED = r"d:\GIT\public\数模\_unpacked_latex_fix"
DOC_XML = os.path.join(UNPACKED, "word", "document.xml")
MEDIA_DIR = os.path.join(UNPACKED, "word", "media")
TEX_DIR = r"d:\GIT\public\数模\_docx_tools\tex_tables"

# ============================================================
# 1. Extract table with all text (including math symbols)
# ============================================================
tree = ET.parse(DOC_XML)
root = tree.getroot()

tables = []
for elem in root.iter():
    tag = elem.tag.split('}')[-1]
    if tag != 'tbl':
        continue

    # Get caption
    caption = ""
    for child in elem:
        if child.tag.split('}')[-1] == 'tblPr':
            for c in child:
                if c.tag.split('}')[-1] == 'tblCaption':
                    ns = c.tag.split('}')[0].strip('{') if '}' in c.tag else ''
                    caption = html_mod.unescape(c.get(f'{{{ns}}}val', ''))

    # Get rows
    rows = []
    for tr_elem in elem:
        if tr_elem.tag.split('}')[-1] != 'tr':
            continue
        cells = []
        for tc_elem in tr_elem:
            if tc_elem.tag.split('}')[-1] != 'tc':
                continue
            # Extract ALL text (w:t, m:t, any namespace)
            texts = []
            for desc in tc_elem.iter():
                if desc.text and desc.tag.split('}')[-1] == 't':
                    texts.append(html_mod.unescape(desc.text.strip()))
            # Get gridspan
            span = 1
            for tc_child in tc_elem:
                if tc_child.tag.split('}')[-1] == 'tcPr':
                    for prop in tc_child:
                        if prop.tag.split('}')[-1] == 'gridSpan':
                            ns = prop.tag.split('}')[0].strip('{') if '}' in prop.tag else ''
                            span = int(prop.get(f'{{{ns}}}val', '1'))
            cells.append({'text': ' '.join(texts), 'span': span})
        if cells:
            rows.append(cells)
    tables.append({'caption': caption, 'rows': rows})

print(f"Extracted {len(tables)} tables")
t = tables[0]
rows = t['rows']
print(f"Table 1: {len(rows)} rows")

# Show first 3 rows
for ri in range(min(3, len(rows))):
    cells = [c['text'] for c in rows[ri]]
    print(f"  Row {ri}: {' | '.join(cells)}")

# ============================================================
# 2. Generate LaTeX for Table 1
# ============================================================
ncols = max(len(r) for r in rows)
header = rows[0]
data = rows[1:]

def esc(t):
    r = t.replace('\\', '\\textbackslash ')
    r = r.replace('_', '\\_').replace('%', '\\%').replace('&', '\\&')
    r = r.replace('#', '\\#').replace('{', '\\{').replace('}', '\\}')
    r = r.replace('$', '\\$').replace('~', '\\textasciitilde ')
    r = r.replace('^', '\\textasciicircum ').replace('<', '$<$').replace('>', '$>$')
    return r

lat = []
lat.append(r"\documentclass[10pt]{article}")
lat.append(r"\usepackage[UTF8]{ctex}")
lat.append(r"\usepackage{booktabs,array,geometry,multirow}")
lat.append(r"\geometry{margin=0.2in}")
lat.append(r"\pagestyle{empty}")
lat.append(r"\setlength{\tabcolsep}{4pt}")
lat.append(r"\renewcommand{\arraystretch}{1.15}")
lat.append(r"\begin{document}")
lat.append(f"% Table 1: {t['caption']}")
lat.append('\\begin{tabular}{' + 'c' * ncols + '}')
lat.append(r"\toprule")

hdr = []
for cell in header:
    s = cell.get('span', 1)
    txt = esc(cell['text'])
    hdr.append(f"\\textbf{{{txt}}}" if s == 1 else f"\\multicolumn{{{s}}}{{c}}{{\\textbf{{{txt}}}}}")
lat.append(' & '.join(hdr) + r" \\")
lat.append(r"\midrule")

for row in data:
    cells = []
    ci = 0
    for cell in row:
        if ci >= ncols:
            break
        s = min(cell.get('span', 1), ncols - ci)
        txt = esc(cell['text'])
        cells.append(f"\\multicolumn{{{s}}}{{c}}{{{txt}}}" if s > 1 else txt)
        ci += s
    while ci < ncols:
        cells.append('')
        ci += 1
    lat.append(' & '.join(cells) + r" \\")

lat.append(r"\bottomrule")
lat.append(r"\end{tabular}")
lat.append(r"\end{document}")

tex_content = '\n'.join(lat)
tex_path = os.path.join(TEX_DIR, "tbl1_fixed.tex")
with open(tex_path, 'w', encoding='utf-8') as f:
    f.write(tex_content)

print("\nLaTeX source generated:")
for line in lat[:15]:
    print(f"  {line}")
print("  ...")

# ============================================================
# 3. Compile to PDF -> PNG
# ============================================================
print("\nCompiling...")
r = subprocess.run([PDLATEX, "-interaction=nonstopmode", "tbl1_fixed.tex"],
                   cwd=TEX_DIR, capture_output=True, timeout=120)

pdf_path = os.path.join(TEX_DIR, "tbl1_fixed.pdf")
if os.path.exists(pdf_path):
    subprocess.run([PDFTOPPM, "-png", "-r", "300", "tbl1_fixed.pdf", "tbl1_fixed"],
                   cwd=TEX_DIR, capture_output=True, timeout=30)
    src_png = os.path.join(TEX_DIR, "tbl1_fixed-1.png")
    dst_png = os.path.join(MEDIA_DIR, "tbl_latex_1.png")

    if os.path.exists(src_png):
        shutil.move(src_png, dst_png)
        # Crop white margins
        img = Image.open(dst_png).convert('RGB')
        w, h = img.size
        px = img.load()
        def has_content(x, y):
            return px[x,y][0] < 240 or px[x,y][1] < 240 or px[x,y][2] < 240

        top = next((y for y in range(h) if any(has_content(x,y) for x in range(0,w,3))), 0)
        bottom = next((y for y in range(h-1,-1,-1) if any(has_content(x,y) for x in range(0,w,3))), h-1)
        left = next((x for x in range(w) if any(has_content(x,y) for y in range(0,h,3))), 0)
        right = next((x for x in range(w-1,-1,-1) if any(has_content(x,y) for y in range(0,h,3))), w-1)

        cropped = img.crop((max(0,left-8), max(0,top-8), min(w,right+9), min(h,bottom+9)))
        # Resize if too wide
        cw, ch = cropped.size
        if cw > 1200:
            ratio = 1200 / cw
            cropped = cropped.resize((1200, int(ch*ratio)), Image.LANCZOS)
        cropped.save(dst_png)
        print(f"OK: {dst_png} ({cropped.size[0]}x{cropped.size[1]})")

        # Update EMU in document
        px_w, px_h = cropped.size
        emu_w = int(px_w * 914400 / 200)
        emu_h = int(px_h * 914400 / 200)

        with open(DOC_XML, 'r', encoding='utf-8') as f:
            content = f.read()

        idx = content.find("tbl_latex_1.png")
        if idx > 0:
            ex_start = content.rfind('<ns4:extent ', 0, idx)
            if ex_start > 0:
                ex_end = content.find('/>', ex_start) + 2
                content = content.replace(content[ex_start:ex_end],
                    f'<ns4:extent cx="{emu_w}" cy="{emu_h}"/>', 1)
            sp_start = content.rfind('<ns5:ext cx="', 0, idx)
            if sp_start > 0:
                sp_end = content.find('/>', sp_start) + 2
                content = content.replace(content[sp_start:sp_end],
                    f'<ns5:ext cx="{emu_w}" cy="{emu_h}"/>', 1)

        with open(DOC_XML, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"EMU updated: {emu_w}x{emu_h}")
    else:
        print(f"pdftoppm output not found at {src_png}")
else:
    print("PDF not generated! Checking log...")
    log_path = os.path.join(TEX_DIR, "tbl1_fixed.log")
    if os.path.exists(log_path):
        with open(log_path, encoding='utf-8', errors='replace') as f:
            for line in f.readlines()[-10:]:
                print(f"  {line.strip()}")
