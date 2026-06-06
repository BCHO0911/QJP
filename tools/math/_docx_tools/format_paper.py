"""
数学建模国赛论文格式美化脚本 v4
"""
import sys, os, re, html

SKILL_ROOT = r"C:\Users\全佳鹏\.claude\skills\word-document-processor"
sys.path.insert(0, SKILL_ROOT)
from scripts.document import Document

UNPACKED = r"d:\GIT\public\数模\_unpacked_论文1.5"

doc = Document(UNPACKED)

def get_para_text(p):
    parts = []
    for t in p.getElementsByTagName("w:t"):
        for cn in t.childNodes:
            if cn.nodeValue:
                parts.append(cn.nodeValue)
    return ''.join(parts).strip()

def remove_child_tags(parent, local_name):
    to_kill = []
    for child in parent.childNodes:
        tag = child.nodeName.split('}')[-1]
        if tag == local_name or tag == f'w:{local_name}':
            to_kill.append(child)
    for c in to_kill:
        parent.removeChild(c)

def ensure_child(parent, local_name):
    for child in parent.childNodes:
        tag = child.nodeName.split('}')[-1]
        if tag == local_name or tag == f'w:{local_name}':
            return child
    new_elem = parent.ownerDocument.createElement(local_name)
    parent.appendChild(new_elem)
    return new_elem

def C(tag):
    return f'w:{tag}'

print("=" * 60)
print("数学建模国赛论文格式美化")
print("=" * 60)

# ============================================================
# 1. PAGE SETUP
# ============================================================
print("\n[1/5] 设置页边距 (国赛标准: 上2.54cm 下2.54cm 左3.17cm 右3.17cm)...")
editor = doc["word/document.xml"]
sectPr = editor.dom.getElementsByTagName("w:sectPr")[0]
pgMar = sectPr.getElementsByTagName("w:pgMar")[0]
pgMar.setAttribute("w:top", "1440")
pgMar.setAttribute("w:bottom", "1440")
pgMar.setAttribute("w:left", "1800")
pgMar.setAttribute("w:right", "1800")
pgMar.setAttribute("w:header", "851")
pgMar.setAttribute("w:footer", "992")

# ============================================================
# 2. NORMAL STYLE
# ============================================================
print("[2/5] 更新正文样式 (宋体 小四 1.5倍行距 首行缩进2字符)...")
for style in doc["word/styles.xml"].dom.getElementsByTagName("w:style"):
    if style.getAttribute("w:type") == "paragraph" and style.getAttribute("w:default") == "1":
        pPr = style.getElementsByTagName("w:pPr")[0]
        rPr = style.getElementsByTagName("w:rPr")[0]

        remove_child_tags(pPr, "spacing")
        remove_child_tags(pPr, "ind")
        remove_child_tags(pPr, "jc")

        sp = pPr.ownerDocument.createElement("w:spacing")
        sp.setAttribute("w:line", "360")
        sp.setAttribute("w:lineRule", "auto")
        sp.setAttribute("w:before", "0")
        sp.setAttribute("w:after", "0")
        pPr.appendChild(sp)

        ind = pPr.ownerDocument.createElement("w:ind")
        ind.setAttribute("w:firstLine", "480")
        ind.setAttribute("w:left", "0")
        ind.setAttribute("w:right", "0")
        pPr.appendChild(ind)

        jc = pPr.ownerDocument.createElement("w:jc")
        jc.setAttribute("w:val", "both")
        pPr.appendChild(jc)

        rFonts = rPr.getElementsByTagName("w:rFonts")[0]
        rFonts.setAttribute("w:ascii", "宋体")
        rFonts.setAttribute("w:hAnsi", "宋体")
        rFonts.setAttribute("w:eastAsia", "宋体")
        rFonts.setAttribute("w:cs", "宋体")

        remove_child_tags(rPr, "sz")
        remove_child_tags(rPr, "szCs")
        sz_e = rPr.ownerDocument.createElement("w:sz")
        sz_e.setAttribute("w:val", "24")
        rPr.appendChild(sz_e)
        szCs_e = rPr.ownerDocument.createElement("w:szCs")
        szCs_e.setAttribute("w:val", "24")
        rPr.appendChild(szCs_e)

        remove_child_tags(rPr, "lang")
        break

