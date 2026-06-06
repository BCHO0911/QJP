from docx import Document
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    docx_path = ROOT / 'templates' / '课程论文格式.docx'
    if not docx_path.exists():
        print('模板文件不存在：', docx_path)
        raise SystemExit(1)

    doc = Document(docx_path)
    texts = []
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt:
            texts.append(txt)

    print('\n'.join(texts))


if __name__ == '__main__':
    main()
