from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


TITLE = "经典定律的当代审视：摩尔定律的“终结”与计算机体系结构的新方向"
OUTPUT = "摩尔定律的当代审视.docx"


def set_document_defaults(document: Document) -> None:
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(3.0)

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "宋体"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(12)

    for name, size in [("Title", 18), ("Heading 1", 14), ("Heading 2", 13)]:
        style = styles[name]
        style.font.name = "黑体"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        style.font.size = Pt(size)
        style.font.bold = True


def set_paragraph_format(paragraph, *, first_line_cm=0.74, line_spacing=1.5, space_before=0, space_after=0):
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(first_line_cm)
    fmt.line_spacing = line_spacing
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)


def add_title(document: Document) -> None:
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(TITLE)
    run.font.name = "黑体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    run.font.size = Pt(20)
    run.bold = True
    p.paragraph_format.space_after = Pt(12)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("计算机组成原理结课论文")
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(12)
    p.paragraph_format.space_after = Pt(18)


def add_heading(document: Document, text: str, level: int = 1) -> None:
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.font.name = "黑体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    run.bold = True
    run.font.size = Pt(14 if level == 1 else 13)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.first_line_indent = Cm(0)


def add_body_paragraph(document: Document, text: str, first_line_cm: float = 0.74) -> None:
    p = document.add_paragraph()
    run = p.add_run(text)
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(12)
    set_paragraph_format(p, first_line_cm=first_line_cm, line_spacing=1.5)


def add_abstract(document: Document) -> None:
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("摘 要")
    run.font.name = "黑体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    run.bold = True
    run.font.size = Pt(14)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)

    abstract = (
        "摩尔定律曾长期扮演计算机性能增长的核心引擎，但随着器件尺寸逼近物理极限、功耗墙和数据移动成本快速上升，单纯依赖制程微缩的路径已难以维持以往的加速节奏。"
        "本文回顾摩尔定律对计算产业的历史作用，分析其放缓背后的技术原因，并重点讨论后摩尔时代计算机体系结构的三类新方向：异构计算通过CPU与GPU/TPU协同提升吞吐和能效；存算一体通过减少数据搬运缓解冯·诺依曼瓶颈；领域专用架构则以面向任务的硬件定制实现更高性能密度。"
        "这些路径表明，未来性能增长将更多来自架构创新、软硬件协同与系统级优化，而非单一制程缩放。"
    )
    add_body_paragraph(document, abstract, first_line_cm=0)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("关键词：")
    run.bold = True
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(12)
    run2 = p.add_run("摩尔定律；后摩尔时代；异构计算；存算一体；领域专用架构")
    run2.font.name = "宋体"
    run2._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run2.font.size = Pt(12)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(8)


def add_reference(document: Document, text: str) -> None:
    p = document.add_paragraph(style="Normal")
    p.paragraph_format.left_indent = Cm(0.74)
    p.paragraph_format.first_line_indent = Cm(-0.74)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(10.5)


