"""
Convert all Word tables to LaTeX-style rendered images
Uses matplotlib with booktabs styling to mimic LaTeX output
"""
import re, os, html as html_mod
from PIL import Image
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'stix'

UNPACKED = r"d:\GIT\public\数模\_unpacked_论文1.5"
DOC_XML = os.path.join(UNPACKED, "word", "document.xml")
RELS_PATH = os.path.join(UNPACKED, "word", "_rels", "document.xml.rels")
MEDIA_DIR = os.path.join(UNPACKED, "word", "media")

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def cell_text(tc):
    texts = []
    for t in tc.findall(f'.//{W}t'):
        if t.text:
            texts.append(html_mod.unescape(t.text).strip())
    return ' '.join(texts)

def get_span(tc):
    tcPr = tc.find(f'{W}tcPr')
    if tcPr is not None:
        gs = tcPr.find(f'{W}gridSpan')
        if gs is not None:
            return int(gs.get(f'{W}val', '1'))
    return 1

# ============================================================
# 1. Extract all table data
# ============================================================
print("[1/4] Extracting table data...")
tree = ET.parse(DOC_XML)
root = tree.getroot()
tbls_elem = root.findall('.//w:tbl', NS)
print(f"  Found {len(tbls_elem)} tables")

all_tables = []
for tbl in tbls_elem:
    tblPr = tbl.find(f'{W}tblPr')
    caption = ''
    if tblPr is not None:
        cap = tblPr.find(f'{W}tblCaption')
        if cap is not None:
            caption = html_mod.unescape(cap.get(f'{W}val', ''))

    rows_data = []
    cols_count = 0
    for tr in tbl.findall(f'.//{W}tr', NS):
        cells = []
        for tc in tr.findall(f'{W}tc'):
            cells.append({'text': cell_text(tc), 'span': get_span(tc)})
        if cells:
            total_span = sum(c['span'] for c in cells)
            cols_count = max(cols_count, total_span)
            rows_data.append(cells)

    # Normalize column count
    for row in rows_data:
        while len(row) < cols_count:
            row.append({'text': '', 'span': 1})

    all_tables.append({'caption': caption, 'rows': rows_data, 'nrows': len(rows_data), 'ncols': cols_count})

for i, t in enumerate(all_tables):
    print(f"  T{i+1}: {t['nrows']}r x {t['ncols']}c | {t['caption'][:40]}")

# ============================================================
# 2. Render LaTeX-style table images
# ============================================================
print("\n[2/4] Rendering LaTeX-style table images...")

def render_booktabs_table(caption, rows, idx):
    """Render a table in LaTeX booktabs style using matplotlib."""
    if not rows:
        return None

    nrows = len(rows)
    ncols = max(len(r) for r in rows)

    # Calculate column widths based on max text length
    col_widths = []
    for c in range(ncols):
        max_len = max(len(r[c]['text']) for r in rows)
        col_widths.append(max(max_len + 3, 10))

    total_chars = sum(col_widths)
    # Figure sizing - reasonable for document
    fig_w = min(max(total_chars * 0.09, 4), 7.0)
    row_h = 0.32
    caption_h = 0.35
    bot_margin = 0.15
    top_margin = 0.1
    fig_h = caption_h + nrows * row_h + bot_margin + top_margin

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, total_chars)
    ax.set_ylim(-nrows - 0.2, 0.8)
    ax.axis('off')

    # Column positions
    col_pos = [0]
    for w in col_widths:
        col_pos.append(col_pos[-1] + w)
    table_width = col_pos[-1]

    # Caption (LaTeX style: \caption{...})
    cap_text = f'\\textbf{{表{idx}  {caption}}}' if caption else f'\\textbf{{表{idx}}}'
    ax.text(table_width/2, 0.6, cap_text,
            ha='center', va='center', fontsize=9, fontweight='bold',
            fontfamily='SimHei', transform=ax.transData)

    # Draw cells
    y0 = -0.05  # Starting y position for first row

    for ri, row in enumerate(rows):
        y = y0 - ri * row_h
        ci = 0
        for cell in row:
            if ci >= ncols:
                break
            text = cell['text']
            span = cell.get('span', 1)
            span = min(span, ncols - ci)

            x0 = col_pos[ci]
            x1 = col_pos[min(ci + span, ncols)]
            cx = (x0 + x1) / 2
            cy = y + row_h/2

            if ri == 0:
                # Header: 黑体 centered
                ax.text(cx, cy, text, ha='center', va='center', fontsize=7.5,
                       fontweight='bold', fontfamily='SimHei')
            else:
                # Data: 宋体
                ax.text(cx, cy, text, ha='center', va='center', fontsize=7,
                       fontfamily='SimSun')

            ci += span

    # Booktabs-style rules using plot (axhline doesn't support transform)
    ax.plot([0, total_chars], [y0, y0], color='black', linewidth=1.2)
    ax.plot([0, total_chars], [y0 - row_h, y0 - row_h], color='black', linewidth=0.6)
    ax.plot([0, total_chars], [y0 - nrows * row_h, y0 - nrows * row_h],
            color='black', linewidth=1.2)
    # Thin vertical rules for column separation
    for x in col_pos[1:-1]:
        ax.plot([x, x], [y0, y0 - nrows * row_h],
                color='gray', linewidth=0.2, linestyle='--', alpha=0.3)

    # Save
    fname = f'table_latex_{idx}.png'
    path = os.path.join(MEDIA_DIR, fname)
    plt.savefig(path, dpi=250, bbox_inches='tight', facecolor='white',
                pad_inches=0.05)
    plt.close(fig)

    img = Image.open(path)
    w, h = img.size

    # Add thin border
    from PIL import ImageOps
    bordered = ImageOps.expand(img, border=1, fill=(200,200,200))
    bordered.save(path)

    return fname, w, h

