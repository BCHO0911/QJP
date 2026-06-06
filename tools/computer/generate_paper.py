from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from datetime import datetime

title = '经典定律的当代审视：摩尔定律的“终结”与计算机体系结构的新方向'
author = '学生：待填'
now = datetime.now()
date_str = f'{now.year}年{now.month}月{now.day}日'

content_sections = [
    ('引言',
     '摩尔定律自1965年提出以来，为半导体工业提供了性能增长与成本下降的路线图：每隔约两年集成电路上可容纳的晶体管数量翻倍，推动了计算能力的指数级提升。近年来，摩尔定律的推进速度明显放缓，传统的尺度缩减遭遇物理极限与能效瓶颈。本文回顾摩尔定律的历史贡献，分析导致其放缓的主要技术原因，并聚焦在“后摩尔时代”计算机体系结构上如何通过异构计算、存算一体与领域专用架构等路径继续实现性能与能效提升。'),

    ('摩尔定律的历史贡献与限制',
     '摩尔定律不仅是对集成度增长的观察，还是产业路线规划的重要指导。晶体管密度的持续提升使得更复杂的处理器、更多层次的缓存以及更高频率成为可能，从而带来单芯片性能提升与系统成本下降。与之相关的缩放规律（如Dennard缩放）在20世纪下半叶进一步保证了随尺寸减小而保持功耗密度不变，从而使频率提升成为可能。然而，两大约束逐步显现：其一，物理尺寸接近原子尺度，量子隧穿、短沟道效应等物理问题使得继续简单地缩小晶体管变得艰难；其二，Dennard缩放在微米级以下逐渐失效，器件尺寸减小不再自动带来功耗与电压成比例下降，导致功耗墙出现，芯片功耗与热管理成为限制频率与并行度的关键因素。'),

    ('导致放缓的技术原因',
     '物理极限：门长和栅氧化层的厚度接近极限，漏电流与制造变异增加，工艺复杂度和成本显著上升。\n功耗墙与能效瓶颈：由于能耗无法随缩放同步降低，运行更高频或更多核心的代价增大，出现“Dark Silicon”现象——在功耗预算下不能同时开启所有电路单元。\n制造与成本问题：极紫外光刻（EUV）等先进工艺投入巨大，边际收益递减，导致节点更迭速度放慢并提高系统总体成本。'),

    ('后摩尔时代的体系结构路径',
     '面对摩尔定律放缓，体系结构研究与工程实践呈现多条互补路线，以在能效受限的条件下继续提升算力密度。'),

    ('异构计算：CPU + GPU/TPU 等协同',
     '异构计算通过将通用性高但效率相对低的CPU与面向特定任务（向量、矩阵运算等）优化的加速器协同工作，显著提高了能效比。GPU在图形与深度学习推理/训练中的成功表明，通过数据并行与宽向量执行单元可以以更低能耗实现更高吞吐。Google的TPU等张量加速器证明了为特定领域定制指令集与硬件数据通路，可在数据中心级别带来量级性能/能效提升。异构体系依赖于合适的编程模型与系统软件支持，以在软硬件之间高效分配任务并减少数据移动开销。'),

    ('存算一体（PIM）',
     '数据移动在现代计算中成为极大的能耗与延迟来源，传统冯·诺依曼架构下处理器与内存之间的频繁传输已成为瓶颈。PIM通过在存储器内部或近邻集成计算单元，将部分计算下推至数据所在处，显著减少数据搬运成本，从而提升能效和带宽利用率。对于数据密集型任务（如数据库、图处理和机器学习推理），PIM提供了一条可行且有效的体系结构替代路径。'),

    ('领域专用架构（DSA）',
     '当通用处理器面临能效和性能瓶颈时，针对特定应用或算法设计的专用硬件能以更少的资源完成更多工作。DSA的核心在于牺牲通用性以换取针对性优化：定制的数据流、压缩与量化支持、硬件级并行模式等均能显著提升性能密度。近年来深度学习加速器、视频编解码器与加密加速器的广泛部署证明了DSA在商业与科研上的价值。'),

    ('三维集成与封装技术',
     '通过芯片级垂直堆叠或片上片组合，可以在物理布局上缩短不同功能单元之间的距离，提升带宽并降低能耗。这一方向不限于单一节点的晶体管缩放，而是通过系统级集成优化数据通路与热管理，从而实现更高的系统性能密度。'),

    ('结论与展望',
     '摩尔定律及其伴生的缩放规律曾是推动计算能力爆发式增长的主要动力，但随着物理极限、功耗墙与制造成本的显现，单靠尺度缩减已难以维持过去的增长节奏。在后摩尔时代，体系结构的创新——特别是异构计算、存算一体与领域专用架构——为继续提升性能与能效提供了切实可行的路径。未来的研究应聚焦于统一的异构编程与调度模型、可重构且易于编程的DSA开发链、以及在系统级进行跨层优化。通过软硬协同与跨学科创新，计算体系仍有望在新的范式下继续推进能力边界。'),
]

references = [
    'G. E. Moore, “Cramming more components onto integrated circuits,” Electronics, 1965.',
    'R. H. Dennard et al., “Design of ion-implanted MOSFETs with very small physical dimensions,” IEEE Journal of Solid-State Circuits, 1974.',
    'M. Horowitz, “Computing\'s energy problem (and what we can do about it),” ISSCC Digest, 2014.',
    'H. Esmaeilzadeh et al., “Dark silicon and the end of multicore scaling,” ISCA, 2011.',
    'S. Mittal, “A Survey of Architectural Techniques for Improving GPU Efficiency,” ACM Computing Surveys, 2016.',
    'N. P. Jouppi et al., “In-datacenter performance analysis of a tensor processing unit,” ISCA, 2017.',
    'V. Seshadri et al., “Ambit: In-memory computation of bitwise operations,” ISCA, 2017.',
    'D. Patterson et al., “A New Golden Age in Computer Architecture: Empowering the Machine-Learning Revolution,” Communications of the ACM, 2017.'
]

def set_paragraph_font(paragraph, size_pt=11, bold=False, italic=False):
    for run in paragraph.runs:
        run.font.size = Pt(size_pt)
        run.font.bold = bold
        run.font.italic = italic


def build_docx(path_out):
    doc = Document()

    # Title
    h = doc.add_heading(title, level=0)
    h.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    for run in h.runs:
        run.font.size = Pt(16)
        run.font.bold = True

    # Author and date
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    p_meta.add_run(author + '  |  ' + date_str).italic = True

    doc.add_paragraph()  # spacer

    # Sections
    for sec_title, sec_text in content_sections:
        s = doc.add_heading(sec_title, level=1)
        s.style = 'Heading 1'
        para = doc.add_paragraph(sec_text)
        para_format = para.paragraph_format
        para_format.space_after = Pt(6)
        set_paragraph_font(para, size_pt=11)

    # References
    doc.add_heading('参考文献', level=1)
    for i, ref in enumerate(references, 1):
        p = doc.add_paragraph(f'[{i}] {ref}')
        set_paragraph_font(p, size_pt=10)

    doc.save(path_out)


if __name__ == '__main__':
    out_path = r'd:\GIT\public\计组实验\摩尔定律的当代审视.docx'
    build_docx(out_path)
    print('Saved:', out_path)
