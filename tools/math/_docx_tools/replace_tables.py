"""
Replace native Word tables with generated table images
Uses string replacement on the XML text
"""
import re, os, html as html_mod

UNPACKED = r"d:\GIT\public\数模\_unpacked_论文1.5"
DOC_XML = os.path.join(UNPACKED, "word", "document.xml")
RELS_PATH = os.path.join(UNPACKED, "word", "_rels", "document.xml.rels")
MEDIA_DIR = os.path.join(UNPACKED, "word", "media")

# Read document
with open(DOC_XML, 'r', encoding='utf-8') as f:
    content = f.read()

# Read rels
with open(RELS_PATH, 'r', encoding='utf-8') as f:
    rels = f.read()

# Find next RID
rids = [int(m.group(1)) for m in re.finditer(r'rId(\d+)', rels)]
next_rid = max(rids) + 1

# Find all tables
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

print(f"Found {len(tbls)} tables")

from PIL import Image

# Build image XML template without the caption (it's already in the image)
def make_image_xml(img_path, rid, img_id):
    """Generate the XML for an inline image."""
    pil_img = Image.open(img_path)
    px_w, px_h = pil_img.size
    # EMU at image DPI (200 DPI for generated tables)
    dpi = 200
    emu_w = int(px_w * 914400 / dpi)
    emu_h = int(px_h * 914400 / dpi)
    fname = os.path.basename(img_path)

    return f'''<ns0:p>
      <ns0:pPr>
        <ns0:jc ns0:val="center"/>
        <ns0:spacing ns0:line="240" ns0:lineRule="auto" ns0:before="60" ns0:after="60"/>
      </ns0:pPr>
      <ns0:r>
        <ns0:rPr>
          <ns0:noProof/>
        </ns0:rPr>
        <ns0:drawing>
          <ns4:inline distT="0" distB="0" distL="0" distR="0">
            <ns4:extent cx="{emu_w}" cy="{emu_h}"/>
            <ns4:effectExtent l="0" t="0" r="0" b="0"/>
            <ns4:docPr id="{img_id}" name="{fname}"/>
            <ns4:cNvGraphicFramePr>
              <ns5:graphicFrameLocks noChangeAspect="1"/>
            </ns4:cNvGraphicFramePr>
            <ns5:graphic>
              <ns5:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <ns6:pic>
                  <ns6:nvPicPr>
                    <ns6:cNvPr id="0" name="{fname}"/>
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
    </ns0:p>''', emu_w, emu_h

# Process tables in reverse (preserving positions)
print("\nReplacing tables...")
img_id = 100  # Starting ID for new images

for i in range(len(tbls) - 1, -1, -1):
    t = tbls[i]
    img_num = 24 + i  # image24 = Table 1

    # Check if image exists
    img_fname = f'image{img_num}.png'
    img_path = os.path.join(MEDIA_DIR, img_fname)
    if not os.path.exists(img_path):
        print(f"  WARNING: {img_fname} not found")
        continue

    # Get caption
    tbl_xml = content[t['start']:t['end']]
    cap_m = re.search(r'<ns0:tblCaption ns0:val="([^"]*)"', tbl_xml)
    caption = html_mod.unescape(cap_m.group(1)) if cap_m else ''

    # Create image XML
    rid = f'rId{next_rid}'
    next_rid += 1
    img_xml, emu_w, emu_h = make_image_xml(img_path, rid, img_id)
    img_id += 1

    # Build final replacement (image + caption)
    # Add caption paragraph with 表N: prefix
    table_num = i + 1
    full_caption = f'表{table_num}  {caption}'

    caption_xml = f'''<ns0:p>
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

    replacement = img_xml + caption_xml

    # Replace table
    content = content[:t['start']] + replacement + content[t['end']:]

    # Add relationship
    rel_entry = f'  <Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{img_fname}"/>'
    rels = rels.replace('</Relationships>', f'{rel_entry}\n</Relationships>')

    emu_w_in = emu_w / 914400
    emu_h_in = emu_h / 914400
    print(f"  T{i+1}: {img_fname} -> {emu_w_in:.1f}x{emu_h_in:.1f}in replaced")

# Save
with open(DOC_XML, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"\nSaved document.xml")

with open(RELS_PATH, 'w', encoding='utf-8') as f:
    f.write(rels)
rel_count = rels.count('Relationship Id=')
print(f"Saved document.xml.rels ({rel_count} relationships)")

print("\nDone! Pack with pack.py to create final docx.")