def main() -> None:
    document = Document()
    set_document_defaults(document)

    add_title(document)
    add_abstract(document)

    add_heading(document, "一、摩尔定律的历史贡献与边界")
    add_body_paragraph(
        document,
        "摩尔定律的价值不仅在于对晶体管数量增长的经验描述，更在于它为整个半导体产业提供了长期、稳定且可预期的技术路线图。"
        "在这一预期下，工艺演进、EDA工具、芯片设计和系统部署能够围绕“持续缩放”组织起来，推动个人计算机、移动终端和云计算基础设施的快速普及。"
        "与之配套的Dennard缩放一度使晶体管缩小能够伴随电压和功耗同步下降，从而让频率提升成为可能。"
        "正因如此，过去几十年中的算力增长很大程度上来自制程微缩带来的密度提升。"
    )
    add_body_paragraph(
        document,
        "但这种增长并非无限。随着特征尺寸逼近纳米级，量子隧穿、短沟道效应和制造波动使器件难以继续稳定工作；"
        "与此同时，Dennard缩放失效后，电压难以下降，功耗和散热成为制约CPU/GPU进一步提频的核心障碍。"
        "结果是，性能提升越来越依赖架构层面的并行化与专用化，而不是单纯依赖更先进的制程节点。"
    )

    add_heading(document, "二、摩尔定律放缓的技术原因")
    add_body_paragraph(
        document,
        "摩尔定律放缓首先是物理极限问题。晶体管缩小时，栅极对沟道的控制能力减弱，漏电流增大，器件变异带来的良率压力也随之上升。"
        "先进工艺还面临互连延迟和寄生电容占比上升的问题，使得“更小”不再自动等于“更快”。"
        "其次是功耗墙问题。现代芯片即使晶体管继续增加，也无法把所有单元同时点亮，所谓“暗硅”现象意味着算力预算必须在性能、功耗和温度之间重新分配。"
        "再次，先进光刻和制造设备投入巨大，制程升级带来的边际收益下降，产业端也不再能仅靠缩放获得足够的经济回报。"
    )
    add_body_paragraph(
        document,
        "因此，后摩尔时代的核心任务不再是把同一种处理器做得更小，而是把有限的硅资源用在更值得的地方：减少数据搬运、提高并行效率、缩短关键路径，并让硬件更贴近应用工作负载。"
    )

    add_heading(document, "三、后摩尔时代的体系结构新方向")
    add_heading(document, "3.1 异构计算", level=2)
    add_body_paragraph(
        document,
        "异构计算的思路是让CPU承担控制流复杂、分支多、通用性强的任务，让GPU、TPU等加速器处理规则性高、数据并行明显的计算。"
        "在深度学习训练和推理、图像处理、科学计算等场景中，这种协作模式能显著提升吞吐量和能效。"
        "TPU等张量加速器进一步证明，针对矩阵乘加、激活函数和张量流的专门数据通路，比通用CPU更适合新一代AI工作负载。"
    )
    add_body_paragraph(
        document,
        "从体系结构角度看，异构并不只是“多放几个加速器”，而是要求编程模型、调度机制和内存层次结构同时协同设计。"
        "如果数据在CPU和加速器之间频繁搬移，收益会被互连开销抵消，因此高效的异构系统往往依赖共享内存、统一地址空间或更智能的编译器自动划分。"
    )

    add_heading(document, "3.2 存算一体", level=2)
    add_body_paragraph(
        document,
        "存算一体的目标是缓解冯·诺依曼瓶颈。传统体系结构中，处理器和存储器之间的数据搬运既耗时又耗能，而许多现代应用恰恰被数据移动而非计算本身所限制。"
        "如果把部分计算能力嵌入内存阵列或靠近存储器的位置，就可以让数据“就地计算”，减少带宽压力并提升能效。"
        "对于数据库检索、图处理、位运算和部分神经网络推理等任务，这种思路尤其有效。"
    )
    add_body_paragraph(
        document,
        "存算一体并不意味着完全取代CPU，而是把最适合在内存侧完成的操作卸载出去。"
        "它的研究价值在于重新定义“计算”的边界：当数据密集型任务成为主流后，架构创新的重点已从单核速度转向数据路径优化。"
    )

    add_heading(document, "3.3 领域专用架构", level=2)
    add_body_paragraph(
        document,
        "领域专用架构（DSA）强调为特定应用类别量身定制硬件，例如AI加速器、视频编解码器、密码学模块和网络处理器。"
        "DSA的优势在于能够将通用处理器上不必要的控制和冗余剔除，把晶体管预算集中到目标工作负载真正需要的功能上。"
        "这使得它在性能、功耗和面积三方面都能取得更优解。"
    )
    add_body_paragraph(
        document,
        "DSA并不等于牺牲软件生态。相反，编译器中间表示、自动调优和硬件生成技术的进步，使得专用硬件可以在保持较高开发效率的同时进入实际产品。"
        "未来体系结构竞争的关键，可能是“谁能把领域知识更高效地映射到硬件”而不是“谁的通用核心更快一点”。"
    )

    add_heading(document, "四、结语")
    add_body_paragraph(
        document,
        "摩尔定律并未真正“失效”，但它作为唯一增长范式的时代已经结束。新的性能提升逻辑正在从制程驱动转向架构驱动，从单芯片通用计算转向异构协同、存算协同与领域专用协同。"
        "这意味着未来的计算系统将更像一个分工明确的“硬件生态”，而非单一处理器不断提频的延续。"
        "对于计算机组成原理课程而言，这一变化也提示我们：理解现代计算机，不能只看晶体管数，更要看数据如何流动、任务如何划分、能量如何消耗。"
    )

    add_heading(document, "参考文献")
    refs = [
        "[1] Moore G E. Cramming more components onto integrated circuits[J]. Electronics, 1965.",
        "[2] Dennard R H, Gaensslen F H, Yu H N, et al. Design of ion-implanted MOSFETs with very small physical dimensions[J]. IEEE Journal of Solid-State Circuits, 1974, 9(5): 256-268.",
        "[3] Horowitz M. Computing's energy problem (and what we can do about it)[C]//2014 IEEE International Solid-State Circuits Conference Digest of Technical Papers. IEEE, 2014: 10-14.",
        "[4] Esmaeilzadeh H, Blem E, St Amant R, et al. Dark silicon and the end of multicore scaling[C]//Proceedings of the 38th Annual International Symposium on Computer Architecture. ACM, 2011: 365-376.",
        "[5] Mittal S. A Survey of Techniques for Architecting and Improving GPU Efficiency[J]. ACM Computing Surveys, 2016, 48(4): 1-46.",
        "[6] Jouppi N P, Young C, Patil N, et al. In-datacenter performance analysis of a tensor processing unit[C]//Proceedings of the 44th Annual International Symposium on Computer Architecture. ACM, 2017: 1-12.",
        "[7] Seshadri V, Gokhale V, Boroumand A, et al. Ambit: In-memory bitwise operations using commodity DRAM[C]//Proceedings of the 50th Annual IEEE/ACM International Symposium on Microarchitecture. ACM, 2017: 1-14.",
        "[8] Patterson D, Hennessy J. A new golden age for computer architecture[J]. Communications of the ACM, 2017, 60(2): 34-44.",
    ]
    for ref in refs:
        add_reference(document, ref)

    document.save(OUTPUT)


if __name__ == "__main__":
    main()