# Also generate a "booktabs light" alternative
def render_elegant_table(caption, rows, idx):
    """Clean elegant table style with minimal borders."""
    if not rows:
        return None

    nrows = len(rows)
    ncols = max(len(r) for r in rows)

    col_widths = []
    for c in range(ncols):
        max_len = max(len(r[c]['text']) for r in rows)
        col_widths.append(max(max_len + 3, 10))

    total_chars = sum(col_widths)
    fig_w = min(max(total_chars * 0.09, 4), 7.0)
    row_h = 0.32
    fig_h = 0.35 + nrows * row_h + 0.15

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, total_chars)
    ax.set_ylim(-nrows - 0.2, 0.8)
    ax.axis('off')

    col_pos = [0]
    for w in col_widths:
        col_pos.append(col_pos[-1] + w)
    table_width = col_pos[-1]

    # Caption
    cap_text = f'\\textbf{{表{idx}  {caption}}}'
    ax.text(table_width/2, 0.6, cap_text,
            ha='center', va='center', fontsize=9, fontweight='bold',
            fontfamily='SimHei')

    y0 = -0.05
    for ri, row in enumerate(rows):
        y = y0 - ri * row_h
        ci = 0
        for cell in row:
            if ci >= ncols:
                break
            text = cell['text']
            span = cell.get('span', 1)
            span = min(span, ncols - ci)

            x0 = col_pos[ci]
            x1 = col_pos[min(ci + span, ncols)]
            cx = (x0 + x1) / 2
            cy = y + row_h/2

            if ri == 0:
                # Header with light background
                rect = plt.Rectangle((x0, y), x1 - x0, row_h,
                                     facecolor='#F0F4F8', edgecolor='none', alpha=0.7)
                ax.add_patch(rect)
                ax.text(cx, cy, text, ha='center', va='center', fontsize=7.5,
                       fontweight='bold', fontfamily='SimHei', color='#1a1a2e')
            else:
                ax.text(cx, cy, text, ha='center', va='center', fontsize=7,
                       fontfamily='SimSun')

            ci += span

    # Header bottom line (double line style like LaTeX booktabs)
    ax.plot([0, total_chars], [y0, y0], color='black', linewidth=1.5)
    ax.plot([0, total_chars], [y0 - row_h, y0 - row_h], color='black', linewidth=0.8)
    ax.plot([0, total_chars], [y0 - nrows * row_h, y0 - nrows * row_h],
            color='black', linewidth=1.5)

    # Light vertical guides (very subtle)
    for x in col_pos[1:-1]:
        ax.plot([x, x], [y0, y0 - nrows * row_h],
                color='gray', linewidth=0.15, alpha=0.2)

    fname = f'table_elegant_{idx}.png'
    path = os.path.join(MEDIA_DIR, fname)
    plt.savefig(path, dpi=250, bbox_inches='tight', facecolor='white',
                pad_inches=0.08)
    plt.close(fig)

    img = Image.open(path)
    w, h = img.size
    return fname, w, h

