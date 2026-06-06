"""
Fix:
1. Condense abstract to fit one page
2. Format appendix with proper structure (intro + code blocks)
3. Check font compliance
"""
import sys, os, re, html as html_mod
SKILL_ROOT = r"C:\Users\全佳鹏\.claude\skills\word-document-processor"
sys.path.insert(0, SKILL_ROOT)
from scripts.document import Document

UNPACKED = r"d:\GIT\public\数模\_unpacked_user"
doc = Document(UNPACKED)
editor = doc["word/document.xml"]

def C(tag): return f'w:{tag}'
def create(tag): return editor.dom.createElement(tag if ':' in tag else f'w:{tag}')
def set_w(e, a, v): e.setAttribute(f'w:{a}', v)
def remove_tag(parent, local):
    to_kill = []
    for child in parent.childNodes:
        if child.nodeType != child.ELEMENT_NODE: continue
        t = child.tagName.split('}')[-1]
        if t == local:
            to_kill.append(child)
    for c in to_kill:
        parent.removeChild(c)

def get_text(p):
    parts = []
    for t in p.getElementsByTagName(C('t')):
        for cn in t.childNodes:
            if cn.nodeValue:
                parts.append(cn.nodeValue)
    return html_mod.unescape(''.join(parts)).strip()

def set_runs_text(p, new_text):
    """Replace text in all runs of a paragraph."""
    runs = p.getElementsByTagName(C('r'))
    if runs:
        for i, r in enumerate(runs):
            t_elems = r.getElementsByTagName(C('t'))
            for t in t_elems:
                if t.firstChild:
                    if i == 0:
                        t.firstChild.nodeValue = new_text
                    else:
                        t.firstChild.nodeValue = ''
            if i > 0:
                r.parentNode.removeChild(r)
                # Keep only first run
        return True
    return False

def make_para(text, font='宋体', sz=21, bold=False, jc='left', spacing=240, first_line=0, insert_after=None):
    """Create a paragraph element."""
    p = create('p')
    pPr = create('pPr')
    if jc:
        jc_e = create('jc')
        set_w(jc_e, 'val', jc)
        pPr.appendChild(jc_e)
    sp = create('spacing')
    set_w(sp, 'line', str(spacing))
    set_w(sp, 'lineRule', 'auto')
    set_w(sp, 'before', '0')
    set_w(sp, 'after', '0')
    pPr.appendChild(sp)
    if first_line:
        ind = create('ind')
        set_w(ind, 'firstLine', str(first_line))
        pPr.appendChild(ind)
    p.appendChild(pPr)
    r = create('r')
    rPr = create('rPr')
    rf = create('rFonts')
    set_w(rf, 'ascii', font)
    set_w(rf, 'hAnsi', font)
    set_w(rf, 'eastAsia', font)
    rPr.appendChild(rf)
    sz_e = create('sz')
    set_w(sz_e, 'val', str(sz))
    rPr.appendChild(sz_e)
    szCs = create('szCs')
    set_w(szCs, 'val', str(sz))
    rPr.appendChild(szCs)
    if bold:
        rPr.appendChild(create('b'))
        rPr.appendChild(create('bCs'))
    r.appendChild(rPr)
    t = create('t')
    t.appendChild(editor.dom.createTextNode(text))
    r.appendChild(t)
    p.appendChild(r)
    return p

def make_code_line(line):
    """Create a code line paragraph (Courier New, 8pt, monospace)."""
    p = create('p')
    pPr = create('pPr')
    sp = create('spacing')
    set_w(sp, 'line', '200')
    set_w(sp, 'lineRule', 'auto')
    set_w(sp, 'before', '0')
    set_w(sp, 'after', '0')
    pPr.appendChild(sp)
    p.appendChild(pPr)
    r = create('r')
    rPr = create('rPr')
    rf = create('rFonts')
    set_w(rf, 'ascii', 'Courier New')
    set_w(rf, 'hAnsi', 'Courier New')
    rPr.appendChild(rf)
    sz_e = create('sz')
    set_w(sz_e, 'val', '14')
    rPr.appendChild(sz_e)
    r.appendChild(rPr)
    t = create('t')
    t.appendChild(editor.dom.createTextNode(line if line else ' '))
    r.appendChild(t)
    p.appendChild(r)
    return p

