import sys
from datetime import datetime, timezone

SKILL_ROOT = r"c:\Users\全佳鹏\.claude\skills\word-document-processor"
if SKILL_ROOT not in sys.path:
    sys.path.insert(0, SKILL_ROOT)

from scripts.document import Document

TARGET_BEFORE = 120  # 6pt spacing
TARGET_AFTER = 120   # 6pt spacing
TEXT_THRESHOLD = 30


def _direct_child(elem, tag):
    for child in elem.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.tagName == tag:
            return child
    return None


def _paragraph_text(p):
    parts = []
    for t in p.getElementsByTagName("w:t"):
        if t.firstChild and t.firstChild.nodeType == t.TEXT_NODE:
            parts.append(t.firstChild.data)
    return "".join(parts).strip()


def _should_adjust(p):
    text_len = len(_paragraph_text(p))
    has_math_para = bool(p.getElementsByTagName("m:oMathPara"))
    has_math = bool(p.getElementsByTagName("m:oMath"))
    has_drawing = bool(p.getElementsByTagName("w:drawing"))
    has_pict = bool(p.getElementsByTagName("w:pict"))
    has_object = bool(p.getElementsByTagName("w:object"))

    if has_math_para:
        return True
    if has_math and text_len <= TEXT_THRESHOLD:
        return True
    if (has_drawing or has_pict or has_object) and text_len <= TEXT_THRESHOLD:
        return True
    return False


def _max_change_id(dom):
    max_id = -1
    for tag in ("w:ins", "w:del", "w:pPrChange"):
        for elem in dom.getElementsByTagName(tag):
            val = elem.getAttribute("w:id")
            if val.isdigit():
                max_id = max(max_id, int(val))
    return max_id


def _ensure_spacing(dom, p, change_id, timestamp):
    ppr = _direct_child(p, "w:pPr")
    if not ppr:
        ppr = dom.createElement("w:pPr")
        if p.firstChild:
            p.insertBefore(ppr, p.firstChild)
        else:
            p.appendChild(ppr)

    has_ppr_change = any(
        child.nodeType == child.ELEMENT_NODE and child.tagName == "w:pPrChange"
        for child in ppr.childNodes
    )

    original_ppr = ppr.cloneNode(True)

    spacing = _direct_child(ppr, "w:spacing")
    if not spacing:
        spacing = dom.createElement("w:spacing")
        insert_before = None
        for tag in ("w:ind", "w:jc"):
            node = _direct_child(ppr, tag)
            if node:
                insert_before = node
                break
        if insert_before:
            ppr.insertBefore(spacing, insert_before)
        else:
            ppr.appendChild(spacing)

    curr_before = int(spacing.getAttribute("w:before") or 0)
    curr_after = int(spacing.getAttribute("w:after") or 0)
    new_before = max(curr_before, TARGET_BEFORE)
    new_after = max(curr_after, TARGET_AFTER)

    changed = False
    if new_before != curr_before:
        spacing.setAttribute("w:before", str(new_before))
        changed = True
    if new_after != curr_after:
        spacing.setAttribute("w:after", str(new_after))
        changed = True

    if changed and not has_ppr_change:
        for child in list(original_ppr.childNodes):
            if child.nodeType == child.ELEMENT_NODE and child.tagName == "w:pPrChange":
                original_ppr.removeChild(child)

        ppr_change = dom.createElement("w:pPrChange")
        ppr_change.setAttribute("w:id", str(change_id))
        ppr_change.setAttribute("w:author", "Claude")
        ppr_change.setAttribute("w:date", timestamp)
        ppr_change.appendChild(original_ppr)
        ppr.appendChild(ppr_change)

    return changed


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python adjust_spacing.py <unpacked_dir>")

    unpacked_dir = sys.argv[1]
    doc = Document(unpacked_dir, rsid="3BD2F05D", track_revisions=True)
    editor = doc["word/document.xml"]
    dom = editor.dom

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    next_change_id = _max_change_id(dom) + 1

    updated = 0
    for p in dom.getElementsByTagName("w:p"):
        if not _should_adjust(p):
            continue
        if _ensure_spacing(dom, p, next_change_id, timestamp):
            updated += 1
            next_change_id += 1

    doc.save(validate=False)
    print(f"Updated paragraphs: {updated}")


if __name__ == "__main__":
    main()
