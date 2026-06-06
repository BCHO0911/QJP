# Tools Registry

This folder is the single home for reusable scripts and utilities.

## Docx Tools

- `tools/docx/apply_manuscript.py` - build a manuscript DOCX from JSON content.
- `tools/docx/convert_doc_to_docx.py` - convert legacy `.doc` files to `.docx`.
- `tools/docx/format_and_convert.py` - format generated DOCX files and optionally export PDF.
- `tools/docx/generate_docx.py` - generate the sample course-paper DOCX.
- `tools/docx/read_template.py` - inspect text in the course template DOCX.
- `tools/docx/extract_docx.py` - extract tables, figures, and structure from a DOCX.
- `tools/docx/docx_helpers.py` - shared docx font helpers.

## Math Modeling Tools

- `tools/math/gen_moore_paper_docx.py` - generate the computer-architecture essay DOCX.
- `tools/math/model_optimization.py` - run the numerical experiments and plotting for the modeling work.
- `tools/math/build_paper.js` - build the modeling paper pipeline.
- `tools/math/src/` - reusable modeling code.
- `tools/math/_docx_tools/` - DOCX post-processing helpers for the modeling paper.
- `tools/math/附录_代码_精简版/` - appendix code bundle used by the paper pipeline.

## Computer Organization Tool

- `tools/computer/generate_paper.py` - generate the computer-organization course paper.
