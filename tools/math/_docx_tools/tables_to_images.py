"""
Extract all Word tables and convert them to styled images
"""
import sys, os, re, html as html_mod

# ============================================================
# 1. Extract all table data from the unpacked document
# ============================================================
DOC_XML = r"d:\GIT\public\数模\_unpacked_论文1.5\word\document.xml"

with open(DOC_XML, 'r', encoding='utf-8') as f:
    content = f.read()

def decode_text(text):
    """Decode HTML entities to Chinese text."""
    if not text:
        return ''
    return html_mod.unescape(text.strip())

def get_tbl_data(tbl_xml):
    """Extract table data from a tbl XML block."""
    # Get caption
    cap_m = re.search(r'<ns0:tblCaption ns0:val="([^"]*)"', tbl_xml)
    caption = decode_text(cap_m.group(1)) if cap_m else ''

    # Extract rows
    rows = []
    for tr_m in re.finditer(r'<ns0:tr[ >].*?</ns0:tr>', tbl_xml, re.DOTALL):
        tr_xml = tr_m.group()
        cells = []
        for tc_m in re.finditer(r'<ns0:tc[ >].*?</ns0:tc>', tr_xml, re.DOTALL):
            tc_xml = tc_m.group()
            # Get text from all runs
            texts = []
            for t_m in re.finditer(r'<ns0:t[^>]*>([^<]*)', tc_xml):
                texts.append(decode_text(t_m.group(1)))
            cell_text = ''.join(texts).strip()
            # Get vertical/horizontal merge info
            vmerge = 'vMerge' if 'ns0:vMerge' in tc_xml else ''
            gridspan = ''
            gs_m = re.search(r'ns0:gridSpan ns0:val="(\d+)"', tc_xml)
            if gs_m:
                gridspan = gs_m.group(1)
            cells.append({
                'text': cell_text,
                'gridspan': gridspan,
                'vmerge': vmerge
            })
        if cells:
            rows.append(cells)

    return caption, rows

# Find all tbl elements
tbl_positions = []
for m in re.finditer(r'<ns0:tbl[ >]', content):
    start = m.start()
    # Find matching closing
    depth = 1
    pos = m.end()
    while depth > 0 and pos < len(content):
        if content[pos:pos+9] == '<ns0:tbl ' or content[pos:pos+10] == '<ns0:tbl>':
            depth += 1
            pos += 1
        elif content[pos:pos+10] == '</ns0:tbl>':
            depth -= 1
            if depth == 0:
                end = pos + 10
                break
            pos += 1
        else:
            pos += 1
    tbl_xml = content[start:end]
    caption, rows = get_tbl_data(tbl_xml)
    tbl_positions.append({
        'start': start,
        'end': end,
        'xml': tbl_xml,
        'caption': caption,
        'rows': rows,
        'nrows': len(rows),
        'ncols': max(len(r) for r in rows) if rows else 0
    })

print(f"Found {len(tbl_positions)} tables\n")

for i, t in enumerate(tbl_positions):
    print(f"Table {i+1}: [{t['nrows']}r x {t['ncols']}c] {t['caption'][:50]}")
    # Print first 2 rows
    for ri, row in enumerate(t['rows'][:3]):
        cells = [c['text'][:20] for c in row]
        print(f"  Row{ri}: {' | '.join(cells)}")
    if t['nrows'] > 3:
        print(f"  ... ({t['nrows']-3} more rows)")
    print()

# ============================================================
# 2. Generate table images
# ============================================================
print("Generating table images...")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = r"d:\GIT\public\数模\_unpacked_论文1.5\word\media"

# Image counter for new images (after existing image23.png)
img_counter = 24

