"""
Center all figures, tables, and their captions
Format captions consistently (黑体 五号)
"""
import sys, re, html
SKILL_ROOT = r"C:\Users\全佳鹏\.claude\skills\word-document-processor"
sys.path.insert(0, SKILL_ROOT)
from scripts.document import Document

UNPACKED = r"d:\GIT\public\数模\_unpacked_论文1.5"
doc = Document(UNPACKED)

def remove_child_tags(parent, local_name):
    to_kill = []
    for child in parent.childNodes:
        tag = child.nodeName.split('}')[-1]
        if tag == local_name or tag == f'w:{local_name}' or tag == f'ns0:{local_name}':
            to_kill.append(child)
    for c in to_kill:
        parent.removeChild(c)

def ensure_child(parent, local_name):
    for child in parent.childNodes:
        tag = child.nodeName.split('}')[-1]
        if tag == local_name or tag == f'w:{local_name}' or tag == f'ns0:{local_name}':
            return child
    new_elem = parent.ownerDocument.createElement(local_name)
    parent.appendChild(new_elem)
    return new_elem

def C(tag):
    return f'ns0:{tag}'

def get_text(p):
    parts = []
    for t in p.getElementsByTagName(C("t")):
        for cn in t.childNodes:
            if cn.nodeValue:
                parts.append(cn.nodeValue)
    return ''.join(parts).strip()

def set_center(p):
    """Set paragraph to center alignment."""
    pPr = ensure_child(p, C("pPr"))
    remove_child_tags(pPr, "jc")
    jc = pPr.ownerDocument.createElement(C("jc"))
    jc.setAttribute("ns0:val", "center")
    pPr.appendChild(jc)

def format_caption(p):
    """Format caption paragraph: 黑体 五号 centered."""
    pPr = ensure_child(p, C("pPr"))
    # Center
    remove_child_tags(pPr, "jc")
    jc = pPr.ownerDocument.createElement(C("jc"))
    jc.setAttribute("ns0:val", "center")
    pPr.appendChild(jc)
    # Remove first-line indent
    remove_child_tags(pPr, "ind")
    # Set spacing
    remove_child_tags(pPr, "spacing")
    sp = pPr.ownerDocument.createElement(C("spacing"))
    sp.setAttribute("ns0:line", "240")
    sp.setAttribute("ns0:lineRule", "auto")
    sp.setAttribute("ns0:before", "60")
    sp.setAttribute("ns0:after", "120")
    pPr.appendChild(sp)

    # Apply font to runs
    for r in p.getElementsByTagName(C("r")):
        rPr = ensure_child(r, C("rPr"))
        remove_child_tags(rPr, "rFonts")
        rf = rPr.ownerDocument.createElement(C("rFonts"))
        rf.setAttribute("ns0:ascii", "黑体")
        rf.setAttribute("ns0:hAnsi", "黑体")
        rf.setAttribute("ns0:eastAsia", "黑体")
        rf.setAttribute("ns0:cs", "黑体")
        rPr.appendChild(rf)
        remove_child_tags(rPr, "sz")
        sz = rPr.ownerDocument.createElement(C("sz"))
        sz.setAttribute("ns0:val", "21")  # 五号 = 10.5pt
        rPr.appendChild(sz)
        remove_child_tags(rPr, "szCs")
        szCs = rPr.ownerDocument.createElement(C("szCs"))
        szCs.setAttribute("ns0:val", "21")
        rPr.appendChild(szCs)

editor = doc["word/document.xml"]
body = editor.dom.getElementsByTagName(C("body"))[0]
paras = body.getElementsByTagName(C("p"))
print(f"Total paragraphs: {len(paras)}")

# ============================================================
# 1. CENTER ALL IMAGE PARAGRAPHS AND THEIR CAPTIONS
# ============================================================
print("\n[1/3] Centering images and captions...")
img_count = 0
caption_count = 0

for i, p in enumerate(paras):
    blips = p.getElementsByTagName(C("blip")) if hasattr(C, '__call__') else []
    # Check for blip in any namespace
    blips_found = []
    for child in p.getElementsByTagName("*"):
        tag = child.tagName.split('}')[-1]
        if tag == 'blip' or tag.endswith(':blip') or tag == 'ns5:blip':
            blips_found.append(child)

    if blips_found:
        # Center the image paragraph
        set_center(p)
        img_count += 1
        if img_count <= 3:
            print(f"  P{i}: Image centered")

        # Also format the next paragraph (caption)
        if i + 1 < len(paras):
            next_p = paras[i + 1]
            next_text = get_text(next_p)
            if next_text and any(c in next_text for c in ['图', '表', 'Fig', 'Tab']):
                format_caption(next_p)
                caption_count += 1
            elif next_text and len(next_text) > 5:
                # It might be a caption without explicit label
                # Check if it looks like a caption (descriptive text)
                # Also check the paragraph after next
                format_caption(next_p)
                caption_count += 1

print(f"  Centered {img_count} images")
print(f"  Formatted {caption_count} captions")

# ============================================================
# 2. CENTER ALL TABLE PARAGRAPHS
# ============================================================
print("\n[2/3] Centering tables...")
tbl_count = 0

# Tables are direct children of body in this document
# Find all tbl elements and center them via tblPr
body_elems = editor.dom.getElementsByTagName("ns0:body")[0]
all_elems = editor.dom.getElementsByTagName("*")

for e in all_elems:
    if e.tagName == "ns0:tbl":
        # Get or create tblPr
        tblPr = None
        for child in e.childNodes:
            if child.nodeName == "ns0:tblPr":
                tblPr = child
                break

        if tblPr is None:
            tblPr = e.ownerDocument.createElement("ns0:tblPr")
            e.insertBefore(tblPr, e.firstChild)

        # Set center alignment on table
        # Remove existing jc
        jc_old = None
        for child in tblPr.childNodes:
            if child.nodeName == "ns0:jc":
                jc_old = child
                break
        if jc_old:
            jc_old.setAttribute("ns0:val", "center")
        else:
            jc = e.ownerDocument.createElement("ns0:jc")
            jc.setAttribute("ns0:val", "center")
            tblPr.appendChild(jc)

        tbl_count += 1

print(f"  Centered {tbl_count} tables")

# ============================================================
# 3. FORMAT ANY REMAINING CAPTION-LIKE PARAGRAPHS
# ============================================================
print("\n[3/3] Formatting remaining captions...")
extra_captions = 0
for i, p in enumerate(paras):
    text = get_text(p)
    if not text:
        continue

    # Check if it looks like a table/figure caption
    is_table_caption = any(text.startswith(t) for t in ['表', 'Tab']) and len(text) > 3
    is_figure_caption = any(text.startswith(t) for t in ['图', 'Fig']) and len(text) > 3

    if is_table_caption or is_figure_caption:
        # Check if already formatted by checking font
        rFonts = p.getElementsByTagName(C("rFonts"))
        already_done = False
        for rf in rFonts:
            if rf.getAttribute("ns0:ascii") == "黑体":
                already_done = True
                break

        if not already_done:
            format_caption(p)
            extra_captions += 1

print(f"  Formatted {extra_captions} additional captions")

# ============================================================
# SAVE
# ============================================================
print("\nSaving...")
doc.save(validate=False)
print("Done! Pack with pack.py to create final docx.")
