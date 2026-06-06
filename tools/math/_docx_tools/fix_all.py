"""
Combined fix: center images + replace tables with images (correct DPI)
"""
import re, os, shutil, html as html_mod
from PIL import Image

UNPACKED = r"d:\GIT\public\数模\_unpacked_论文1.5"
DOC_XML = os.path.join(UNPACKED, "word", "document.xml")
RELS_PATH = os.path.join(UNPACKED, "word", "_rels", "document.xml.rels")
MEDIA_DIR = os.path.join(UNPACKED, "word", "media")

with open(DOC_XML, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# Step 1: Center all image paragraphs
# ============================================================
print("[1/4] Centering image paragraphs...")
blip_count = content.count('ns5:blip')
print(f"  Found {blip_count} blips")

for m in re.finditer(r'<ns0:p[^>]*>.*?ns5:blip', content, re.DOTALL):
    para_start = m.start()
    para_end = content.find('</ns0:p>', m.start()) + 9
    para = content[para_start:para_end]

    if 'ns0:val="center"' not in para:
        if '<ns0:pPr>' in para:
            old = '<ns0:pPr>'
            content = content[:para_start + para.index(old) + len(old)] + '<ns0:jc ns0:val="center"/>' + content[para_start + para.index(old) + len(old):]
        elif '<ns0:pPr ' in para:
            ppr_end = content.index('</ns0:pPr>', para_start)
            old = content[para_start:ppr_end+12]
            content = content.replace(old, old.replace('</ns0:pPr>', '<ns0:jc ns0:val="center"/></ns0:pPr>'), 1)
        else:
            old_start = content[para_start:para_start+8]
            if old_start == '<ns0:p>\n' or old_start == '<ns0:p>':
                content = content.replace(old_start, '<ns0:p><ns0:pPr><ns0:jc ns0:val="center"/></ns0:pPr>', 1)

# Verify
blip_centered = len(re.findall(r'<ns0:p[^>]*>.*?ns0:val="center".*?ns5:blip', content, re.DOTALL))
print(f"  Centered: {blip_centered}/{blip_count}")

# ============================================================
# Step 2: Center tables
# ============================================================
print("[2/4] Centering tables...")
tbl_count = len(re.findall(r'<ns0:tbl[ >]', content))
for m in re.finditer(r'<ns0:tbl[ >]', content):
    start = m.start()
    end = content.find('</ns0:tblPr>', start)
    if end > 0:
        tblpr = content[start:end]
        if 'ns0:jc' not in tblpr:
            # Add jc=center after tblW or at end of tblPr
            insert_pos = tblpr.rfind('ns0:val="auto"/>')
            if insert_pos > 0:
                actual_pos = start + insert_pos + 16
                content = content[:actual_pos] + '<ns0:jc ns0:val="center"/>' + content[actual_pos:]
            else:
                # Insert before </ns0:tblPr>
                insert_pos = start + tblpr.find('</ns0:tblPr>')
                content = content[:insert_pos] + '<ns0:jc ns0:val="center"/>' + content[insert_pos:]

tbl_centered = content.count('<ns0:jc ns0:val="center"/>')
print(f"  Tables with center: checking...")

# ============================================================
# Step 3: Copy table images to media
# ============================================================
print("[3/4] Copying table images...")
# Check if table images exist (from previous generation)
table_images_dir = r"d:\GIT\public\数模\_unpacked_论文1.5\word\media"
table_img_count = 0
for i in range(21):
    src_name = f'image{24+i}.png'
    src = os.path.join(table_images_dir, src_name)
    if os.path.exists(src):
        img = Image.open(src)
        table_img_count += 1
        if i < 3:
            print(f"  {src_name}: {img.size[0]}x{img.size[1]}")

if table_img_count == 0:
    # They might be in the previous unpacked - check other locations
    for path in [r"d:\GIT\public\数模\_docx_tools\preview",
                 r"d:\GIT\public\数模\_unpacked_论文1.5\word\media"]:
        for f in os.listdir(path):
            if f.startswith('image2') or f.startswith('image3') or f.startswith('image4'):
                shutil.copy2(os.path.join(path, f), os.path.join(MEDIA_DIR, f))
                table_img_count += 1

print(f"  Found {table_img_count} table images in media")

# ============================================================
# Step 4: Replace tables with images (correct DPI = 200)
# ============================================================
print("[4/4] Replacing tables with images...")

# Read rels
with open(RELS_PATH, 'r', encoding='utf-8') as f:
    rels = f.read()

# Find next RID
rids = [int(m.group(1)) for m in re.finditer(r'rId(\d+)', rels)]
next_rid = max(rids) + 1

# Find all tbl elements
tbls = []
for m in re.finditer(r'<ns0:tbl[ >]', content):
    start = m.start()
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
    tbls.append({'start': start, 'end': end})

print(f"  Found {len(tbls)} tables to replace")

img_id = 100
replaced = 0

for i in range(len(tbls) - 1, -1, -1):
    t = tbls[i]
    img_num = 24 + i
    img_fname = f'image{img_num}.png'
    img_path = os.path.join(MEDIA_DIR, img_fname)

    if not os.path.exists(img_path):
        print(f"  WARNING: {img_fname} not found, skipping T{i+1}")
        continue

    # Get caption
    tbl_xml = content[t['start']:t['end']]
    cap_m = re.search(r'<ns0:tblCaption ns0:val="([^"]*)"', tbl_xml)
    caption = html_mod.unescape(cap_m.group(1)) if cap_m else ''

    # Image dimensions at 200 DPI
    pil_img = Image.open(img_path)
    px_w, px_h = pil_img.size
    emu_w = int(px_w * 914400 / 200)
    emu_h = int(px_h * 914400 / 200)

    # Build image XML
    rid = f'rId{next_rid}'
    next_rid += 1

    img_xml = f'''<ns0:p>
      <ns0:pPr>
        <ns0:jc ns0:val="center"/>
        <ns0:spacing ns0:line="240" ns0:lineRule="auto" ns0:before="60" ns0:after="60"/>
      </ns0:pPr>
      <ns0:r>
        <ns0:rPr><ns0:noProof/></ns0:rPr>
        <ns0:drawing>
          <ns4:inline distT="0" distB="0" distL="0" distR="0">
            <ns4:extent cx="{emu_w}" cy="{emu_h}"/>
            <ns4:effectExtent l="0" t="0" r="0" b="0"/>
            <ns4:docPr id="{img_id}" name="{img_fname}"/>
            <ns4:cNvGraphicFramePr>
              <ns5:graphicFrameLocks noChangeAspect="1"/>
            </ns4:cNvGraphicFramePr>
            <ns5:graphic>
              <ns5:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <ns6:pic>
                  <ns6:nvPicPr>
                    <ns6:cNvPr id="0" name="{img_fname}"/>
                    <ns6:cNvPicPr/>
                  </ns6:nvPicPr>
                  <ns6:blipFill>
                    <ns5:blip ns7:embed="{rid}"/>
                    <ns5:stretch><ns5:fillRect/></ns5:stretch>
                  </ns6:blipFill>
                  <ns6:spPr>
                    <ns5:xfrm>
                      <ns5:off x="0" y="0"/>
                      <ns5:ext cx="{emu_w}" cy="{emu_h}"/>
                    </ns5:xfrm>
                    <ns5:prstGeom prst="rect"/>
                  </ns6:spPr>
                </ns6:pic>
              </ns5:graphicData>
            </ns5:graphic>
          </ns4:inline>
        </ns0:drawing>
      </ns0:r>
    </ns0:p>'''

    # Caption
    full_caption = f'表{i+1}  {caption}'
    cap_xml = f'''<ns0:p>
      <ns0:pPr>
        <ns0:jc ns0:val="center"/>
        <ns0:spacing ns0:line="240" ns0:lineRule="auto" ns0:before="60" ns0:after="120"/>
      </ns0:pPr>
      <ns0:r>
        <ns0:rPr>
          <ns0:rFonts ns0:ascii="&#40657;&#20307;" ns0:hAnsi="&#40657;&#20307;" ns0:eastAsia="&#40657;&#20307;" ns0:cs="&#40657;&#20307;"/>
          <ns0:sz ns0:val="21"/>
          <ns0:szCs ns0:val="21"/>
        </ns0:rPr>
        <ns0:t>{full_caption}</ns0:t>
      </ns0:r>
    </ns0:p>'''

    replacement = img_xml + cap_xml
    content = content[:t['start']] + replacement + content[t['end']:]

    # Add relationship
    rel_entry = f'  <Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{img_fname}"/>'
    rels = rels.replace('</Relationships>', f'{rel_entry}\n</Relationships>')

    img_id += 1
    replaced += 1
    emu_w_in = emu_w / 914400
    emu_h_in = emu_h / 914400
    print(f"  T{i+1}: {img_fname} -> {emu_w_in:.1f}x{emu_h_in:.1f}in ({px_w}x{px_h}px)")

# Save
with open(DOC_XML, 'w', encoding='utf-8') as f:
    f.write(content)
with open(RELS_PATH, 'w', encoding='utf-8') as f:
    f.write(rels)

print(f"\nDone! Replaced {replaced} tables. Pack with pack.py")