# ============================================================
# Find body
# ============================================================
body = editor.dom.getElementsByTagName(C('body'))[0]
paras = body.getElementsByTagName(C('p'))
print(f"Total paragraphs: {len(paras)}")

# ============================================================
# 1. CONDENSE ABSTRACT
# ============================================================
print("\n[1/3] Condensing abstract...")

# Find the abstract body paragraph (P2, first paragraph after "摘要" heading)
abstract_para = None
abstract_idx = -1
for i in range(len(paras)):
    text = get_text(paras[i])
    if text == '摘要':
        # The next paragraph with significant content is the abstract body
        for j in range(i+1, min(i+15, len(paras))):
            t2 = get_text(paras[j])
            if len(t2) > 20 and not t2.startswith('关键词'):
                abstract_para = paras[j]
                abstract_idx = j
                break
        break

if abstract_para:
    # New condensed abstract (~500 chars, fits one page)
    new_abstract = (
        "针对中老年人群高血脂症风险预警及干预方案优化问题，本文融合中医体质分类标签、"
        "痰湿体质特征量化指标、活动量表评分及血常规体检数据，构建\"体质辨识—风险预警—干预优化\""
        "三位一体的多维度数学模型框架。问题一采用LASSO回归、随机森林、Spearman相关和互信息"
        "四种方法交叉验证，从37维原始特征中筛选出14项表征痰湿体质严重程度的关键指标和10项"
        "预警高血脂发病风险的关键指标。Logistic回归OR值分析表明，阳虚质贡献度最高(OR=1.197)。"
        "问题二构建融合中医体质、西医血脂指标和活动能力的三级风险评分模型，将1000例样本划分为"
        "低风险232人(23.2%)、中风险540人(54.0%)、高风险228人(22.8%)。GradientBoosting模型"
        "表现最优(准确率90.80%, F1=0.9034)。消融实验表明，中医体质维度贡献31.8%的性能提升，"
        "中西医结合比纯西医指标提升49.1%。问题三针对278例痰湿体质患者构建优化模型，枚举全部"
        "可行方案提取1838个Pareto最优解，为每位患者提供\"最省钱-性价比-效果优先\"三套推荐方案。"
        "AHP层次分析确定多目标权重(效果53.9%>耐受29.7%>成本16.4%)，灵敏度分析验证了模型"
        "的鲁棒性(参数扰动下成本变化<2%)。"
    )
    set_runs_text(abstract_para, new_abstract)
    print(f"  Abstract condensed from P{abstract_idx}")
    print(f"  New length: {len(new_abstract)} chars")

    # The abstract body spans multiple paragraphs (P2-P9)
    # P2 is the first abstract body (already replaced), P3-P9 need clearing
    removed = 0
    for i in range(abstract_idx + 1, min(abstract_idx + 15, len(paras))):
        p = paras[i]
        text = get_text(p)
        if text.startswith('关键词'):
            break
        if text and len(text) > 5:
            runs = p.getElementsByTagName(C('r'))
            for r in runs:
                t_elems = r.getElementsByTagName(C('t'))
                for t in t_elems:
                    if t.firstChild:
                        t.firstChild.nodeValue = ''
            removed += 1
    print(f"  Cleared {removed} detailed abstract body paragraphs")
else:
    print("  WARNING: Could not find abstract paragraph!")

# ============================================================
# 2. REFORMAT APPENDIX
# ============================================================
print("\n[2/3] Reformatting appendix...")

# Find appendix section and reformat
# The appendix starts at P487 (附录A 支撑材料代码清单)
# We need to add proper introduction, section structure, and code formatting

# Find appendix start position
appendix_start = -1
for i in range(len(paras)):
    text = get_text(paras[i])
    if text == '附录A 支撑材料代码清单' or '支撑材料代码清单' in text:
        appendix_start = i
        break

