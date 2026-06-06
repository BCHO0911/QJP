"""
Fix image centering and caption formatting
Uses direct regex on XML text for reliability
"""
import re, os

DOC_XML = r"d:\GIT\public\数模\_unpacked_论文1.5\word\document.xml"

with open(DOC_XML, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ============================================================
# 1. Center all image paragraphs
# ============================================================
print("[1/2] Centering image paragraphs...")

# Find each blip and add center to its containing paragraph
# Pattern: find blip, go up to find the opening <ns0:p, check for center, add if missing
blip_count = content.count('ns5:blip')
print(f"  Found {blip_count} blip references")

# Strategy: For each paragraph containing a blip, ensure it has jc=center
# Find all paragraphs with blips
para_pattern = r'(<ns0:p[^>]*>(?:.(?!</ns0:p>))*?ns5:blip.*?</ns0:p>)'
paras_with_blips = re.findall(para_pattern, content, re.DOTALL)
print(f"  Paragraphs containing blips: {len(paras_with_blips)}")

for para in paras_with_blips:
    # Check if already has center
    if 'ns0:val="center"' in para or "ns0:val='center'" in para:
        continue

    # Check if pPr exists
    if '<ns0:pPr>' in para or '<ns0:pPr ' in para:
        # Add jc=center inside pPr
        # Find the closing of pPr
        if '<ns0:pPr>' in para:
            # Simple pPr without attributes
            old = '<ns0:pPr>'
            new = '<ns0:pPr><ns0:jc ns0:val="center"/>'
        else:
            # pPr with attributes
            # Find first ns0:jc or closing >
            ppr_end = para.index('</ns0:pPr>') if '</ns0:pPr>' in para else -1
            if ppr_end > 0:
                # Find the start of pPr
                ppr_start = para.index('<ns0:pPr')
                old = para[ppr_start:ppr_end+12]
                # Add jc before closing
                new = old.replace('</ns0:pPr>', '<ns0:jc ns0:val="center"/></ns0:pPr>')
    else:
        # Need to create pPr with jc
        old = '<ns0:p>'
        new = '<ns0:p><ns0:pPr><ns0:jc ns0:val="center"/></ns0:pPr>'

    if old != new:
        content = content.replace(old, new, 1)
        changes += 1

# Find remaining image paragraphs that might not match the pattern
# Check paragraphs with ns5:blip by searching differently
for m in re.finditer(r'<ns0:p[^>]*>.*?ns5:blip', content, re.DOTALL):
    para_start = m.start()
    para_end = content.find('</ns0:p>', m.start()) + 9
    para = content[para_start:para_end]

    if 'ns0:val="center"' not in para:
        # Add center to this paragraph
        if '<ns0:pPr>' in para:
            old = content[para_start:para_end].split('<ns0:pPr>')[0] + '<ns0:pPr>'
            new = old + '<ns0:jc ns0:val="center"/>'
            content = content.replace(old, new, 1)
            changes += 1
        elif '<ns0:pPr ' in para:
            # pPr with attributes
            ppr_end = content.index('</ns0:pPr>', para_start)
            old = content[para_start:ppr_end+12]
            new = old.replace('</ns0:pPr>', '<ns0:jc ns0:val="center"/></ns0:pPr>')
            content = content.replace(old, new, 1)
            changes += 1
        else:
            old = content[para_start:para_start+8]  # '<ns0:p>'
            new = '<ns0:p><ns0:pPr><ns0:jc ns0:val="center"/></ns0:pPr>'
            content = content.replace(old, new, 1)
            changes += 1

print(f"  Made {changes} changes to center images")

# ============================================================
# 2. Ensure caption paragraphs are centered
# ============================================================
print("\n[2/2] Centering caption paragraphs...")

# Captions are paragraphs with font 黑体 五号 (sz=21)
# that follow image paragraphs or precede/follow tables
caption_changes = 0

# Find paragraphs with sz=21 (五号) that aren't already centered
for m in re.finditer(r'<ns0:p[^>]*>.*?ns0:sz ns0:val="21".*?</ns0:p>', content, re.DOTALL):
    para = m.group()
    if 'ns0:val="center"' not in para:
        # Check if it's a caption (has text longer than 3 chars)
        texts = re.findall(r'<ns0:t[^>]*>([^<]+)', para)
        if any(len(t) > 3 for t in texts):
            # Center it
            if '<ns0:pPr>' in para:
                old = '<ns0:pPr>'
                new = '<ns0:pPr><ns0:jc ns0:val="center"/>'
                content = content.replace(para.replace('<ns0:pPr>', '|||PPR|||', 1).replace('|||PPR|||', '<ns0:pPr>'),
                                         para.replace('<ns0:pPr>', '<ns0:pPr><ns0:jc ns0:val="center"/>', 1), 1)
                caption_changes += 1
            elif '<ns0:pPr ' in para:
                ppr_end = para.index('</ns0:pPr>')
                old_part = para[:ppr_end+12]
                new_part = old_part.replace('</ns0:pPr>', '<ns0:jc ns0:val="center"/></ns0:pPr>')
                content = content.replace(old_part, new_part, 1)
                caption_changes += 1

print(f"  Centered {caption_changes} caption paragraphs")

# ============================================================
# 3. SAVE
# ============================================================
with open(DOC_XML, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nTotal changes: {changes + caption_changes}")
print("Done! Now pack with pack.py")
