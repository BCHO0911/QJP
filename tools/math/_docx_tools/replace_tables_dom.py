"""
Replace native Word tables with images using Document library DOM
Proper namespace handling
"""
import sys, os, re
SKILL_ROOT = r"C:\Users\全佳鹏\.claude\skills\word-document-processor"
sys.path.insert(0, SKILL_ROOT)
from scripts.document import Document
from PIL import Image

UNPACKED = r"d:\GIT\public\数模\_unpacked_论文1.5"
doc = Document(UNPACKED)
editor = doc["word/document.xml"]

MEDIA_DIR = os.path.join(doc.unpacked_path, "word", "media")

# Find all tbl elements by tag name
all_elems = editor.dom.getElementsByTagName('*')
tbls = [e for e in all_elems if e.tagName in ('tbl', 'w:tbl')]
print(f"Found {len(tbls)} tables")

# Get next available image IDs
rels_editor = doc['word/_rels/document.xml.rels']
next_rid = rels_editor.get_next_rid()

import re as re_mod
rels_content = open(os.path.join(doc.unpacked_path, "word", "_rels", "document.xml.rels"), 'r', encoding='ascii').read()

img_id = 300
replaced = 0

for i, tbl in enumerate(tbls):
    fname = f'tbl_{i+1}.png'
    path = os.path.join(MEDIA_DIR, fname)
    if not os.path.exists(path):
        print(f"  WARNING: {fname} not found")
        continue

    pil = Image.open(path)
    px_w, px_h = pil.size
    emu_w = int(px_w * 914400 / 250)
    emu_h = int(px_h * 914400 / 250)

    # Build image XML as string, then let Document library parse it
    # Use proper namespace handling
    img_xml_str = f'''<w:p>
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
                  <pic:blipFill><a:blip r:embed="{next_rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
                  <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm><a:prstGeom prst="rect"/></pic:spPr>
                </pic:pic>
              </a:graphicData>
            </a:graphic>
          </wp:inline>
        </w:drawing>
      </w:r>
    </w:p>'''

    # Replace tbl with image paragraph
    editor.replace_node(tbl, img_xml_str)

    # Add relationship
    rel_entry = f'<Relationship Id="{next_rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{fname}"/>'
    rels_editor.append_to(rels_editor.dom.documentElement, re_mod.escape(rel_entry))

    # Actually need to handle rels differently - use string replacement
    rels_content = rels_content.replace('</Relationships>', f'\n{rel_entry}\n</Relationships>')

    img_id += 1
    next_rid = rels_editor.get_next_rid()
    replaced += 1
    print(f"  T{i+1}: replaced with {fname}")

# Save rels
with open(os.path.join(doc.unpacked_path, "word", "_rels", "document.xml.rels"), 'w', encoding='ascii') as f:
    f.write(rels_content)

# Save document
doc.save(validate=False)
print(f"\nReplaced {replaced}/{len(tbls)} tables. Done!")
