from docx.oxml.ns import qn
from docx.shared import Pt


def set_chinese_font(run, name='宋体', size=12, bold=False):
    try:
        run.font.name = name
        run.font.size = Pt(size)
        run.font.bold = bold
        r = run._r
        if getattr(r, 'rPr', None) is not None:
            try:
                r.rPr.rFonts.set(qn('w:eastAsia'), name)
            except Exception:
                pass
    except Exception:
        pass
