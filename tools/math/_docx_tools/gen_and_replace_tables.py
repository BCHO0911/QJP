"""
Read Word tables using ElementTree, generate images, then replace
"""
import re, os, html as html_mod
import xml.etree.ElementTree as ET
from PIL import Image, ImageOps
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

UNPACKED = r"d:\GIT\public\数模\_unpacked_论文1.5"
DOC_XML = os.path.join(UNPACKED, "word", "document.xml")
RELS_PATH = os.path.join(UNPACKED, "word", "_rels", "document.xml.rels")
MEDIA_DIR = os.path.join(UNPACKED, "word", "media")

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def get_cell_text(tc):
    """Extract all text from a table cell."""
    texts = []
    for t in tc.findall(f'.//{W}t'):
        if t.text:
            texts.append(html_mod.unescape(t.text.strip()))
    return ' '.join(texts).strip()

def get_span(tc):
    """Get gridspan for a cell."""
    tcPr = tc.find(f'{W}tcPr')
    if tcPr is not None:
        gs = tcPr.find(f'{W}gridSpan')
        if gs is not None:
            val = gs.get(f'{W}val', '1')
            return int(val)
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
            caption = cap.get(f'{W}val', '')
            caption = html_mod.unescape(caption)

    rows_data = []
    for tr in tbl.findall(f'.//{W}tr', NS):
        cells = []
        for tc in tr.findall(f'{W}tc'):
            text = get_cell_text(tc)
            span = get_span(tc)
            cells.append({'text': text, 'span': span})
        if cells:
            rows_data.append(cells)

    all_tables.append({'caption': caption, 'rows': rows_data,
                       'nrows': len(rows_data),
                       'ncols': max(len(r) for r in rows_data) if rows_data else 0})

for i, t in enumerate(all_tables):
    print(f"  T{i+1}: {t['nrows']}r x {t['ncols']}c | {t['caption'][:40]}")

# ============================================================
# 2. Generate table images
# ============================================================
print("\n[2/4] Generating table images...")

def render_table(caption, rows, idx):
    """Render a table as a styled PNG image."""
    if not rows:
        return None

    nrows = len(rows)
    ncols = max(len(r) for r in rows)

    # Calculate column widths based on max text length per column
    col_widths = []
    for c in range(ncols):
        max_len = max((len(r[c]['text']) if c < len(r) else 0) for r in rows)
        span = max((r[c]['span'] if c < len(r) else 1) for r in rows)
        # Adjust for spans
        adj_len = max_len // span if span > 0 else max_len
        col_widths.append(max(adj_len + 2, 8))

    # Scale to reasonable image size
    total_chars = sum(col_widths)
    fig_w = max(5, min(total_chars * 0.10, 7.5))
    row_h = 0.3 if nrows > 5 else 0.35
    fig_h = max(1.2, nrows * row_h + 0.6)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, total_chars)
    ax.set_ylim(-nrows - 0.5, 0.5)
    ax.axis('off')

    # Caption
    if caption:
        ax.text(total_chars/2, 0.3, f'表{idx}  {caption}',
                ha='center', va='center', fontsize=9, fontweight='bold',
                fontfamily='SimHei')

    # Column positions
    col_pos = [0]
    for w in col_widths:
        col_pos.append(col_pos[-1] + w)

    # Draw cells
    for ri, row in enumerate(rows):
        y = -ri - 1
        ci = 0
        for cell in row:
            if ci >= ncols:
                break
            text = cell['text']
            span = cell.get('span', 1)
            span = min(span, ncols - ci)

            x0 = col_pos[ci]
            x1 = col_pos[min(ci + span, len(col_pos) - 1)]

            # Background for header
            if ri == 0:
                rect = Rectangle((x0, y), x1 - x0, 1,
                               linewidth=0.5, edgecolor='black',
                               facecolor='#D6EAF8')
                ax.add_patch(rect)
                ax.text((x0 + x1)/2, y + 0.5, text,
                       ha='center', va='center', fontsize=7,
                       fontweight='bold', fontfamily='SimHei')
            else:
                # Alternate row colors
                face = '#F8F9FA' if ri % 2 == 0 else '#FFFFFF'
                rect = Rectangle((x0, y), x1 - x0, 1,
                               linewidth=0.5, edgecolor='black',
                               facecolor=face)
                ax.add_patch(rect)
                ax.text((x0 + x1)/2, y + 0.5, text,
                       ha='center', va='center', fontsize=6.5,
                       fontfamily='SimSun')

            ci += span
        # Fill remaining cells
        while ci < ncols:
            x0 = col_pos[ci]
            x1 = col_pos[ci + 1]
            face = '#F8F9FA' if ri % 2 == 0 else '#FFFFFF'
            rect = Rectangle((x0, y), x1 - x0, 1,
                           linewidth=0.5, edgecolor='black', facecolor=face)
            ax.add_patch(rect)
            ci += 1

    # Grid lines (already drawn via rectangles)

    plt.tight_layout()
    fname = f'image{24 + idx - 1}.png'
    path = os.path.join(MEDIA_DIR, fname)
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    img = Image.open(path)
    w, h = img.size

    # Add 1px black border
    bordered = ImageOps.expand(img, border=1, fill=(0,0,0))
    bordered.save(path)

    return fname, w, h