# ============================================================
# 3. HEADING FORMATTING
# ============================================================
def apply_heading(p, font, sz, bold=True, jc="left"):
    pPr = ensure_child(p, C("pPr"))
    remove_child_tags(pPr, "jc")
    jc_e = pPr.ownerDocument.createElement("w:jc")
    jc_e.setAttribute("w:val", jc)
    pPr.appendChild(jc_e)
    remove_child_tags(pPr, "spacing")
    sp_e = pPr.ownerDocument.createElement("w:spacing")
    sp_e.setAttribute("w:before", "120")
    sp_e.setAttribute("w:after", "60")
    sp_e.setAttribute("w:line", "360")
    sp_e.setAttribute("w:lineRule", "auto")
    pPr.appendChild(sp_e)
    remove_child_tags(pPr, "ind")

    for r in p.getElementsByTagName(C("r")):
        rPr = ensure_child(r, C("rPr"))
        remove_child_tags(rPr, "rFonts")
        rf = rPr.ownerDocument.createElement("w:rFonts")
        rf.setAttribute("w:ascii", font)
        rf.setAttribute("w:hAnsi", font)
        rf.setAttribute("w:eastAsia", font)
        rf.setAttribute("w:cs", font)
        rPr.appendChild(rf)
        remove_child_tags(rPr, "sz")
        sz_e = rPr.ownerDocument.createElement("w:sz")
        sz_e.setAttribute("w:val", str(sz))
        rPr.appendChild(sz_e)
        remove_child_tags(rPr, "szCs")
        szcs_e = rPr.ownerDocument.createElement("w:szCs")
        szcs_e.setAttribute("w:val", str(sz))
        rPr.appendChild(szcs_e)
        if bold:
            if not rPr.getElementsByTagName(C("b")):
                rPr.appendChild(rPr.ownerDocument.createElement("w:b"))
            if not rPr.getElementsByTagName(C("bCs")):
                rPr.appendChild(rPr.ownerDocument.createElement("w:bCs"))
        else:
            remove_child_tags(rPr, "b")
            remove_child_tags(rPr, "bCs")

def format_ref(p):
    pPr = ensure_child(p, C("pPr"))
    remove_child_tags(pPr, "ind")
    remove_child_tags(pPr, "spacing")
    sp = pPr.ownerDocument.createElement("w:spacing")
    sp.setAttribute("w:line", "240")
    sp.setAttribute("w:lineRule", "auto")
    sp.setAttribute("w:before", "0")
    sp.setAttribute("w:after", "0")
    pPr.appendChild(sp)
    for r in p.getElementsByTagName(C("r")):
        rPr = ensure_child(r, C("rPr"))
        remove_child_tags(rPr, "rFonts")
        rf = rPr.ownerDocument.createElement("w:rFonts")
        rf.setAttribute("w:ascii", "宋体")
        rf.setAttribute("w:hAnsi", "宋体")
        rf.setAttribute("w:eastAsia", "宋体")
        rf.setAttribute("w:cs", "宋体")
        rPr.appendChild(rf)
        remove_child_tags(rPr, "sz")
        sz_e = rPr.ownerDocument.createElement("w:sz")
        sz_e.setAttribute("w:val", "21")
        rPr.appendChild(sz_e)
        remove_child_tags(rPr, "szCs")
        szcs_e = rPr.ownerDocument.createElement("w:szCs")
        szcs_e.setAttribute("w:val", "21")
        rPr.appendChild(szcs_e)

# Heading definitions
L1 = ["问题重述", "问题分析", "模型假设", "符号说明", "数据处理",
      "模型建立", "结果分析", "灵敏度分析", "模型优化", "模型评价",
      "结论", "研究展望", "引用文献", "附录"]

