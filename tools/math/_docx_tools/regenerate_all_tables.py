"""
Regenerate ALL LaTeX tables with correct math symbol extraction
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
# 1. Extract ALL tables with math-aware text extraction
# ============================================================
print("[1/4] Extracting all tables with math symbol support...")
tree = ET.parse(DOC_XML)
root = tree.getroot()

tables = []
for elem in root.iter():
    tag = elem.tag.split('}')[-1]
    if tag != 'tbl':
        continue
    caption = ""
    for child in elem:
        if child.tag.split('}')[-1] == 'tblPr':
            for c in child:
                if c.tag.split('}')[-1] == 'tblCaption':
                    ns = c.tag.split('}')[0].strip('{') if '}' in c.tag else ''
                    caption = html_mod.unescape(c.get(f'{{{ns}}}val', ''))
    rows = []
    for tr_elem in elem:
        if tr_elem.tag.split('}')[-1] != 'tr':
            continue
        cells = []
        for tc_elem in tr_elem:
            if tc_elem.tag.split('}')[-1] != 'tc':
                continue
            texts = []
            for desc in tc_elem.iter():
                if desc.text and desc.tag.split('}')[-1] == 't':
                    texts.append(html_mod.unescape(desc.text.strip()))
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

print(f"  {len(tables)} tables extracted")

# ============================================================
# 2. Generate LaTeX + Compile for all tables
# ============================================================
print("[2/4] Generating and compiling LaTeX tables...")

def esc(t):
    t = t.replace('\\', '\\textbackslash ')
    t = t.replace('_', '\\_').replace('%', '\\%').replace('&', '\\&')
    t = t.replace('#', '\\#').replace('{', '\\{').replace('}', '\\}')
    t = t.replace('$', '\\$').replace('~', '\\textasciitilde ')
    t = t.replace('^', '\\textasciicircum ').replace('<', '$<$').replace('>', '$>$')
    return t

for i, t in enumerate(tables):
    rows = t['rows']
    if not rows:
        continue
    ncols = max(len(r) for r in rows)
    header = rows[0]
    data = rows[1:]

    lat = []
    lat.append(r"\documentclass[10pt]{article}")
    lat.append(r"\usepackage[UTF8]{ctex}")
    lat.append(r"\usepackage{booktabs,array,geometry,multirow}")
    lat.append(r"\geometry{margin=0.2in}")
    lat.append(r"\pagestyle{empty}")
    lat.append(r"\setlength{\tabcolsep}{4pt}")
    lat.append(r"\renewcommand{\arraystretch}{1.15}")
    lat.append(r"\begin{document}")

    # Check if table has wide content - use small font for wide tables
    max_cells = max(len(r) for r in rows) if rows else 0
    if max_cells >= 6:
        lat.append(r"\small")

    cols = 'c' * ncols
    lat.append(f'\\begin{{tabular}}{{{cols}}}')
    lat.append(r"\toprule")

    hdr = []
    for cell in header:
        s = cell.get('span', 1)
        txt = esc(cell['text'])
        hdr.append(f"\\textbf{{{txt}}}")
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

    tex_path = os.path.join(TEX_DIR, f"tbl_all_{i+1}.tex")
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lat))

    r = subprocess.run([PDLATEX, "-interaction=nonstopmode", f"tbl_all_{i+1}.tex"],
                       cwd=TEX_DIR, capture_output=True, timeout=120)

    pdf_path = os.path.join(TEX_DIR, f"tbl_all_{i+1}.pdf")
    if os.path.exists(pdf_path):
        subprocess.run([PDFTOPPM, "-png", "-r", "300", f"tbl_all_{i+1}.pdf", f"tbl_all_{i+1}"],
                       cwd=TEX_DIR, capture_output=True, timeout=30)
        src = os.path.join(TEX_DIR, f"tbl_all_{i+1}-1.png")
        dst = os.path.join(MEDIA_DIR, f"tbl_latex_{i+1}.png")
        if os.path.exists(src):
            shutil.move(src, dst)
            # Crop
            img = Image.open(dst).convert('RGB')
            w, h = img.size
            px = img.load()
            def has_content(x, y):
                return px[x,y][0] < 240 or px[x,y][1] < 240 or px[x,y][2] < 240
            top = next((y for y in range(h) if any(has_content(x,y) for x in range(0,w,3))), 0)
            bottom = next((y for y in range(h-1,-1,-1) if any(has_content(x,y) for x in range(0,w,3))), h-1)
            left = next((x for x in range(w) if any(has_content(x,y) for y in range(0,h,3))), 0)
            right = next((x for x in range(w-1,-1,-1) if any(has_content(x,y) for y in range(0,h,3))), w-1)
            pad = 8
            cropped = img.crop((max(0,left-pad), max(0,top-pad), min(w,right+pad+1), min(h,bottom+pad+1)))
            cw, ch = cropped.size
            if cw > 1200:
                ratio = 1200 / cw
                cropped = cropped.resize((1200, int(ch*ratio)), Image.LANCZOS)
            cropped.save(dst)
            print(f"  T{i+1}: OK ({cropped.size[0]}x{cropped.size[1]})")
        else:
            print(f"  T{i+1}: pdftoppm failed")
    else:
        log_path = os.path.join(TEX_DIR, f"tbl_all_{i+1}.log")
        print(f"  T{i+1}: FAILED")
        if os.path.exists(log_path):
            with open(log_path, encoding='utf-8', errors='replace') as f:
                for line in f.readlines()[-3:]:
                    print(f"    {line.strip()}")

# ============================================================
# 3. Replace tables in document + update EMU
# ============================================================
print("\n[3/4] Replacing tables and updating EMU...")
with open(DOC_XML, 'r', encoding='utf-8') as f:
    content = f.read()

with open(os.path.join(UNPACKED, "word", "_rels", "document.xml.rels"), 'r', encoding='ascii') as f:
    rels = f.read()

rids = [int(m.group(1)) for m in __import__('re').finditer(r'rId(\d+)', rels)]
next_rid = max(rids) + 1

import re
opens = [(m.start(), m.end()) for m in re.finditer(r'<ns0:tbl[ >]', content)]
closes = [(m.start(), m.end()) for m in re.finditer(r'</ns0:tbl>', content)]

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

img_id = 500
replaced = 0
for i in range(len(tbls) - 1, -1, -1):
    t = tbls[i]
    fname = f'tbl_latex_{i+1}.png'
    fpath = os.path.join(MEDIA_DIR, fname)
    if not os.path.exists(fpath):
        continue

    pil = Image.open(fpath)
    px_w, px_h = pil.size
    emu_w = int(px_w * 914400 / 200)
    emu_h = int(px_h * 914400 / 200)

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
with open(os.path.join(UNPACKED, "word", "_rels", "document.xml.rels"), 'w', encoding='ascii') as f:
    f.write(rels)

# ============================================================
# 4. Pack final DOCX
# ============================================================
print("[4/4] Packing final DOCX...")
OUTPUT = r"d:\论文_最终版.docx"
if os.path.exists(OUTPUT):
    try: os.remove(OUTPUT)
    except: pass

import zipfile
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in os.walk(UNPACKED):
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            arcname = os.path.relpath(fp, UNPACKED)
            zf.write(fp, arcname)

print(f"\nDone: {OUTPUT} ({os.path.getsize(OUTPUT)//1024}KB)")