table_count = 0
for i, t in enumerate(all_tables):
    result = render_table(t['caption'], t['rows'], i + 1)
    if result:
        fname, w, h = result
        table_count += 1
        print(f"  T{i+1}: {fname} ({w}x{h})")

print(f"\n  Generated {table_count} table images")

# ============================================================
# 3. Center tables in document
# ============================================================
print("[3/4] Centering tables...")
with open(DOC_XML, 'r', encoding='ascii') as f:
    content = f.read()

# Add center to tables
tbl_count = len(re.findall(r'<w:tbl[ >]', content))
for m in re.finditer(r'<w:tbl[ >]', content):
    start = m.start()
    end = content.find('</w:tblPr>', start)
    if end > 0:
        block = content[start:end]
        if 'w:jc' not in block:
            content = content[:end] + '<w:jc w:val="center"/>' + content[end:]

print(f"  Centered {tbl_count} tables")

# ============================================================
# 4. Replace tables with images
# ============================================================
print("[4/4] Replacing tables with images...")

# Read rels
with open(RELS_PATH, 'r', encoding='ascii') as f:
    rels = f.read()

rids = [int(m.group(1)) for m in re.finditer(r'rId(\d+)', rels)]
next_rid = max(rids) + 1

# Find all tables
tbls = []
for m in re.finditer(r'<w:tbl[ >]', content):
    start = m.start()
    depth = 1
    pos = m.end()
    while depth > 0 and pos < len(content):
        if content[pos:pos+6] == '<w:tbl':
            depth += 1
        elif content[pos:pos+10] == '</w:tbl>':
            depth -= 1
            if depth == 0:
                end = pos + 10
                break
        pos += 1
    if depth == 0:
        tbls.append({'start': start, 'end': end})

print(f"  Found {len(tbls)} table positions")

img_id = 100
replaced = 0

for i in range(len(tbls) - 1, -1, -1):
    t = tbls[i]
    img_num = 24 + i
    img_fname = f'image{img_num}.png'
    img_path = os.path.join(MEDIA_DIR, img_fname)

    if not os.path.exists(img_path):
        print(f"  WARNING: {img_fname} not found")
        continue

    tbl_xml = content[t['start']:t['end']]
    cap_m = re.search(r'w:tblCaption w:val="([^"]*)"', tbl_xml)
    caption = html_mod.unescape(cap_m.group(1)) if cap_m else ''

    # Image at 200 DPI
    pil_img = Image.open(img_path)
    px_w, px_h = pil_img.size
    emu_w = int(px_w * 914400 / 200)
    emu_h = int(px_h * 914400 / 200)

    rid = f'rId{next_rid}'
    next_rid += 1

    # Image XML
    img_xml = f'''<w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:line="240" w:lineRule="auto" w:before="60" w:after="60"/></w:pPr>
      <w:r><w:rPr><w:noProof/></w:rPr>
        <w:drawing>
          <wp:inline distT="0" distB="0" distL="0" distR="0">
            <wp:extent cx="{emu_w}" cy="{emu_h}"/>
            <wp:effectExtent l="0" t="0" r="0" b="0"/>
            <wp:docPr id="{img_id}" name="{img_fname}"/>
            <wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
            <a:graphic>
              <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <pic:pic>
                  <pic:nvPicPr><pic:cNvPr id="0" name="{img_fname}"/><pic:cNvPicPr/></pic:nvPicPr>
                  <pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
                  <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm><a:prstGeom prst="rect"/></pic:spPr>
                </pic:pic>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>'''

    # Caption
    full_cap = f'表{i+1}  {caption}'
    cap_xml = f'''<w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:line="240" w:lineRule="auto" w:before="60" w:after="120"/></w:pPr>
      <w:r>
        <w:rPr><w:rFonts w:ascii="&#40657;&#20307;" w:hAnsi="&#40657;&#20307;" w:eastAsia="&#40657;&#20307;" w:cs="&#40657;&#20307;"/><w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr>
        <w:t>{full_cap}</w:t>
      </w:r>
    </w:p>'''

    replacement = img_xml + cap_xml
    content = content[:t['start']] + replacement + content[t['end']:]

    rel_entry = f'  <Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{img_fname}"/>'
    rels = rels.replace('</Relationships>', f'{rel_entry}\n</Relationships>')

    img_id += 1
    replaced += 1
    print(f"  T{i+1}: {img_fname} ({emu_w/914400:.1f}x{emu_h/914400:.1f}in)")

# Save
with open(DOC_XML, 'w', encoding='ascii') as f:
    f.write(content)
with open(RELS_PATH, 'w', encoding='ascii') as f:
    f.write(rels)

print(f"\nDone! Replaced {replaced}/{len(tbls)} tables.")
print("Pack to create final docx.")
