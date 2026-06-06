import os
import sys
from pathlib import Path

def convert(doc_path, out_path):
    try:
        import win32com.client as win32
    except Exception as e:
        print('需要 pywin32 支持：', e)
        return 2

    word = win32.Dispatch('Word.Application')
    word.Visible = False
    try:
        doc = word.Documents.Open(doc_path)
        doc.SaveAs(out_path, FileFormat=16)  # wdFormatDocumentDefault = 16 for docx
        doc.Close()
        print('已转换为 docx:', out_path)
        return 0
    except Exception as e:
        print('转换失败：', e)
        return 1
    finally:
        word.Quit()


if __name__ == '__main__':
    src = r'D:\cxdownload\课程论文格式.doc'
    dst_dir = Path(r'D:\GIT\public\templates')
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / '课程论文格式.docx'
    rc = convert(src, str(dst))
    sys.exit(rc)
