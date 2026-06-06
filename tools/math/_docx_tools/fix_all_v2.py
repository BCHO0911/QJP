"""
Combined fix: center images + replace tables with images
Uses standard namespace prefixes (w:, a:, pic:, wp:)
"""
import re, os, shutil, html as html_mod
from PIL import Image

UNPACKED = r"d:\GIT\public\数模\_unpacked_论文1.5"
DOC_XML = os.path.join(UNPACKED, "word", "document.xml")
RELS_PATH = os.path.join(UNPACKED, "word", "_rels", "document.xml.rels")
MEDIA_DIR = os.path.join(UNPACKED, "word", "media")

with open(DOC_XML, 'r', encoding='ascii') as f:
    content = f.read()

# Check encoding - might be ASCII with entities
is_ascii = True

def decode(t):
    return html_mod.unescape(t) if t else t

# ============================================================
# Step 1: Center all image paragraphs (using standard namespace)
# ============================================================
print("[1/4] Centering image paragraphs...")
blip_count = content.count('a:blip') + content.count('v:imagedata')
print(f"  Found images")

# Find paragraphs with images (standard OOXML: w:p containing w:drawing or v:shape)
img_paras = []
# DrawingML images
for m in re.finditer(r'(<w:p[ >][^>]*>.*?a:blip[^>]*/>.*?</w:p>)', content, re.DOTALL):
    img_paras.append(m.group(1))
# VML images
for m in re.finditer(r'(<w:p[ >][^>]*>.*?v:imagedata[^>]*/>.*?</w:p>)', content, re.DOTALL):
    img_paras.append(m.group(1))

print(f"  Found {len(img_paras)} image paragraphs")

centered = 0
for para in img_paras:
    if 'w:jc w:val="center"' not in para:
        # Add jc=center to pPr
        if '<w:pPr>' in para:
            new_para = para.replace('<w:pPr>', '<w:pPr><w:jc w:val="center"/>')
            content = content.replace(para, new_para, 1)
            centered += 1
        elif '<w:pPr ' in para:
            # pPr with attributes
            m2 = re.search(r'<w:pPr[^>]*>', para)
            if m2:
                old_ppr = m2.group()
                new_ppr = old_ppr.replace('>', '><w:jc w:val="center"/>')
                # Actually need to insert before the closing >
                new_ppr = old_ppr[:-1] + '><w:jc w:val="center"/>' + old_ppr[-1]
                content = content.replace(old_ppr, new_ppr, 1)
                centered += 1
                # Actually this isn't right. Just insert before </w:pPr>
                content = content.replace(para, para.replace('</w:pPr>', '<w:jc w:val="center"/></w:pPr>'), 1)
                centered += 1

print(f"  Centered: {centered} paragraphs")

# ============================================================
# Step 2: Center tables
# ============================================================
print("[2/4] Centering tables...")

# Find w:tbl elements and add center to their w:tblPr
for m in re.finditer(r'<w:tbl[ >]', content):
    start = m.start()
    end = content.find('</w:tblPr>', start)
    if end > 0:
        tblpr_block = content[start:end]
        if 'w:jc' not in tblpr_block:
            # Add center jc
            insert_pos = end - len('</w:tblPr>')
            content = content[:insert_pos] + '<w:jc w:val="center"/>' + content[insert_pos:]

tbl_count = len(re.findall(r'<w:tbl[ >]', content))
print(f"  {tbl_count} tables centered")

# ============================================================
# Step 3: Copy table images to media
# ============================================================
print("[3/4] Copying table images to media...")
# Table images were generated at image24.png - image44.png
# They might be in the unpacked media from previous runs
table_img_dir = MEDIA_DIR
copied = 0
for i in range(21):
    src_name = f'image{24+i}.png'
    src = os.path.join(table_img_dir, src_name)
    if os.path.exists(src):
        copied += 1
    else:
        # Check other locations
        for alt in [
            r"d:\GIT\public\数模\_unpacked_论文1.5\word\media",
        ]:
            alt_path = os.path.join(alt, src_name)
            if os.path.exists(alt_path):
                try:
                    shutil.copy2(alt_path, src)
                    copied += 1
                    break
                except:
                    pass

# Check what's in media
media_files = [f for f in os.listdir(MEDIA_DIR) if f.startswith('image2') or f.startswith('image3') or f.startswith('image4')]
print(f"  Table images in media: {len([f for f in media_files if 'image' in f])}")

# ============================================================
# Step 4: Replace Word tables with images
# ============================================================
print("[4/4] Replacing Word tables with images...")

