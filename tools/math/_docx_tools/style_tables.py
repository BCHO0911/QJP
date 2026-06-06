"""
Style all tables using table property editing
Robust namespace handling
"""
import sys
SKILL_ROOT = r"C:\Users\全佳鹏\.claude\skills\word-document-processor"
sys.path.insert(0, SKILL_ROOT)
from scripts.document import Document

UNPACKED = r"d:\GIT\public\数模\_unpacked_论文1.5"
doc = Document(UNPACKED)
editor = doc["word/document.xml"]

def is_tag(elem, name):
    """Check if element has the given local tag name."""
    if not elem or not hasattr(elem, 'tagName'):
        return False
    tag = elem.tagName
    return tag == name or tag == f'w:{name}' or tag.split('}')[-1] == name

def C(tag): return f'w:{tag}'

def create(tag):
    return editor.dom.createElement(tag if ':' in tag else f'w:{tag}')

def set_w(elem, attr, val):
    elem.setAttribute(f'w:{attr}', val)

def remove_tag(parent, local):
    to_kill = []
    for child in parent.childNodes:
        if child.nodeType != child.ELEMENT_NODE: continue
        if is_tag(child, local):
            to_kill.append(child)
    for c in to_kill:
        parent.removeChild(c)

# Find tables
all_elems = editor.dom.getElementsByTagName('*')
tbls = [e for e in all_elems if is_tag(e, 'tbl')]
print(f"Found {len(tbls)} tables")

for ti, tbl in enumerate(tbls):
    # Get tblPr
    tblPr = None
    for child in tbl.childNodes:
        if child.nodeType == child.ELEMENT_NODE and is_tag(child, 'tblPr'):
            tblPr = child
            break
    if tblPr is None:
        tblPr = create('tblPr')
        tbl.insertBefore(tblPr, tbl.firstChild)

    # Borders (thin black lines on all sides + inside)
    remove_tag(tblPr, 'tblBorders')
    borders = create('tblBorders')
    for side in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        be = create(side)
        for a, v in [('val', 'single'), ('sz', '4'), ('space', '0'), ('color', '000000')]:
            be.setAttribute(f'w:{a}', v)
        borders.appendChild(be)
    tblPr.appendChild(borders)

    # Width 100%
    remove_tag(tblPr, 'tblW')
    tw = create('tblW')
    tw.setAttribute('w:w', '5000')
    tw.setAttribute('w:type', 'pct')
    tblPr.appendChild(tw)

    # Center
    remove_tag(tblPr, 'jc')
    jc = create('jc')
    jc.setAttribute('w:val', 'center')
    tblPr.appendChild(jc)

    remove_tag(tblPr, 'tblInd')

    # Style rows
    rows = []
    for child in tbl.childNodes:
        if child.nodeType == child.ELEMENT_NODE and is_tag(child, 'tr'):
            rows.append(child)

    for ri, tr in enumerate(rows):
        # Find cells
        cells = []
        for child in tr.childNodes:
            if child.nodeType == child.ELEMENT_NODE and is_tag(child, 'tc'):
                cells.append(child)

        for cell in cells:
            tcPr = None
            for child in cell.childNodes:
                if child.nodeType == child.ELEMENT_NODE and is_tag(child, 'tcPr'):
                    tcPr = child
                    break
            if tcPr is None:
                tcPr = create('tcPr')
                cell.insertBefore(tcPr, cell.firstChild)

            if ri == 0:
                # Header: light blue
                remove_tag(tcPr, 'shd')
                shd = create('shd')
                shd.setAttribute('w:val', 'clear')
                shd.setAttribute('w:color', 'auto')
                shd.setAttribute('w:fill', 'D6EAF8')
                tcPr.appendChild(shd)

                # Bold + SimHei in runs
                for r in cell.getElementsByTagName('*'):
                    if not is_tag(r, 'r'): continue
                    rPr = None
                    for c in r.childNodes:
                        if c.nodeType == c.ELEMENT_NODE and is_tag(c, 'rPr'):
                            rPr = c
                            break
                    if rPr is None:
                        rPr = create('rPr')
                        r.insertBefore(rPr, r.firstChild)

                    if not rPr.getElementsByTagName('*') or not [c for c in rPr.childNodes if is_tag(c, 'b')]:
                        rPr.appendChild(create('b'))

                    remove_tag(rPr, 'rFonts')
                    rf = create('rFonts')
                    rf.setAttribute('w:ascii', '黑体')
                    rf.setAttribute('w:hAnsi', '黑体')
                    rf.setAttribute('w:eastAsia', '黑体')
                    rf.setAttribute('w:cs', '黑体')
                    rPr.appendChild(rf)
            else:
                # Data rows: SimSun
                remove_tag(tcPr, 'shd')
                for r in cell.getElementsByTagName('*'):
                    if not is_tag(r, 'r'): continue
                    rPr = None
                    for c in r.childNodes:
                        if c.nodeType == c.ELEMENT_NODE and is_tag(c, 'rPr'):
                            rPr = c
                            break
                    if rPr is None:
                        rPr = create('rPr')
                        r.insertBefore(rPr, r.firstChild)

                    remove_tag(rPr, 'rFonts')
                    rf = create('rFonts')
                    rf.setAttribute('w:ascii', '宋体')
                    rf.setAttribute('w:hAnsi', '宋体')
                    rf.setAttribute('w:eastAsia', '宋体')
                    rf.setAttribute('w:cs', '宋体')
                    rPr.appendChild(rf)

            # Vertical center
            remove_tag(tcPr, 'vAlign')
            va = create('vAlign')
            va.setAttribute('w:val', 'center')
            tcPr.appendChild(va)

    if ti < 5:
        print(f"  T{ti+1}: {len(rows)} rows, {len(cells) if rows else 0} cols")

print(f"\nStyled {len(tbls)} tables. Saving...")
doc.save(validate=False)
print("Done! Pack with pack.py")
