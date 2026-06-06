#!/usr/bin/env python3
import zipfile
import os
import shutil
import sys
from pathlib import Path

try:
    from docx import Document
except Exception:
    print('python-docx not installed. Please run: pip install python-docx')
    raise

def escape_latex(s):
    if s is None:
        return ''
    replace_map = {
        '\\': '\\textbackslash{}',
        '&': '\\&', '%': '\\%', '$': '\\$', '#': '\\#', '_': '\\_', '{': '\\{', '}' : '\\}', '~': '\\textasciitilde{}', '^': '\\textasciicircum{}'
    }
    out = s
    for k,v in replace_map.items():
        out = out.replace(k, v)
    # normalize whitespace
    out = ' '.join(out.split())
    return out


def extract_media_from_docx(docx_path, out_images_dir):
    out_images_dir = Path(out_images_dir)
    out_images_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx_path, 'r') as z:
        for f in z.namelist():
            if f.startswith('word/media/'):
                name = os.path.basename(f)
                z.extract(f, out_images_dir.parent)
                src = out_images_dir.parent / f
                dst = out_images_dir / name
                shutil.move(str(src), str(dst))
    return sorted([p.name for p in out_images_dir.iterdir() if p.is_file()])


def tables_to_latex(doc_path, out_tex_path):
    doc = Document(doc_path)
    lines = []
    lines.append('% Auto-generated tables from {}\n'.format(doc_path))
    lines.append('\\section*{符号说明 — 表格导出}\n')
    lines.append('\\begin{center}')
    for idx, table in enumerate(doc.tables, start=1):
        ncols = len(table.columns)
        col_format = 'l ' + ' '.join(['X'] * (ncols-1)) if ncols>=2 else 'X'
        lines.append('\\begin{tabularx}{\\textwidth}{@{}' + col_format + '@{}}')
        lines.append('\\toprule')
        for r_i, row in enumerate(table.rows):
            cells = [escape_latex(c.text) for c in row.cells]
            lines.append(' & '.join(cells) + ' \\')
            if r_i==0:
                lines.append('\\midrule')
        lines.append('\\bottomrule')
        lines.append('\\end{tabularx}\n')
    lines.append('\\end{center}')

    Path(out_tex_path).write_text('\n'.join(lines), encoding='utf-8')
    return out_tex_path


def figures_to_latex(images_dir, out_tex_path):
    images = sorted([p for p in Path(images_dir).iterdir() if p.is_file()])
    lines = []
    lines.append('% Auto-generated figures from docx media\n')
    lines.append('\\section*{插图}\n')
    for i,img in enumerate(images, start=1):
        caption = f'图{i} '  # placeholder, user can edit description
        lines.append('\\begin{figure}[htbp]')
        lines.append('  \\centering')
        lines.append(f'  \\includegraphics[width=0.8\\linewidth]{{images/{img.name}}}')
        lines.append(f'  \\caption{{{caption}}}')
        lines.append(f'  \\label{{fig:doc_img_{i}}}')
        lines.append('\\end{figure}\n')
    Path(out_tex_path).write_text('\n'.join(lines), encoding='utf-8')
    return out_tex_path


def main():
    if len(sys.argv) > 1:
        docx_path = sys.argv[1]
    else:
        docx_path = r'd:\GIT\public\paper_final.docx'
        # fallback to 数模 subfolder if exists
        alt = Path(r'd:\GIT\public\数模\paper_final.docx')
        if alt.exists():
            docx_path = str(alt)

    out_root = Path(r'd:\GIT\public\latex_output')
    out_root.mkdir(parents=True, exist_ok=True)
    images_dir = out_root / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)

    print('Extracting media...')
    imgs = extract_media_from_docx(docx_path, images_dir)
    print(f'Extracted images: {imgs}')

    print('Converting tables to LaTeX...')
    tables_tex = tables_to_latex(docx_path, out_root / 'tables.tex')
    print('Wrote', tables_tex)

    print('Generating figures LaTeX...')
    figures_tex = figures_to_latex(images_dir, out_root / 'figures.tex')
    print('Wrote', figures_tex)

    print('Done. Outputs in', out_root)

if __name__ == '__main__':
    main()