L2 = ["研究背景", "问题描述",
      "问题1分析", "问题2分析", "问题3分析",
      "整体建模框架",
      "数据来源与初步观察", "列名标准化与缺失值检查", "衍生特征构造",
      "描述性统计分析", "数据分布与异常值检测",
      "问题1：关键指标筛选模型", "问题2：多维度风险预警模型",
      "问题3：6个月干预方案优化模型",
      "灰色GM(1,1)预测模型",
      "问题1结果", "问题2结果", "问题3结果",
      "灰色关联度分析", "主成分分析(PCA)", "AHP层次分析",
      "优化模型参数灵敏度", "分类模型特征灵敏度",
      "中介效应模型：揭示痰湿体质间接作用路径",
      "GradientBoosting早停法与正则化优化",
      "Sigmoid平台期下降率模型", "干预措施协同效应模型",
      "依从性Monte Carlo模拟",
      "模型优点", "模型不足与改进方向", "模型推广",
      "关键指标筛选与体质贡献度", "多维度风险预警模型",
      "6个月干预方案优化",
      "附录A：AI工具使用详情"]

L3 = ["特征选择方法", "体质贡献度分析模型",
      "风险评分模型", "分类模型", "模型评估指标",
      "可解释性分析", "消融实验",
      "决策变量", "约束条件", "痰湿积分下降模型",
      "多目标优化",
      "决策树规则提取", "三级风险阈值", "核心特征组合",
      "主要符号说明"]

body = editor.dom.getElementsByTagName("w:body")[0]
paras = body.getElementsByTagName("w:p")
print(f"[3/5] 格式化标题 (共 {len(paras)} 个段落)...")

counts = {"title": 0, "abstract": 0, "keywords": 0, "L1": 0, "L2": 0, "L3": 0}

for i, p in enumerate(paras):
    text = get_para_text(p)
    if not text:
        continue
    if i == 0:
        apply_heading(p, "黑体", 44, bold=True, jc="center")
        counts["title"] += 1
        continue
    if text == "摘要":
        apply_heading(p, "黑体", 32, bold=True, jc="center")
        counts["abstract"] += 1
        continue
    if text.startswith("关键词"):
        apply_heading(p, "黑体", 24, bold=True, jc="left")
        counts["keywords"] += 1
        continue
    matched = False
    for h in L1:
        if text == h:
            apply_heading(p, "黑体", 32, bold=True, jc="center")
            counts["L1"] += 1
            matched = True
            break
    if matched: continue
    for h in L2:
        if text == h:
            apply_heading(p, "黑体", 30, bold=True, jc="left")
            counts["L2"] += 1
            matched = True
            break
    if matched: continue
    for h in L3:
        if text == h:
            apply_heading(p, "黑体", 28, bold=True, jc="left")
            counts["L3"] += 1
            matched = True
            break
    if matched: continue

print(f"  标题格式化完成: {counts}")

# ============================================================
# 4. REFERENCES
# ============================================================
print("[4/5] 格式化参考文献 (宋体 五号)...")
in_refs = False
ref_count = 0
for i, p in enumerate(paras):
    text = get_para_text(p)
    if text == "引用文献":
        in_refs = True
        continue
    if in_refs and text:
        if text.startswith("附录"):
            in_refs = False
            continue
        format_ref(p)
        ref_count += 1
print(f"  {ref_count} 条参考文献已格式化")

# ============================================================
# 5. SAVE BACK TO UNPACKED
# ============================================================
print("[5/5] 保存格式化结果...")
doc.save(validate=False)  # Save back to original unpacked directory
print("  已保存到:", UNPACKED)
print("\n[完成] 格式美化完成, 正在打包生成docx...")
# Pack the document
import subprocess, glob, os
pack_script = os.path.join(SKILL_ROOT, "ooxml", "scripts", "pack.py")
output_docx = r"d:\GIT\public\数模\论文_国赛格式.docx"
result = subprocess.run(
    [sys.executable, pack_script, UNPACKED, output_docx],
    capture_output=True, text=True
)
if result.returncode == 0:
    print(f"  OK -> {output_docx}")
else:
    print(f"  WARNING: {result.stderr}")