# Render all tables - try elegant style (looks more like polished LaTeX)
table_count = 0
for i, t in enumerate(all_tables):
    result = render_elegant_table(t['caption'], t['rows'], i + 1)
    if result:
        table_count += 1
        fname, w, h = result
        print(f"  T{i+1}: {fname} ({w}x{h})")

print(f"\n  Generated {table_count} LaTeX-style table images")

# ============================================================
# 3. Replace native tables with images
# ============================================================
print("[3/4] Replacing tables with images...")

with open(DOC_XML, 'r', encoding='ascii') as f:
    content = f.read()

with open(RELS_PATH, 'r', encoding='ascii') as f:
    rels = f.read()

# Find next RID
rids = [int(m.group(1)) for m in re.finditer(r'rId(\d+)', rels)]
next_rid = max(rids) + 1

# Find all tbl elements using simple regex approach
# w:tbl opens, </w:tbl> closes - use stack
open_pos = [m.start() for m in re.finditer(r'<w:tbl[ >]', content)]
close_pos = [m.start() for m in re.finditer(r'</w:tbl>', content)]
tbls = []
open_idx = 0
close_idx = 0
while open_idx < len(open_pos) and close_idx < len(close_pos):
    start = open_pos[open_idx]
    # Find matching close - need to handle nested tbl tags
    nested = 0
    oi = open_idx + 1
    ci = close_idx
    while ci < len(close_pos):
        # Are there more opens before this close?
        while oi < len(open_pos) and open_pos[oi] < close_pos[ci]:
            nested += 1
            oi += 1
        if nested == 0:
            break
        nested -= 1
        ci += 1
    # ci now points to matching close
    end = close_pos[ci] + 10
    tbls.append({'start': start, 'end': end})
    open_idx = oi
    close_idx = ci + 1

print(f"  Found {len(tbls)} tables to replace")

# Process in reverse
replaced = 0
img_id = 200
for i in range(len(tbls) - 1, -1, -1):
    t = tbls[i]
    # Use elegant style image
    fname = f'table_elegant_{i+1}.png'
    path = os.path.join(MEDIA_DIR, fname)

    if not os.path.exists(path):
        print(f"  WARNING: {fname} not found")
        continue

    tbl_xml = content[t['start']:t['end']]
    cap_m = re.search(r'w:tblCaption w:val="([^"]*)"', tbl_xml)
    caption = html_mod.unescape(cap_m.group(1)) if cap_m else ''

    pil = Image.open(path)
    px_w, px_h = pil.size
    emu_w = int(px_w * 914400 / 250)
    emu_h = int(px_h * 914400 / 250)

    rid = f'rId{next_rid}'
    next_rid += 1

    # Image paragraph (centered, no caption since it's in the image)
    img_xml = f'''<w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:line="240" w:lineRule="auto" w:before="60" w:after="120"/></w:pPr>
      <w:r><w:rPr><w:noProof/></w:rPr>
        <w:drawing>
          <wp:inline distT="0" distB="0" distL="0" distR="0">
            <wp:extent cx="{emu_w}" cy="{emu_h}"/>
            <wp:effectExtent l="0" t="0" r="0" b="0"/>
            <wp:docPr id="{img_id}" name="{fname}"/>
            <wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
            <a:graphic>
              <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <pic:pic>
                  <pic:nvPicPr><pic:cNvPr id="0" name="{fname}"/><pic:cNvPicPr/></pic:nvPicPr>
                  <pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
                  <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm><a:prstGeom prst="rect"/></pic:spPr>
                </pic:pic>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>'''

    content = content[:t['start']] + img_xml + content[t['end']:]

    rel_entry = f'  <Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{fname}"/>'
    rels = rels.replace('</Relationships>', f'{rel_entry}\n</Relationships>')

    img_id += 1
    replaced += 1
    print(f"  T{i+1}: {fname} ({emu_w/914400:.1f}x{emu_h/914400:.1f}in)")

# Save
with open(DOC_XML, 'w', encoding='ascii') as f:
    f.write(content)
with open(RELS_PATH, 'w', encoding='ascii') as f:
    f.write(rels)

print(f"\nReplaced {replaced}/{len(tbls)} tables. Pack with pack.py")