def render_table_to_image(caption, rows, table_idx):
    """Render a table as a styled image."""
    global img_counter

    if not rows:
        return None

    nrows = len(rows)
    ncols = max(len(r) for r in rows)

    # Calculate column widths based on content
    col_widths = []
    for c in range(ncols):
        max_w = 0
        for r in rows:
            if c < len(r):
                text = r[c]['text']
                gridspan = r[c].get('gridspan', '')
                w = max(len(text), 8)
                if gridspan:
                    # Adjust for spanned columns
                    span_count = int(gridspan)
                    w = w // span_count if span_count > 0 else w
                max_w = max(max_w, w)
        col_widths.append(min(max_w + 2, 30))

    # Total width
    total_chars = sum(col_widths)
    fig_width = max(6, total_chars * 0.12)
    fig_height = max(1.5, nrows * 0.35 + 0.6)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_xlim(0, total_chars)
    ax.set_ylim(-nrows - 1, 0.5)
    ax.axis('off')

    # Draw title/caption
    if caption:
        ax.text(total_chars/2, 0.2, f"表{table_idx}: {caption}",
                ha='center', va='center', fontsize=10, fontweight='bold',
                fontfamily='SimHei')

    # Draw cells
    y_offset = -0.5  # Start below caption
    col_positions = [0]
    for w in col_widths:
        col_positions.append(col_positions[-1] + w)

    for ri, row in enumerate(rows):
        y = y_offset - ri - 1

        # Handle merged cells
        ci = 0
        for c_idx, cell in enumerate(row):
            if ci >= ncols:
                break

            text = cell['text'] if cell['text'] else ''
            gs = cell.get('gridspan', '')
            span = int(gs) if gs else 1

            x_start = col_positions[ci]
            x_end = col_positions[min(ci + span, len(col_positions) - 1)]

            # Draw cell border
            rect = Rectangle((x_start, y), x_end - x_start, 1,
                           linewidth=0.5, edgecolor='black', facecolor='none')
            ax.add_patch(rect)

            # Special styling for header row
            if ri == 0:
                # Header: light gray background
                rect_bg = Rectangle((x_start, y), x_end - x_start, 1,
                                  facecolor='#E8E8E8', edgecolor='black', linewidth=0.5)
                ax.add_patch(rect_bg)
                ax.text((x_start + x_end)/2, y + 0.5, text,
                       ha='center', va='center', fontsize=7,
                       fontweight='bold', fontfamily='SimSun')
            else:
                ax.text((x_start + x_end)/2, y + 0.5, text,
                       ha='center', va='center', fontsize=6.5,
                       fontfamily='SimSun')

            ci += span

    # Draw horizontal lines
    for ri in range(nrows + 1):
        y = y_offset - ri
        ax.axhline(y=y, color='black', linewidth=0.5)

    # Draw vertical lines
    for cp in col_positions:
        ax.axvline(x=cp, color='black', linewidth=0.5)

    plt.tight_layout()

    # Save image
    fname = f'image{img_counter}.png'
    img_path = os.path.join(OUT_DIR, fname)
    plt.savefig(img_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    # Get dimensions for document
    from PIL import Image
    pil_img = Image.open(img_path)
    w, h = pil_img.size

    # Add 1px black border
    from PIL import ImageOps
    pil_img = ImageOps.expand(pil_img, border=1, fill=(0, 0, 0))
    pil_img.save(img_path)

    result = {
        'filename': fname,
        'width_px': w,
        'height_px': h,
        'img_idx': img_counter,
        'caption': caption
    }
    img_counter += 1
    return result

# Process all tables
table_images = []
for i, t in enumerate(tbl_positions):
    result = render_table_to_image(t['caption'], t['rows'], i + 1)
    if result:
        table_images.append(result)
        print(f"  Table {i+1}: -> {result['filename']} ({result['width_px']}x{result['height_px']})")

print(f"\nGenerated {len(table_images)} table images")

# Save table data for replacement step
import json
with open(os.path.join(OUT_DIR, '..', '..', '..', '数模', '_docx_tools', '_table_data.json'), 'w', encoding='utf-8') as f:
    json.dump({
        'positions': [{'start': t['start'], 'end': t['end'], 'caption': t['caption']} for t in tbl_positions],
        'images': table_images
    }, f, ensure_ascii=False, indent=2)

print("Table data saved for replacement step")