if appendix_start >= 0:
    # The paragraph after the heading (P488) has an introduction
    # Find the introduction paragraph
    intro_para = None
    for i in range(appendix_start + 1, min(appendix_start + 5, len(paras))):
        text = get_text(paras[i])
        if len(text) > 20:
            intro_para = paras[i]
            break

    # Update introduction
    new_intro = (
        "以下代码为本文三个问题建模与求解的核心源程序，包括数据预处理、"
        "关键指标筛选、风险预警模型构建和干预方案优化四个模块。"
        "各模块代码文件的功能说明如下：\n"
        "附录A.1 数据加载与预处理模块——data_loader.py：负责原始数据加载、列名校正、"
        "缺失值检查和衍生特征构造。\n"
        "附录A.2 关键指标筛选与体质贡献度分析——q1_full.py：实现四种特征选择方法的"
        "交叉验证和Logistic回归OR值分析。\n"
        "附录A.3 多维度风险预警模型——q2_full.py：实现三级风险评分、六模型交叉验证对比、"
        "决策树规则提取和消融实验。\n"
        "附录A.4 6个月干预方案优化模型——q3_full.py：实现枚举法求解、Pareto前沿分析、"
        "多方案推荐和灵敏度分析。"
    )
    if intro_para:
        set_runs_text(intro_para, new_intro)
        print(f"  Updated introduction at P{appendix_start+1}")

    # Add description before each code section
    # Find all "附录A.X" headings and add descriptive text after them
    section_descs = {
        'A.1': ("本模块实现数据加载、列名校正、缺失值检查和衍生特征构造功能。"
                "原始数据包含37个字段，涵盖中医体质分型、活动能力评估、血常规体检指标和人口学信息。"),
        'A.2': ("本模块实现四种特征选择方法的交叉验证（LASSO回归、随机森林特征重要性、"
                "Spearman相关性分析和互信息法），以及九种体质对高血脂发病风险的Logistic回归OR值分析。"),
        'A.3': ("本模块构建融合中医体质、西医血脂指标和活动能力的三级风险预警模型，"
                "包括风险评分公式、六种分类模型交叉验证对比、决策树规则提取和消融实验。"),
        'A.4': ("本模块针对痰湿体质确诊患者构建6个月干预方案优化模型，"
                "通过枚举全部可行组合提取Pareto最优解，提供\"最省钱-性价比-效果优先\"三套推荐方案。"),
    }

    for i in range(appendix_start, min(appendix_start + 400, len(paras))):
        text = get_text(paras[i])
        for sec_id, desc in section_descs.items():
            if f'附录{sec_id}' in text and '(精简版)' not in text and '(完整版)' not in text:
                # Find the paragraph after this heading (skip the "(精简版)" line)
                if i + 1 < len(paras):
                    next_text = get_text(paras[i+1])
                    if '(精简版)' in next_text:
                        # The description should go between heading and code
                        # Replace the (精简版) line with the description
                        desc_para = paras[i+1]
                        set_runs_text(desc_para, desc)
                        print(f"  Added description for 附录{sec_id}")
                break

    print("  Appendix reformatted")
else:
    print("  WARNING: Could not find appendix start!")
    # Find where it might be
    for i in range(len(paras)):
        text = get_text(paras[i])
        if '附录' in text:
            print(f"  Found '附录' at P{i}: {text[:50]}")

# ============================================================
# 3. FONT CHECK
# ============================================================
print("\n[3/3] Font compliance check...")
issues = []
for i, p in enumerate(paras):
    text = get_text(p)
    if not text:
        continue

    runs = p.getElementsByTagName(C('r'))
    for r in runs:
        rPr = None
        for child in r.childNodes:
            if child.nodeType == child.ELEMENT_NODE and child.tagName.split('}')[-1] == 'rPr':
                rPr = child
                break
        if rPr is None:
            continue

        sz_elems = rPr.getElementsByTagName(C('sz'))
        if not sz_elems:
            continue
        sz_val = sz_elems[0].getAttribute('w:val')

        rf_elems = rPr.getElementsByTagName(C('rFonts'))
        if not rf_elems:
            continue
        font_ascii = rf_elems[0].getAttribute('w:ascii')
        font_ea = rf_elems[0].getAttribute('w:eastAsia')

        # Check body text (小四 = sz 24)
        if i > 30 and i < 450:  # Body text range
            if sz_val not in ['24', '28', '30', '32', '44']:
                issue = f"P{i}: non-standard sz={sz_val}, font={font_ea}, text=\"{text[:30]}\""
                if issue not in issues:
                    issues.append(issue)

for iss in issues[:5]:
    print(f"  {iss}")
print(f"  Total font issues found: {len(issues)} (showing first 5)")

# ============================================================
# SAVE
# ============================================================
print("\nSaving...")
doc.save(validate=False)
print("Done! Pack with pack.py")
