import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docx import Document
from docx.shared import Inches
from tools.docx.docx_helpers import set_chinese_font


def make_docx(path):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # Title
    title = doc.add_heading('', level=0)
    run = title.add_run('经典定律的当代审视：摩尔定律的“终结”与计算机体系结构的新方向')
    set_chinese_font(run, name='宋体', size=16)
    run.bold = True
    doc.add_paragraph()

    # Author / info
    p_info = doc.add_paragraph()
    r = p_info.add_run('作者：自动生成  日期：2026-06-05')
    set_chinese_font(r, name='宋体', size=10)
    doc.add_paragraph()

    # Body paragraphs
    body = []
    body.append(('引言',
                 '摩尔定律自1965年提出以来，为半导体工业提供了性能增长与成本下降的路线图：每隔约两年集成电路上可容纳的晶体管数量翻倍，推动了计算能力的指数级提升[1]。这一趋势支撑了过去半个多世纪的信息技术繁荣，但近年来摩尔定律的推进速度明显放缓，传统的尺度缩减遭遇物理极限与能效瓶颈。本文回顾摩尔定律的历史贡献，分析导致其放缓的主要技术原因，并聚焦在“后摩尔时代”计算机体系结构上如何通过异构计算、存算一体与领域专用架构等路径继续实现性能与能效提升。'))

    body.append(('摩尔定律的历史贡献与限制',
                 '摩尔定律不仅是对集成度增长的经验观察，还是产业路线规划的重要指导。晶体管密度的持续提升使得更复杂的处理器、更深层次的缓存以及更高的频率成为可能，从而带来单芯片性能提升与系统成本下降[1]。与之相关的缩放规律（如Dennard缩放）在20世纪下半叶进一步保证了随尺寸减小而保持功耗密度不变，使得频率提升成为可行路径[2]。然而，随着特征尺寸接近原子尺度、量子效应与短沟道效应增多，简单的尺度缩减不再能以过去的速度带来收益；同时，功耗墙使得频率与并行度的扩张遇到实质性限制[2][3]。'))

    body.append(('导致放缓的技术原因',
                 '主要原因可归纳为三点：物理极限、功耗与能效瓶颈、以及制造与成本问题。物理极限体现在栅长、沟道控制与漏电流等器件物理问题上；功耗墙导致出现所谓的“Dark Silicon”现象，即在功耗预算内无法同时开启所有电路单元；制造成本方面，极紫外光刻等先进工艺带来极高资本支出，使得每一代工艺的边际收益递减[3][4]。这些因素促使产业与学术界寻求超越单纯缩放的替代路径。'))

    body.append(('后摩尔时代的体系结构路径',
                 '在摩尔定律放缓的背景下，体系结构上出现了多条互补的发展路径：异构计算、存算一体、领域专用架构（DSA）以及先进封装与三维集成。下面分别展开讨论。'))

    body.append(('异构计算：CPU + GPU/TPU',
                 '异构计算通过将通用处理器与专用加速器结合，按负载特点分配任务，从而提升整体能效与吞吐。GPU凭借其宽向量与高并行度在图形处理与深度学习推理/训练中表现出色；Google 的 TPU 等张量加速器则通过为张量运算定制数据路径、内存访问与指令支持，实现了在数据中心级别的性能与能效跃迁[5][6]。关键挑战包括编程模型的友好性、任务划分与数据移动开销的最小化。'))

    body.append(('存算一体（PIM）',
                 '数据移动在能耗中占据巨大比例，冯·诺依曼瓶颈因频繁的数据传输而更加突出。PIM 的思想是将部分计算能力放置在存储器内部或附近，减少数据搬运。对于位操作、近邻数据访问密集型的算法（如图处理、数据库以及部分机器学习任务），PIM 能显著降低能耗并提升带宽利用率。近年来包括在 DRAM 内部实现位操作与在内存侧集成可编程逻辑的研究，展示了 PIM 在特定场景下的潜在优势[7]。'))

    body.append(('领域专用架构（DSA）',
                 'DSA 通过为特定应用牺牲通用性以换取极致的能效与性能密度。深度学习推理/训练加速器、视频编解码器与压缩/加密加速器都是成功案例。DSA 的推广得益于高层编译器、中间表示（如 MLIR）与硬件生成工具链的发展，这些工具降低了从算法到硬件实现的门槛，促进了专用硬件在边缘与云端的落地[6][8]。'))

    body.append(('先进封装与三维集成',
                 '通过芯片級垂直堆叠、chiplet 设计与高速互连，可以在系统级别优化带宽、延迟与能效，从而在不依赖单一晶体管缩放的情况下提升整体性能密度。封装技术与热管理成为实现这些方案的工程关键。'))

    body.append(('设计取舍与联合优化',
                 '在实践中，工程师常将多种策略组合以达到目标：例如数据中心级 AI 系统可能同时采用 DSA（张量核）、异构平台（CPU+GPU/TPU）以及先进封装以优化带宽；边缘设备则可能更依赖低功耗 DSA 与 PIM。体系结构设计需在通用性、能效、开发成本与生态支持之间权衡，并通过软硬协同实现跨层优化。'))

    body.append(('结论与展望',
                 '摩尔定律不再是单一路径，但并不意味着计算能力的终结。通过异构计算、存算一体、领域专用架构以及先进封装的跨层创新，体系结构研究与工程仍有空间在后摩尔时代继续推升性能与能效。未来的重点包括统一的异构编程模型、可重构且易于编程的专用硬件工具链，以及系统级的热管理与带宽优化。软硬协同、算法与体系结构协作将是未来若干年的主旋律。'))

    for heading, para in body:
        h = doc.add_heading(heading, level=1)
        set_chinese_font(h.runs[0], name='宋体', size=12)
        p = doc.add_paragraph()
        r = p.add_run(para)
        set_chinese_font(r, name='宋体', size=11)

    # References
    doc.add_heading('参考文献', level=1)
    refs = [
        'G. E. Moore, "Cramming more components onto integrated circuits," Electronics, 1965.',
        'R. H. Dennard et al., "Design of ion-implanted MOSFETs with very small physical dimensions," IEEE J. Solid-State Circuits, 1974.',
        'M. Horowitz, "Computing\'s energy problem (and what we can do about it)," ISSCC Digest, 2014.',
        'H. Esmaeilzadeh et al., "Dark silicon and the end of multicore scaling," ISCA, 2011.',
        'S. Mittal, "A Survey of Architectural Techniques for Improving GPU Efficiency," ACM Computing Surveys, 2016.',
        'N. P. Jouppi et al., "In-datacenter performance analysis of a tensor processing unit," ISCA, 2017.',
        'V. Seshadri et al., "Ambit: In-memory computation of bitwise operations," ISCA, 2017.',
        'D. Patterson et al., "A New Golden Age in Computer Architecture: Empowering the Machine-Learning Revolution," Communications of the ACM, 2017.'
    ]
    for i, rtext in enumerate(refs, 1):
        p = doc.add_paragraph(f'[{i}] {rtext}')
        set_chinese_font(p.runs[0], name='宋体', size=10)

    out_dir = ROOT / 'output'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / '摩尔定律_终结与体系结构.docx')
    doc.save(out_path)
    return out_path


if __name__ == '__main__':
    print('正在生成 docx...')
    path = make_docx(os.getcwd())
    print('已生成：', path)