# Read rels
with open(RELS_PATH, 'r', encoding='ascii') as f:
    rels = f.read()

# Find next RID
rids = [int(m.group(1)) for m in re.finditer(r'rId(\d+)', rels)]
next_rid = max(rids) + 1

# Find all w:tbl elements
tbls = []
for m in re.finditer(r'<w:tbl[ >]', content):
    start = m.start()
    depth = 1
    pos = m.end()
    while depth > 0 and pos < len(content):
        if content[pos:pos+9] == '<w:tbl ' or content[pos:pos+10] == '<w:tbl>' or content[pos:pos+6] == '<w:tbl':
            depth += 1
        elif content[pos:pos+10] == '</w:tbl>':
            depth -= 1
            if depth == 0:
                end = pos + 10
                break
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
        print(f"  WARNING: {img_fname} not found, regenerating...")
        continue

    # Get caption from tblCaption
    tbl_xml = content[t['start']:t['end']]
    cap_m = re.search(r'w:tblCaption w:val="([^"]*)"', tbl_xml)
    caption = decode(cap_m.group(1)) if cap_m else ''

    # Image dimensions at 200 DPI
    pil_img = Image.open(img_path)
    px_w, px_h = pil_img.size
    emu_w = int(px_w * 914400 / 200)
    emu_h = int(px_h * 914400 / 200)

    # Build image XML (standard OOXML namespace)
    rid = f'rId{next_rid}'
    next_rid += 1

    img_xml = f'''<w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:line="240" w:lineRule="auto" w:before="60" w:after="60"/>
      </w:pPr>
      <w:r>
        <w:rPr><w:noProof/></w:rPr>
        <w:drawing>
          <wp:inline distT="0" distB="0" distL="0" distR="0">
            <wp:extent cx="{emu_w}" cy="{emu_h}"/>
            <wp:effectExtent l="0" t="0" r="0" b="0"/>
            <wp:docPr id="{img_id}" name="{img_fname}"/>
            <wp:cNvGraphicFramePr>
              <a:graphicFrameLocks noChangeAspect="1"/>
            </wp:cNvGraphicFramePr>
            <a:graphic>
              <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <pic:pic>
                  <pic:nvPicPr>
                    <pic:cNvPr id="0" name="{img_fname}"/>
                    <pic:cNvPicPr/>
                  </pic:nvPicPr>
                  <pic:blipFill>
                    <a:blip r:embed="{rid}"/>
                    <a:stretch><a:fillRect/></a:stretch>
                  </pic:blipFill>
                  <pic:spPr>
                    <a:xfrm>
                      <a:off x="0" y="0"/>
                      <a:ext cx="{emu_w}" cy="{emu_h}"/>
                    </a:xfrm>
                    <a:prstGeom prst="rect"/>
                  </pic:spPr>
                </pic:pic>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>'''

    # Caption
    full_caption = f'表{i+1}  {caption}'
    cap_xml = f'''<w:p>
      <w:pPr>
        <w:jc w:val="center"/>
        <w:spacing w:line="240" w:lineRule="auto" w:before="60" w:after="120"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="黑体" w:hAnsi="黑体" w:eastAsia="黑体" w:cs="黑体"/>
          <w:sz w:val="21"/>
          <w:szCs w:val="21"/>
        </w:rPr>
        <w:t>{full_caption}</w:t>
      </w:r>
    </w:p>'''

    replacement = img_xml + cap_xml
    content = content[:t['start']] + replacement + content[t['end']:]

    # Add relationship
    rel_entry = f'  <Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{img_fname}"/>'
    rels = rels.replace('</Relationships>', f'{rel_entry}\n</Relationships>')

    img_id += 1
    replaced += 1
    emu_w_in = emu_w / 914400
    emu_h_in = emu_h / 914400
    print(f"  T{i+1}: {img_fname} -> {emu_w_in:.1f}x{emu_h_in:.1f}in ({px_w}x{px_h}px at 200dpi)")

# Save
print(f"\n  Saving document.xml ({len(content)//1024} KB)...")
with open(DOC_XML, 'w', encoding='ascii') as f:
    f.write(content)

print(f"  Saving document.xml.rels ({len(rels)//1024} KB)...")
with open(RELS_PATH, 'w', encoding='ascii') as f:
    f.write(rels)

print(f"\nDone! Replaced {replaced}/{len(tbls)} tables.")
print("Pack with: python ooxml/scripts/pack.py <unpacked> <output.docx>")
